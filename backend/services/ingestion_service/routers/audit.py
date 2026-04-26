"""GET /audit — paginated audit log (analyst+ only)."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.ingestion_service.dependencies import CurrentUser, get_current_user, get_db
from backend.services.ingestion_service.models.audit import AuditEntry
from backend.shared.auth.rbac import Permission, require

router = APIRouter()


@router.get("/audit")
async def list_audit(
    import_id: uuid.UUID | None = Query(None),
    institution_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require(current_user.role, Permission.VIEW_AUDIT_LOG)

    stmt = select(AuditEntry).order_by(AuditEntry.created_at.desc())

    if import_id:
        stmt = stmt.where(AuditEntry.import_id == import_id)
    if institution_id:
        stmt = stmt.where(AuditEntry.institution_id == institution_id)
    if action:
        stmt = stmt.where(AuditEntry.action == action)

    # Institution-scoped users can only see their own institution's audit log
    from backend.shared.auth.rbac import Role
    if current_user.role not in (Role.SUPER_ADMIN, Role.UCAR_ANALYST, Role.IT_ADMIN):
        stmt = stmt.where(AuditEntry.institution_id == current_user.institution_id)

    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    entries = result.scalars().all()

    return {
        "page": page,
        "page_size": page_size,
        "entries": [
            {
                "id": str(e.id),
                "import_id": str(e.import_id) if e.import_id else None,
                "institution_id": str(e.institution_id),
                "user_id": str(e.user_id),
                "action": e.action,
                "description_fr": e.description_fr,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ],
    }
