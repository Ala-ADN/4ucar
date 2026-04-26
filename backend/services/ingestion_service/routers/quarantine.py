"""Quarantine management routes.

GET  /imports/{import_id}/quarantine
POST /imports/{import_id}/quarantine/{quarantine_id}/resolve
"""

from __future__ import annotations

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
from backend.services.ingestion_service.models.import_record import ImportRecord, QuarantineRow
from backend.shared.auth.rbac import Permission, require
from backend.shared.exceptions import NotFound, PermissionDenied, ValidationFailed

router = APIRouter()


@router.get("/imports/{import_id}/quarantine")
async def list_quarantine(
    import_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await db.get(ImportRecord, import_id)
    if not record:
        raise NotFound(detail=f"Import {import_id} introuvable.")
    require_own_institution(record.institution_id, current_user)

    result = await db.execute(
        select(QuarantineRow)
        .where(QuarantineRow.import_id == import_id)
        .order_by(QuarantineRow.row_index)
    )
    rows = result.scalars().all()

    return {
        "import_id": str(import_id),
        "quarantine_count": len(rows),
        "rows": [
            {
                "id": str(row.id),
                "row_index": row.row_index,
                "raw_data": row.raw_data,
                "failed_field": row.failed_field,
                "failure_reason_fr": row.failure_reason_fr,
                "resolution": row.resolution,
                "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
            }
            for row in rows
        ],
    }


class QuarantineResolution(BaseModel):
    resolution: str  # correct | override | discard
    corrected_value: str | float | int | None = None
    override_justification: str | None = None


@router.post("/imports/{import_id}/quarantine/{quarantine_id}/resolve")
async def resolve_quarantine(
    import_id: uuid.UUID,
    quarantine_id: uuid.UUID,
    body: QuarantineResolution,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await db.get(ImportRecord, import_id)
    if not record:
        raise NotFound(detail=f"Import {import_id} introuvable.")
    require_own_institution(record.institution_id, current_user)

    q_row = await db.get(QuarantineRow, quarantine_id)
    if not q_row or q_row.import_id != import_id:
        raise NotFound(detail=f"Ligne de quarantaine {quarantine_id} introuvable.")

    if body.resolution not in ("correct", "override", "discard"):
        raise ValidationFailed(detail="La résolution doit être : correct, override ou discard.")

    # Only analyst+ can force-override an INVALID row
    if body.resolution == "override":
        require(current_user.role, Permission.OVERRIDE_QUARANTINE)
        if not body.override_justification:
            raise ValidationFailed(detail="Une justification est requise pour forcer l'import d'une ligne invalide.")

    q_row.resolution = body.resolution
    q_row.corrected_value = body.corrected_value
    q_row.override_justification = body.override_justification
    q_row.resolved_by = current_user.user_id
    q_row.resolved_at = datetime.now(timezone.utc)

    audit = AuditEntry(
        import_id=import_id,
        institution_id=record.institution_id,
        user_id=current_user.user_id,
        action=AuditAction.QUARANTINE_RESOLVED,
        description_fr=(
            f"Ligne {q_row.row_index} résolue : {body.resolution}. "
            f"Champ : {q_row.failed_field}."
        ),
        payload={
            "quarantine_id": str(quarantine_id),
            "resolution": body.resolution,
            "corrected_value": body.corrected_value,
            "justification": body.override_justification,
        },
    )
    db.add(audit)
    await db.commit()

    return {
        "quarantine_id": str(quarantine_id),
        "resolution": body.resolution,
        "resolved_at": q_row.resolved_at.isoformat(),
    }
