"""Data request management routes (analyst+ only).

POST  /requests
GET   /requests
GET   /requests/{id}
PATCH /requests/{id}/respond
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.ingestion_service.dependencies import CurrentUser, get_current_user, get_db
from backend.services.ingestion_service.models.import_record import DataRequest, DataRequestResponse
from backend.shared.auth.rbac import Permission, Role, require
from backend.shared.exceptions import NotFound, PermissionDenied

router = APIRouter()


class DataRequestCreate(BaseModel):
    title: str
    domain: str
    period: str
    deadline: datetime
    notes: str | None = None
    target_institutions: list[str]  # list of institution UUID strings


class DataRequestRespond(BaseModel):
    status: str  # not_started | in_progress | submitted | late
    import_id: str | None = None


@router.post("/requests", status_code=201)
async def create_request(
    body: DataRequestCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require(current_user.role, Permission.MANAGE_DATA_REQUESTS)

    request = DataRequest(
        created_by=current_user.user_id,
        title=body.title,
        domain=body.domain,
        period=body.period,
        deadline=body.deadline,
        notes=body.notes,
        target_institutions=body.target_institutions,
    )
    db.add(request)
    await db.flush()

    for inst_id_str in body.target_institutions:
        response = DataRequestResponse(
            request_id=request.id,
            institution_id=uuid.UUID(inst_id_str),
            status="not_started",
        )
        db.add(response)

    await db.commit()
    return {"request_id": str(request.id), "status": "created"}


@router.get("/requests")
async def list_requests(
    domain: str | None = Query(None),
    period: str | None = Query(None),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require(current_user.role, Permission.VIEW_INSTITUTION_KPIS)

    stmt = select(DataRequest).order_by(DataRequest.created_at.desc())
    if domain:
        stmt = stmt.where(DataRequest.domain == domain)
    if period:
        stmt = stmt.where(DataRequest.period == period)

    # Institution admins only see requests targeting them
    if current_user.role in (Role.INSTITUTION_ADMIN, Role.INSTITUTION_DIRECTOR):
        # Filter via responses
        inst_str = str(current_user.institution_id)
        # SQLAlchemy JSON containment — Postgres JSONB @> operator
        from sqlalchemy import cast
        from sqlalchemy.dialects.postgresql import JSONB
        stmt = stmt.where(
            DataRequest.target_institutions.cast(JSONB).contains([inst_str])
        )

    result = await db.execute(stmt)
    requests = result.scalars().all()

    return [
        {
            "request_id": str(r.id),
            "title": r.title,
            "domain": r.domain,
            "period": r.period,
            "deadline": r.deadline.isoformat(),
            "target_count": len(r.target_institutions),
            "created_at": r.created_at.isoformat(),
        }
        for r in requests
    ]


@router.get("/requests/{request_id}")
async def get_request(
    request_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    require(current_user.role, Permission.VIEW_INSTITUTION_KPIS)

    req = await db.get(DataRequest, request_id)
    if not req:
        raise NotFound(detail=f"Demande {request_id} introuvable.")

    result = await db.execute(
        select(DataRequestResponse).where(DataRequestResponse.request_id == request_id)
    )
    responses = result.scalars().all()

    return {
        "request_id": str(req.id),
        "title": req.title,
        "domain": req.domain,
        "period": req.period,
        "deadline": req.deadline.isoformat(),
        "notes": req.notes,
        "target_institutions": req.target_institutions,
        "responses": [
            {
                "institution_id": str(r.institution_id),
                "status": r.status,
                "import_id": str(r.import_id) if r.import_id else None,
                "updated_at": r.updated_at.isoformat(),
            }
            for r in responses
        ],
    }


@router.patch("/requests/{request_id}/respond")
async def respond_to_request(
    request_id: uuid.UUID,
    body: DataRequestRespond,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DataRequestResponse).where(
            DataRequestResponse.request_id == request_id,
            DataRequestResponse.institution_id == current_user.institution_id,
        )
    )
    response = result.scalars().first()
    if not response:
        raise NotFound(detail="Aucune réponse à cette demande pour votre établissement.")

    valid_statuses = ("not_started", "in_progress", "submitted")
    if body.status not in valid_statuses:
        from backend.shared.exceptions import ValidationFailed
        raise ValidationFailed(detail=f"Statut invalide. Choisissez parmi : {valid_statuses}")

    response.status = body.status
    if body.import_id:
        response.import_id = uuid.UUID(body.import_id)

    await db.commit()
    return {"status": body.status}
