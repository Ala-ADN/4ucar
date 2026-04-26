"""KPI computation dispatcher.

Aggregates per-domain calculators. Every calculator is a pure function over a
typed input bundle and returns a `KpiResult`; the dispatcher just runs them.

Domain H (accreditation) is the exception - it returns
`dict[framework_code, list[ControlEvaluation]]`, not `list[KpiResult]`,
because compliance is qualitative (status), not quantitative (value).
"""

from __future__ import annotations

from collections.abc import Iterable

from .academic import DOMAIN_B_CALCULATORS
from .accreditation import evaluate_accreditation
from .employment import DOMAIN_C_CALCULATORS
from .finance import DOMAIN_E_CALCULATORS
from .hr import DOMAIN_F_CALCULATORS
from .inputs import (
    InstitutionAcademicInputs,
    InstitutionAccreditationInputs,
    InstitutionEmploymentInputs,
    InstitutionEsgInputs,
    InstitutionFinanceInputs,
    InstitutionHrInputs,
    InstitutionInternationalInputs,
    InstitutionResearchInputs,
)
from .international import DOMAIN_D_CALCULATORS
from .research import DOMAIN_A_CALCULATORS
from .result import ControlEvaluation, KpiResult
from .sustainability import DOMAIN_G_CALCULATORS

# ---------------------------------------------------------------------------
# Domain A - Research & Citations
# ---------------------------------------------------------------------------


def compute_research_domain(inputs: InstitutionResearchInputs) -> list[KpiResult]:
    """Run every Domain A calculator for one institution + period."""
    return [calc(inputs) for calc in DOMAIN_A_CALCULATORS]


def compute_research_for_network(
    institutions: Iterable[InstitutionResearchInputs],
) -> dict[str, list[KpiResult]]:
    """Run Domain A across the network; key results by `institution_code`."""
    return {inst.institution_code: compute_research_domain(inst) for inst in institutions}


# ---------------------------------------------------------------------------
# Domain B - Academic Quality & Teaching
# ---------------------------------------------------------------------------


def compute_academic_domain(inputs: InstitutionAcademicInputs) -> list[KpiResult]:
    """Run every Domain B calculator for one institution + period."""
    return [calc(inputs) for calc in DOMAIN_B_CALCULATORS]


def compute_academic_for_network(
    institutions: Iterable[InstitutionAcademicInputs],
) -> dict[str, list[KpiResult]]:
    """Run Domain B across the network; key results by `institution_code`."""
    return {inst.institution_code: compute_academic_domain(inst) for inst in institutions}


# ---------------------------------------------------------------------------
# Domain C - Employability & Industry Relations
# ---------------------------------------------------------------------------


def compute_employment_domain(inputs: InstitutionEmploymentInputs) -> list[KpiResult]:
    """Run every Domain C calculator for one institution + period."""
    return [calc(inputs) for calc in DOMAIN_C_CALCULATORS]


def compute_employment_for_network(
    institutions: Iterable[InstitutionEmploymentInputs],
) -> dict[str, list[KpiResult]]:
    """Run Domain C across the network; key results by `institution_code`."""
    return {inst.institution_code: compute_employment_domain(inst) for inst in institutions}


# ---------------------------------------------------------------------------
# Domain D - Internationalization
# ---------------------------------------------------------------------------


def compute_international_domain(inputs: InstitutionInternationalInputs) -> list[KpiResult]:
    """Run every Domain D calculator for one institution + period."""
    return [calc(inputs) for calc in DOMAIN_D_CALCULATORS]


def compute_international_for_network(
    institutions: Iterable[InstitutionInternationalInputs],
) -> dict[str, list[KpiResult]]:
    """Run Domain D across the network; key results by `institution_code`."""
    return {inst.institution_code: compute_international_domain(inst) for inst in institutions}


# ---------------------------------------------------------------------------
# Domain E - Finance & Resources
# ---------------------------------------------------------------------------


def compute_finance_domain(inputs: InstitutionFinanceInputs) -> list[KpiResult]:
    """Run every Domain E calculator for one institution + period."""
    return [calc(inputs) for calc in DOMAIN_E_CALCULATORS]


def compute_finance_for_network(
    institutions: Iterable[InstitutionFinanceInputs],
) -> dict[str, list[KpiResult]]:
    """Run Domain E across the network; key results by `institution_code`."""
    return {inst.institution_code: compute_finance_domain(inst) for inst in institutions}


# ---------------------------------------------------------------------------
# Domain F - Human Resources
# ---------------------------------------------------------------------------


def compute_hr_domain(inputs: InstitutionHrInputs) -> list[KpiResult]:
    """Run every Domain F calculator for one institution + period."""
    return [calc(inputs) for calc in DOMAIN_F_CALCULATORS]


def compute_hr_for_network(
    institutions: Iterable[InstitutionHrInputs],
) -> dict[str, list[KpiResult]]:
    """Run Domain F across the network; key results by `institution_code`."""
    return {inst.institution_code: compute_hr_domain(inst) for inst in institutions}


# ---------------------------------------------------------------------------
# Domain G - Sustainability & ESG
# ---------------------------------------------------------------------------


def compute_esg_domain(inputs: InstitutionEsgInputs) -> list[KpiResult]:
    """Run every Domain G calculator for one institution + period."""
    return [calc(inputs) for calc in DOMAIN_G_CALCULATORS]


def compute_esg_for_network(
    institutions: Iterable[InstitutionEsgInputs],
) -> dict[str, list[KpiResult]]:
    """Run Domain G across the network; key results by `institution_code`."""
    return {inst.institution_code: compute_esg_domain(inst) for inst in institutions}


# ---------------------------------------------------------------------------
# Domain H - Accreditation & Compliance (qualitative; returns ControlEvaluation)
# ---------------------------------------------------------------------------


def compute_accreditation(
    inputs: InstitutionAccreditationInputs,
) -> dict[str, list[ControlEvaluation]]:
    """Evaluate every active framework's controls for one institution.

    Returns {framework_code: [ControlEvaluation, ...]}.
    """
    return evaluate_accreditation(inputs)


def compute_accreditation_for_network(
    institutions: Iterable[InstitutionAccreditationInputs],
) -> dict[str, dict[str, list[ControlEvaluation]]]:
    """Run Domain H across the network: {institution_code: {framework_code: [...]}}."""
    return {inst.institution_code: compute_accreditation(inst) for inst in institutions}
