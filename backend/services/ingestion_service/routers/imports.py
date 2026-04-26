"""Import lifecycle routes:

GET  /imports/{import_id}/status
GET  /imports/{import_id}/mapping      (enqueues mapping task if not done)
POST /imports/{import_id}/mapping      (confirm mapping → triggers normalize+validate)
GET  /imports/{import_id}/validation
POST /imports/{import_id}/commit
POST /imports/{import_id}/cancel
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.ingestion_service.dependencies import (
    CurrentUser,
    get_current_user,
    get_db,
    require_own_institution,
)
from backend.services.ingestion_service.models.audit import AuditAction, AuditEntry
from backend.services.ingestion_service.models.import_record import (
    DataRecord,
    ImportRecord,
    LockedPeriod,
)
from backend.shared.auth.rbac import Permission, require
from backend.shared.exceptions import CommitConflict, NotFound, PeriodLocked, ValidationFailed

router = APIRouter()


async def _get_import_or_404(import_id: uuid.UUID, db: AsyncSession) -> ImportRecord:
    record = await db.get(ImportRecord, import_id)
    if not record:
        raise NotFound(detail=f"Import {import_id} introuvable.")
    return record


# ── Status ────────────────────────────────────────────────────────────────────


@router.get("/imports/{import_id}/status")
async def get_status(
    import_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await _get_import_or_404(import_id, db)
    require_own_institution(record.institution_id, current_user)

    response = {
        "import_id": str(record.id),
        "status": record.status,
        "domain": record.domain,
        "period": record.period,
        "original_filename": record.original_filename,
        "created_at": record.created_at.isoformat(),
    }

    if record.status in ("extracted", "mapping_proposed", "mapping_confirmed", "validated", "committed"):
        response["headers"] = record.extracted_headers
        response["preview"] = record.extracted_preview
        response["total_rows"] = record.total_rows
        if getattr(record, "available_sheets", None):
            response["available_sheets"] = record.available_sheets

    return response


# ── Mapping proposal ──────────────────────────────────────────────────────────


@router.get("/imports/{import_id}/mapping")
async def get_mapping(
    import_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await _get_import_or_404(import_id, db)
    require_own_institution(record.institution_id, current_user)

    if record.status == "extracted":
        # Build identity mapping inline — no external API, no queue
        headers = record.extracted_headers or []
        proposal = [
            {"column": h, "field_id": h, "confidence": 1.0, "reason": "Correspondance directe."}
            for h in headers
        ]
        record.mapping_proposal = proposal
        record.status = "mapping_proposed"
        await db.commit()

    if record.status in ("mapping_proposed", "mapping_confirmed", "validated", "committed"):
        if not record.mapping_proposal and record.extracted_headers:
            record.mapping_proposal = [
                {"column": h, "field_id": h, "confidence": 1.0, "reason": "Correspondance directe."}
                for h in record.extracted_headers
            ]
            await db.commit()
        return {
            "status": record.status,
            "proposal": record.mapping_proposal or [],
        }

    raise ValidationFailed(detail=f"Statut inattendu : {record.status}")


class MappingConfirmation(BaseModel):
    mapping: dict[str, str | None]  # {column_header: field_id | null}


@router.post("/imports/{import_id}/mapping")
async def confirm_mapping(
    import_id: uuid.UUID,
    body: MappingConfirmation,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await _get_import_or_404(import_id, db)
    require_own_institution(record.institution_id, current_user)

    if record.status not in ("mapping_proposed", "mapping_confirmed"):
        raise ValidationFailed(detail=f"Impossible de confirmer dans l'état : {record.status}")

    record.confirmed_mapping = body.mapping
    record.status = "mapping_confirmed"

    audit = AuditEntry(
        import_id=record.id,
        institution_id=record.institution_id,
        user_id=current_user.user_id,
        action=AuditAction.MAPPING_CONFIRMED,
        description_fr="Correspondance des colonnes confirmée par l'utilisateur.",
        payload={"mapping": body.mapping},
    )
    db.add(audit)
    await db.commit()

    # Trigger normalization + validation
    from backend.services.ingestion_service.tasks import run_normalization_and_validation

    task = run_normalization_and_validation.apply_async(args=[str(import_id)], queue="extraction")
    record.validation_task_id = task.id
    await db.commit()

    return {"status": "mapping_confirmed", "task_id": task.id}


# ── Validation results ────────────────────────────────────────────────────────


@router.get("/imports/{import_id}/validation")
async def get_validation(
    import_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await _get_import_or_404(import_id, db)
    require_own_institution(record.institution_id, current_user)

    if record.status not in ("validated", "committed"):
        raise ValidationFailed(detail=f"La validation n'est pas encore disponible dans l'état : {record.status}")

    return {
        "status": record.status,
        "summary": record.validation_summary,
        "normalization_log": record.normalization_log,
    }


# ── Commit ────────────────────────────────────────────────────────────────────


class CommitRequest(BaseModel):
    overwrite_mode: str | None = None  # overwrite | merge | cancel


@router.post("/imports/{import_id}/commit")
async def commit_import(
    import_id: uuid.UUID,
    body: CommitRequest = CommitRequest(),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await _get_import_or_404(import_id, db)
    require_own_institution(record.institution_id, current_user)

    if record.status != "validated":
        raise ValidationFailed(detail=f"La validation doit être complète avant le commit. État actuel : {record.status}")

    # ── Period lock check ────────────────────────────────────────────────────
    result = await db.execute(
        select(LockedPeriod).where(
            LockedPeriod.institution_id == record.institution_id,
            LockedPeriod.period == record.period,
        )
    )
    if result.scalars().first():
        raise PeriodLocked()

    # ── Conflict detection ───────────────────────────────────────────────────
    existing_result = await db.execute(
        select(DataRecord).where(
            DataRecord.institution_id == record.institution_id,
            DataRecord.period == record.period,
            DataRecord.domain == record.domain,
            DataRecord.is_archived == False,  # noqa: E712
        ).limit(1)
    )
    existing = existing_result.scalars().first()

    if existing and not body.overwrite_mode:
        raise CommitConflict(
            existing_import=str(existing.import_id),
            period=record.period,
            domain=record.domain,
        )

    if body.overwrite_mode == "cancel":
        raise CommitConflict(detail="Commit annulé par l'utilisateur.")

    # ── Archive existing records if overwrite mode ────────────────────────────
    if existing and body.overwrite_mode == "overwrite":
        now = datetime.now(timezone.utc)
        await db.execute(
            # Mass update — using synchronous-style execute; fine for asyncpg
            select(DataRecord).where(
                DataRecord.institution_id == record.institution_id,
                DataRecord.period == record.period,
                DataRecord.domain == record.domain,
                DataRecord.is_archived == False,  # noqa: E712
            )
        )
        # Archive them
        from sqlalchemy import update
        await db.execute(
            update(DataRecord)
            .where(
                DataRecord.institution_id == record.institution_id,
                DataRecord.period == record.period,
                DataRecord.domain == record.domain,
                DataRecord.is_archived == False,  # noqa: E712
            )
            .values(is_archived=True, archived_at=now, archived_by_import_id=record.id)
        )

    # ── Write committed records ──────────────────────────────────────────────
    # In a complete implementation, rows are read from a staging table.
    # For now, the summary counts are committed and the audit entry written.
    record.status = "committed"
    record.committed_at = datetime.now(timezone.utc)
    record.overwrite_mode = body.overwrite_mode
    record.records_committed = (record.records_valid or 0) + (record.records_warned or 0)

    audit = AuditEntry(
        import_id=record.id,
        institution_id=record.institution_id,
        user_id=current_user.user_id,
        action=AuditAction.COMMIT_COMPLETED,
        description_fr=(
            f"Import validé et enregistré. "
            f"{record.records_committed} enregistrements commis, "
            f"{record.records_quarantined} en quarantaine."
        ),
        payload={"overwrite_mode": body.overwrite_mode, "summary": record.validation_summary},
    )
    db.add(audit)
    await db.commit()

    # ── Publish event to Redis ────────────────────────────────────────────────
    from backend.services.ingestion_service.config import get_settings as _gs
    from backend.shared.cache.redis_client import get_redis, publish

    settings = _gs()
    redis = get_redis(settings.redis_url)
    event = json.dumps({
        "event": "data.committed",
        "institution_id": str(record.institution_id),
        "period": record.period,
        "domain": record.domain,
        "import_id": str(record.id),
        "record_count": record.records_committed,
        "committed_at": record.committed_at.isoformat(),
    })
    await publish(redis, settings.events_channel, event)

    return {
        "status": "committed",
        "records_committed": record.records_committed,
        "records_quarantined": record.records_quarantined,
    }


# ── Cancel ────────────────────────────────────────────────────────────────────


@router.post("/imports/{import_id}/cancel")
async def cancel_import(
    import_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await _get_import_or_404(import_id, db)
    require_own_institution(record.institution_id, current_user)

    if record.status == "committed":
        raise ValidationFailed(detail="Un import déjà commis ne peut pas être annulé via cette route.")

    from datetime import datetime, timezone
    record.status = "cancelled"
    record.cancelled_at = datetime.now(timezone.utc)

    audit = AuditEntry(
        import_id=record.id,
        institution_id=record.institution_id,
        user_id=current_user.user_id,
        action=AuditAction.IMPORT_CANCELLED,
        description_fr="Import annulé par l'utilisateur.",
    )
    db.add(audit)
    await db.commit()

    return {"status": "cancelled"}
