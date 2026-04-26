"""KPI recompute orchestrator.

Runs the 7 numeric-domain dispatchers for one tenant + period and upserts
the resulting KpiRecord rows. The orchestrator is decoupled from input
loading: callers pass a `RecomputeInputs` bundle holding pre-built
domain inputs. The default `empty_inputs(...)` factory yields all-MISSING
records, which is the correct baseline for a tenant with no ingested
data yet (the records flag exactly which uploads are required).

When the doc-service repositories come online, swap `empty_inputs(...)`
for a loader that pulls real faculty/students/budgets/etc.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.kpi_service.domain import (
    InstitutionAcademicInputs,
    InstitutionEmploymentInputs,
    InstitutionEsgInputs,
    InstitutionFinanceInputs,
    InstitutionHrInputs,
    InstitutionInternationalInputs,
    InstitutionResearchInputs,
    KpiResult,
    compute_academic_domain,
    compute_employment_domain,
    compute_esg_domain,
    compute_finance_domain,
    compute_hr_domain,
    compute_international_domain,
    compute_research_domain,
)
from backend.services.kpi_service.repositories import KpiRecordRepository
from backend.services.kpi_service.schemas.kpi import kpi_result_to_record_kwargs


@dataclass
class RecomputeInputs:
    """All seven per-domain input bundles for one institution + period."""

    research: InstitutionResearchInputs
    academic: InstitutionAcademicInputs
    employment: InstitutionEmploymentInputs
    international: InstitutionInternationalInputs
    finance: InstitutionFinanceInputs
    hr: InstitutionHrInputs
    esg: InstitutionEsgInputs


@dataclass
class RecomputeSummary:
    total: int
    complete: int
    estimated: int
    uncomputable: int


def empty_inputs(
    *,
    institution_id: str,
    institution_code: str,
    period_start: date,
    period_end: date,
) -> RecomputeInputs:
    """Build a RecomputeInputs with no faculty/students/etc.

    Every dispatcher will return KpiResult records with `value=None` and
    `missing_fields` populated - this is the desired bootstrap state for
    a brand-new tenant.
    """
    common = dict(
        institution_id=institution_id,
        institution_code=institution_code,
        period_start=period_start,
        period_end=period_end,
    )
    return RecomputeInputs(
        research=InstitutionResearchInputs(**common),
        academic=InstitutionAcademicInputs(**common),
        employment=InstitutionEmploymentInputs(**common),
        international=InstitutionInternationalInputs(**common),
        finance=InstitutionFinanceInputs(**common),
        hr=InstitutionHrInputs(**common),
        esg=InstitutionEsgInputs(**common),
    )


def _run_all_dispatchers(inputs: RecomputeInputs) -> list[KpiResult]:
    return [
        *compute_research_domain(inputs.research),
        *compute_academic_domain(inputs.academic),
        *compute_employment_domain(inputs.employment),
        *compute_international_domain(inputs.international),
        *compute_finance_domain(inputs.finance),
        *compute_hr_domain(inputs.hr),
        *compute_esg_domain(inputs.esg),
    ]


async def recompute_all_domains(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    inputs: RecomputeInputs,
) -> RecomputeSummary:
    """Run every numeric-domain calculator and persist the results.

    Caller commits the session.
    """
    results = _run_all_dispatchers(inputs)
    repo = KpiRecordRepository(session)
    await repo.upsert_many(
        [kpi_result_to_record_kwargs(r, tenant_id=tenant_id) for r in results]
    )
    return RecomputeSummary(
        total=len(results),
        complete=sum(1 for r in results if r.is_complete),
        estimated=sum(1 for r in results if r.is_estimated),
        uncomputable=sum(1 for r in results if r.value is None),
    )
