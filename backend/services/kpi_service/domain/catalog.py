"""KPI catalog - the canonical list of every numeric KPI the engine knows.

Built once by introspecting the calculator registries: each calculator is
called with an empty input bundle, and the resulting `KpiResult` carries
the kpi_id / name / domain / formula / unit metadata we need.

This avoids maintaining a parallel hand-coded catalog that could drift
from the calculators.

Domain H (accreditation) is intentionally excluded - it returns
ControlEvaluation, not KpiResult, and its catalog is the per-tenant
framework + control set, not a static KPI list.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .computation import (
    compute_academic_domain,
    compute_employment_domain,
    compute_esg_domain,
    compute_finance_domain,
    compute_hr_domain,
    compute_international_domain,
    compute_research_domain,
)
from .inputs import (
    InstitutionAcademicInputs,
    InstitutionEmploymentInputs,
    InstitutionEsgInputs,
    InstitutionFinanceInputs,
    InstitutionHrInputs,
    InstitutionInternationalInputs,
    InstitutionResearchInputs,
)


@dataclass(frozen=True)
class KpiDescriptor:
    """Static catalog metadata for one KPI."""

    kpi_id: str
    name: str
    domain: str
    formula: str
    unit: str


# Periods used only to instantiate the empty input bundles below; the
# calculator metadata they emit (kpi_id/name/formula/unit) is independent
# of period bounds.
_CATALOG_PERIOD_START = date(2000, 1, 1)
_CATALOG_PERIOD_END = date(2000, 12, 31)


def _empty(cls):
    return cls(
        institution_id="",
        institution_code="",
        period_start=_CATALOG_PERIOD_START,
        period_end=_CATALOG_PERIOD_END,
    )


_DISPATCHERS_WITH_EMPTY_INPUTS = (
    (compute_research_domain, InstitutionResearchInputs),
    (compute_academic_domain, InstitutionAcademicInputs),
    (compute_employment_domain, InstitutionEmploymentInputs),
    (compute_international_domain, InstitutionInternationalInputs),
    (compute_finance_domain, InstitutionFinanceInputs),
    (compute_hr_domain, InstitutionHrInputs),
    (compute_esg_domain, InstitutionEsgInputs),
)


def build_catalog() -> list[KpiDescriptor]:
    """Run every dispatcher once with empty inputs and harvest metadata."""
    descriptors: list[KpiDescriptor] = []
    for dispatcher, inputs_cls in _DISPATCHERS_WITH_EMPTY_INPUTS:
        for result in dispatcher(_empty(inputs_cls)):
            descriptors.append(
                KpiDescriptor(
                    kpi_id=result.kpi_id,
                    name=result.name,
                    domain=result.domain,
                    formula=result.formula,
                    unit=result.unit,
                )
            )
    return descriptors


# Eager-evaluate at import time - the catalog is small (~65 entries) and
# idempotent. Consumers should treat as immutable.
CATALOG: list[KpiDescriptor] = build_catalog()
CATALOG_BY_ID: dict[str, KpiDescriptor] = {d.kpi_id: d for d in CATALOG}
