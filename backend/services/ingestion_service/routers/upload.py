"""POST /upload — receive file, validate, save, enqueue extraction."""

from __future__ import annotations

import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.ingestion_service.config import get_settings
from backend.services.ingestion_service.dependencies import CurrentUser, get_current_user, get_db
from backend.services.ingestion_service.models.audit import AuditAction, AuditEntry
from backend.services.ingestion_service.models.import_record import ImportRecord
from backend.shared.auth.rbac import Permission
from backend.shared.exceptions import FileTooLarge, UnsupportedFormat

router = APIRouter()

_ALLOWED_MIME_PREFIXES = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml",  # xlsx
    "application/vnd.ms-excel",                                      # xls
    "application/vnd.oasis.opendocument.spreadsheet",               # ods
    "text/csv",
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/webp",
)

_MAGIC_BYTES: dict[bytes, str] = {
    b"PK\x03\x04": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    b"%PDF": "application/pdf",
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
    b"II*\x00": "image/tiff",
    b"MM\x00*": "image/tiff",
    b"RIFF": "image/webp",
}


def _detect_mime(header_bytes: bytes) -> str | None:
    for magic, mime in _MAGIC_BYTES.items():
        if header_bytes.startswith(magic):
            return mime
    # CSV: no magic bytes — allow based on content sniffing later
    return None


@router.post("/upload", status_code=202)
async def upload_file(
    file: UploadFile = File(...),
    domain: str = Form(...),
    period: str = Form(...),
    institution_id: str = Form(...),
    is_historical: bool = Form(False),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()

    # ── Auth check ──────────────────────────────────────────────────────────
    from backend.shared.auth.rbac import require
    require(current_user.role, Permission.UPLOAD_DOCUMENTS)

    if is_historical:
        require(current_user.role, Permission.IMPORT_HISTORICAL)

    inst_id = uuid.UUID(institution_id)
    from backend.services.ingestion_service.dependencies import require_own_institution
    require_own_institution(inst_id, current_user)

    # ── File size check (before reading the whole file) ──────────────────────
    # Read first chunk to detect type; then stream the rest
    first_chunk = await file.read(8)
    detected_mime = _detect_mime(first_chunk) or "text/csv"

    # Check size via Content-Length header (early rejection)
    if file.size and file.size > settings.max_file_size_bytes:
        raise FileTooLarge()

    # Validate MIME
    if not any(detected_mime.startswith(prefix) for prefix in _ALLOWED_MIME_PREFIXES):
        raise UnsupportedFormat(detail=f"Detected type: {detected_mime}")

    # ── Save to disk ─────────────────────────────────────────────────────────
    import_id = uuid.uuid4()
    upload_dir = Path(settings.upload_dir) / str(import_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = Path(file.filename or "upload").name
    storage_path = upload_dir / safe_filename

    bytes_written = len(first_chunk)
    async with aiofiles.open(storage_path, "wb") as out:
        await out.write(first_chunk)
        while chunk := await file.read(1024 * 1024):  # 1 MB chunks
            if bytes_written + len(chunk) > settings.max_file_size_bytes:
                storage_path.unlink(missing_ok=True)
                raise FileTooLarge()
            await out.write(chunk)
            bytes_written += len(chunk)

    # ── Create import record ─────────────────────────────────────────────────
    record = ImportRecord(
        id=import_id,
        institution_id=inst_id,
        uploaded_by=current_user.user_id,
        original_filename=file.filename or safe_filename,
        storage_path=str(storage_path),
        file_size_bytes=bytes_written,
        detected_mime_type=detected_mime,
        domain=domain,
        period=period,
        is_historical=is_historical,
        status="pending",
    )
    db.add(record)

    audit = AuditEntry(
        import_id=import_id,
        institution_id=inst_id,
        user_id=current_user.user_id,
        action=AuditAction.FILE_UPLOADED,
        description_fr=f"Fichier « {safe_filename} » reçu ({bytes_written} octets). Extraction en attente.",
    )
    db.add(audit)
    await db.commit()

    # ── Enqueue extraction ────────────────────────────────────────────────────
    from backend.services.ingestion_service.tasks import run_extraction

    task = run_extraction.apply_async(args=[str(import_id)], queue="extraction")
    record.extraction_task_id = task.id
    await db.commit()

    return {
        "import_id": str(import_id),
        "status": "pending",
        "message": "Fichier reçu. L'extraction est en cours.",
    }
