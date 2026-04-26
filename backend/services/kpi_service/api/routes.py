"""KPI HTTP routes.

Endpoints (per spec section 11):
    GET  /kpi/definitions                 - full catalog (in-memory, no DB)
    GET  /kpi/records                     - tenant's KPI records (filterable)
    GET  /kpi/records/{kpi_id}/trend      - time-series for one KPI
    POST /kpi/recompute                   - run all 7 dispatchers + persist

All tenant-scoped endpoints require `X-Tenant-Id` (UUID) header.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from backend.services.kpi_service.api.dependencies import SessionDep, TenantDep
from backend.services.kpi_service.domain.catalog import CATALOG, CATALOG_BY_ID
from backend.services.kpi_service.repositories import KpiRecordRepository
from backend.services.kpi_service.schemas.kpi import (
    KpiDefinitionRead,
    KpiRecomputeRequest,
    KpiRecomputeResponse,
    KpiRecordRead,
    KpiTrendPoint,
    KpiTrendRead,
)
from backend.services.kpi_service.services.recompute import (
    empty_inputs,
    recompute_all_domains,
)

router = APIRouter(prefix="/kpi", tags=["kpi"])


@router.get(
    "/definitions",
    response_model=list[KpiDefinitionRead],
    summary="List the KPI catalog",
)
async def list_kpi_definitions(
    domain: str | None = Query(default=None, description="Filter by domain code"),
) -> list[KpiDefinitionRead]:
    items = CATALOG
    if domain:
        d = domain.upper()
        items = [x for x in items if x.domain == d]
    return [KpiDefinitionRead.from_descriptor(x) for x in items]


@router.get(
    "/records",
    response_model=list[KpiRecordRead],
    summary="List computed KPI records for the current tenant",
)
async def list_kpi_records(
    session: SessionDep,
    tenant_id: TenantDep,
    domain: str | None = Query(default=None),
    period_start: date | None = Query(default=None),
    period_end: date | None = Query(default=None),
) -> list[KpiRecordRead]:
    repo = KpiRecordRepository(session)
    records = await repo.list_for_tenant(
        tenant_id,
        domain=domain,
        period_start=period_start,
        period_end=period_end,
    )
    return [
        KpiRecordRead.from_orm_with_descriptor(r, CATALOG_BY_ID[r.kpi_id])
        for r in records
        if r.kpi_id in CATALOG_BY_ID
    ]


@router.get(
    "/records/{kpi_id}/trend",
    response_model=KpiTrendRead,
    summary="Time-series trend for one KPI",
)
async def get_kpi_trend(
    kpi_id: str,
    session: SessionDep,
    tenant_id: TenantDep,
    periods: int = Query(default=12, ge=1, le=120),
) -> KpiTrendRead:
    descriptor = CATALOG_BY_ID.get(kpi_id)
    if descriptor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown KPI id: {kpi_id}",
        )
    repo = KpiRecordRepository(session)
    records = await repo.get_trend(tenant_id, kpi_id, limit=periods)
    return KpiTrendRead(
        kpi_id=descriptor.kpi_id,
        name=descriptor.name,
        domain=descriptor.domain,
        unit=descriptor.unit,
        points=[
            KpiTrendPoint(
                period_start=r.period_start,
                period_end=r.period_end,
                value=float(r.value) if r.value is not None else None,
                is_complete=r.is_complete,
            )
            for r in records
        ],
    )


@router.post(
    "/recompute",
    response_model=KpiRecomputeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Recompute every numeric KPI for the tenant + period",
)
async def post_recompute(
    request: KpiRecomputeRequest,
    session: SessionDep,
    tenant_id: TenantDep,
) -> KpiRecomputeResponse:
    """Runs the full Domain A-G dispatchers and upserts KpiRecord rows.

    For now this uses empty input bundles - every KPI returns a record
    with `value=None` and `missing_fields` populated, which is the
    correct bootstrap state for a tenant with no ingested data yet.

    When the doc-service is online, swap `empty_inputs` for a real
    repository-backed loader inside this handler (or push it into a
    Celery task).
    """
    if request.period_end < request.period_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="period_end must be >= period_start",
        )

    inputs = empty_inputs(
        institution_id=str(tenant_id),
        institution_code=str(tenant_id),
        period_start=request.period_start,
        period_end=request.period_end,
    )
    summary = await recompute_all_domains(
        session, tenant_id=tenant_id, inputs=inputs
    )
    await session.commit()

    return KpiRecomputeResponse(
        tenant_id=tenant_id,
        period_start=request.period_start,
        period_end=request.period_end,
        records_computed=summary.total,
        complete=summary.complete,
        estimated=summary.estimated,
        uncomputable=summary.uncomputable,
    )
