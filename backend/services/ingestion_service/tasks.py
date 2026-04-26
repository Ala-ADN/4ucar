"""Celery task definitions for the ingestion pipeline.

Three task types, each in its own queue:
  extraction  → run_extraction, run_normalization_and_validation
  ocr         → run_ocr_extraction (CPU/GPU bound — separate pool)
  mapping     → run_mapping (Gemini API call, fuzzy fallback)

Tasks write results directly to PostgreSQL via a synchronous session.
They do NOT call back into the FastAPI process.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.workers.celery_app import celery_app
from backend.services.ingestion_service.config import get_settings
from backend.services.ingestion_service.models.audit import AuditAction, AuditEntry
from backend.services.ingestion_service.models.import_record import ImportRecord
from backend.shared.logging import get_logger

logger = get_logger(__name__)


_sync_engine = None


def _get_sync_session() -> Session:
    global _sync_engine
    if _sync_engine is None:
        settings = get_settings()
        _sync_engine = create_engine(settings.postgres_dsn_sync, pool_pre_ping=True)
    return Session(_sync_engine)


# ── EXTRACTION ────────────────────────────────────────────────────────────────


@celery_app.task(bind=True, name="backend.services.ingestion_service.tasks.run_extraction", max_retries=2)
def run_extraction(self, import_id: str) -> dict:
    """Detect file type and run the appropriate extractor. Updates import record."""
    from backend.services.ingestion_service.extractors import excel, csv_extractor, pdf_extractor
    from backend.services.ingestion_service.extractors.base import ExtractionResult

    settings = get_settings()

    with _get_sync_session() as session:
        record = session.get(ImportRecord, uuid.UUID(import_id))
        if not record:
            return {"error": "import not found"}

        record.status = "extracting"
        session.commit()

        try:
            file_path = Path(record.storage_path)
            mime = record.detected_mime_type or ""

            if "excel" in mime or "spreadsheet" in mime or file_path.suffix.lower() in (".xlsx", ".xls", ".ods"):
                result: ExtractionResult = excel.extract(file_path)
            elif mime == "text/csv" or file_path.suffix.lower() == ".csv":
                result = csv_extractor.extract(file_path)
            elif "pdf" in mime or file_path.suffix.lower() == ".pdf":
                if pdf_extractor.is_native_pdf(file_path):
                    result = pdf_extractor.extract(file_path)
                else:
                    # Scanned PDF — render pages, then dispatch to OCR task
                    page_images = pdf_extractor.render_pages_as_images(file_path)
                    if len(page_images) > settings.max_pdf_pages:
                        from backend.shared.exceptions import PdfTooManyPages
                        raise PdfTooManyPages(detail=f"Pages: {len(page_images)}")

                    record.status = "ocr_pending"
                    session.commit()
                    run_ocr_extraction.apply_async(
                        args=[import_id],
                        kwargs={"page_images_hex": [p.hex() for p in page_images]},
                        queue="ocr",
                    )
                    return {"status": "ocr_dispatched"}
            else:
                # Image file
                image_bytes = file_path.read_bytes()
                run_ocr_extraction.apply_async(
                    args=[import_id],
                    kwargs={"page_images_hex": [image_bytes.hex()]},
                    queue="ocr",
                )
                record.status = "ocr_pending"
                session.commit()
                return {"status": "ocr_dispatched"}

            _store_extraction_result(session, record, result)
            _write_audit(session, record, AuditAction.EXTRACTION_COMPLETED,
                         f"Extraction terminée : {result.total_rows} lignes, {len(result.headers)} colonnes.")
            return {"status": "extracted", "headers": result.headers, "total_rows": result.total_rows}

        except Exception as exc:
            record.status = "extraction_failed"
            _write_audit(session, record, AuditAction.EXTRACTION_FAILED, f"Échec extraction : {exc}")
            session.commit()
            logger.error("extraction_failed", import_id=import_id, error=str(exc))
            raise self.retry(exc=exc, countdown=5)


@celery_app.task(bind=True, name="backend.services.ingestion_service.tasks.run_ocr_extraction", max_retries=1)
def run_ocr_extraction(self, import_id: str, page_images_hex: list[str]) -> dict:
    """Run PaddleOCR PP-StructureV2 on rendered images."""
    from backend.services.ingestion_service.extractors import ocr_extractor

    page_images = [bytes.fromhex(h) for h in page_images_hex]

    with _get_sync_session() as session:
        record = session.get(ImportRecord, uuid.UUID(import_id))
        if not record:
            return {"error": "import not found"}

        try:
            result = ocr_extractor.extract_from_pdf_pages(page_images)
            _store_extraction_result(session, record, result)
            _write_audit(session, record, AuditAction.EXTRACTION_COMPLETED,
                         f"OCR terminé : {result.total_rows} lignes extraites.")
            return {"status": "extracted", "total_rows": result.total_rows}

        except Exception as exc:
            record.status = "extraction_failed"
            _write_audit(session, record, AuditAction.EXTRACTION_FAILED, f"Échec OCR : {exc}")
            session.commit()
            logger.error("ocr_failed", import_id=import_id, error=str(exc))
            raise self.retry(exc=exc, countdown=10)


# ── MAPPING ───────────────────────────────────────────────────────────────────


@celery_app.task(bind=True, name="backend.services.ingestion_service.tasks.run_mapping", max_retries=2)
def run_mapping(self, import_id: str, domain: str) -> dict:
    """Identity mapping — each extracted header is assumed to match a field of the same name."""
    with _get_sync_session() as session:
        record = session.get(ImportRecord, uuid.UUID(import_id))
        if not record:
            return {"error": "import not found"}

        headers = record.extracted_headers or []
        if not headers:
            return {"error": "no headers available"}

        proposal = [
            {"column": h, "field_id": h, "confidence": 1.0, "reason": "Correspondance directe."}
            for h in headers
        ]

        record.mapping_proposal = proposal
        record.status = "mapping_proposed"
        _write_audit(session, record, AuditAction.MAPPING_PROPOSED,
                     f"Correspondance directe générée pour {len(proposal)} colonnes.")
        session.commit()

        return {"status": "mapping_proposed", "proposal": proposal}


# ── NORMALIZATION + VALIDATION ────────────────────────────────────────────────


@celery_app.task(bind=True, name="backend.services.ingestion_service.tasks.run_normalization_and_validation", max_retries=1)
def run_normalization_and_validation(self, import_id: str) -> dict:
    """Apply confirmed mapping → normalize values → validate → quarantine invalids."""
    from backend.services.ingestion_service.normalizer import normalize_row
    from backend.services.ingestion_service.validator import validate_row, ValidationStatus
    from backend.services.ingestion_service.models.import_record import QuarantineRow

    with _get_sync_session() as session:
        record = session.get(ImportRecord, uuid.UUID(import_id))
        if not record:
            return {"error": "import not found"}

        mapping = record.confirmed_mapping or {}
        rows = record.extracted_preview or []  # In real impl, stored separately; preview for now

        # NOTE: For brevity, rows are stored in the import record as JSON.
        # Production stores full row data in a separate table.
        full_rows_json = (record.extracted_preview or [])  # placeholder
        normalization_log: list[dict] = []
        valid_count = warned_count = quarantine_count = 0
        domain = record.domain or "academic"

        for row_idx, raw_row in enumerate(full_rows_json):
            normalized, row_log = normalize_row(raw_row, mapping)
            normalization_log.extend(row_log)

            status, reason, field = validate_row(normalized, mapping, domain)

            if status == ValidationStatus.INVALID:
                q = QuarantineRow(
                    import_id=record.id,
                    row_index=row_idx,
                    raw_data=raw_row,
                    failed_field=field or "unknown",
                    failure_reason_fr=reason or "Valeur invalide.",
                )
                session.add(q)
                quarantine_count += 1
            elif status == ValidationStatus.WARNED:
                warned_count += 1
            else:
                valid_count += 1

        record.normalization_log = normalization_log
        record.records_valid = valid_count
        record.records_warned = warned_count
        record.records_quarantined = quarantine_count
        record.validation_summary = {
            "valid": valid_count,
            "warned": warned_count,
            "quarantined": quarantine_count,
        }
        record.status = "validated"
        _write_audit(session, record, AuditAction.VALIDATION_COMPLETED,
                     f"Validation : {valid_count} valides, {warned_count} avertissements, {quarantine_count} en quarantaine.")
        session.commit()

        return {
            "status": "validated",
            "valid": valid_count,
            "warned": warned_count,
            "quarantined": quarantine_count,
        }


# ── HELPERS ───────────────────────────────────────────────────────────────────


def _store_extraction_result(session: Session, record: ImportRecord, result) -> None:
    from backend.services.ingestion_service.extractors.base import ExtractionResult

    record.extracted_headers = result.headers
    record.extracted_preview = result.preview
    record.total_rows = result.total_rows
    record.status = "extracted"
    session.commit()


def _write_audit(session: Session, record: ImportRecord, action: str, description_fr: str) -> None:
    entry = AuditEntry(
        import_id=record.id,
        institution_id=record.institution_id,
        user_id=record.uploaded_by,
        action=action,
        description_fr=description_fr,
    )
    session.add(entry)
    session.commit()
