"""KPI computation dispatcher.

Aggregates per-domain calculators. Every calculator is a pure function over a
typed input bundle and returns a `KpiResult`; the dispatcher just runs them.
"""

from __future__ import annotations

from collections.abc import Iterable

from .inputs import InstitutionResearchInputs
from .research import DOMAIN_A_CALCULATORS
from .result import KpiResult


def compute_research_domain(inputs: InstitutionResearchInputs) -> list[KpiResult]:
    """Run every Domain A calculator for one institution + period."""
    return [calc(inputs) for calc in DOMAIN_A_CALCULATORS]


def compute_research_for_network(
    institutions: Iterable[InstitutionResearchInputs],
) -> dict[str, list[KpiResult]]:
    """Run Domain A for every institution; key results by `institution_code`.

    Use when iterating across the 35 UCAR institutions for the network
    dashboard or ranking computation.
    """
    return {inst.institution_code: compute_research_domain(inst) for inst in institutions}
