"""KPI domain layer — pure-function calculators decoupled from persistence.

Public API:
    InstitutionResearchInputs       — typed input bundle for Domain A
    KpiResult                       — uniform return type with missing-field flags
    compute_research_domain()       — runs all RES-01..RES-11 for one institution
    compute_research_for_network()  — runs Domain A across many institutions
"""

from .computation import compute_research_domain, compute_research_for_network
from .inputs import (
    ConsultancyContract,
    DoctoralStudent,
    FacultyMember,
    FundedProject,
    InstitutionResearchInputs,
    Publication,
)
from .result import KpiResult

__all__ = [
    "ConsultancyContract",
    "DoctoralStudent",
    "FacultyMember",
    "FundedProject",
    "InstitutionResearchInputs",
    "KpiResult",
    "Publication",
    "compute_research_domain",
    "compute_research_for_network",
]
