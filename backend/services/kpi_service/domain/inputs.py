"""Typed input bundles for Domain A (Research & Citations) KPIs.

These dataclasses are the *contract* between the persistence layer and the KPI
calculators. The computation code never touches a database; it only consumes
these structures, which makes calculators testable in isolation and prevents
schema lock-in. Repositories (or integrations like Google Scholar) are
responsible for populating them.

Every numeric field that may be unknown is typed `| None` so the calculators
can flag missing inputs explicitly rather than silently treat them as zero.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Publication:
    """A peer-reviewed publication attached to a faculty member.

    Fields populated by Scopus / WoS / Google Scholar / parsed publication-list
    documents. Anything we cannot determine stays `None` so the calculator can
    distinguish "missing data" from "zero".
    """

    title: str
    year: int | None
    citation_count: int | None = None
    is_peer_reviewed: bool = True
    is_open_access: bool | None = None
    coauthor_countries: list[str] | None = None
    field_top_1pct: bool | None = None
    doi: str | None = None
    source: str = "unknown"


@dataclass
class FacultyMember:
    """A single academic staff member contributing to research KPIs."""

    id: str
    full_name: str
    is_active: bool = True
    fte_fraction: float = 1.0
    h_index: int | None = None
    home_country: str = "TN"
    publications: list[Publication] = field(default_factory=list)


@dataclass
class FundedProject:
    """An externally funded R&D project (RES-05, RES-06)."""

    id: str
    title: str
    amount_tnd: float | None
    is_external: bool
    is_active: bool
    start_date: date | None = None
    end_date: date | None = None


@dataclass
class DoctoralStudent:
    """A doctoral candidate; `awarded_date` is set the year their PhD is granted."""

    id: str
    is_active: bool
    enrollment_date: date | None = None
    awarded_date: date | None = None


@dataclass
class ConsultancyContract:
    """Knowledge-transfer or consultancy revenue contract (RES-10)."""

    id: str
    revenue_tnd: float | None
    contract_date: date | None = None


@dataclass
class InstitutionResearchInputs:
    """Everything Domain A needs for one institution and one period.

    `period_start` / `period_end` define the period this computation is for.
    Five-year-window KPIs (RES-01, RES-03) derive their cutoff from `period_end`.
    """

    institution_id: str
    institution_code: str
    period_start: date
    period_end: date
    faculty: list[FacultyMember] = field(default_factory=list)
    funded_projects: list[FundedProject] = field(default_factory=list)
    doctoral_students: list[DoctoralStudent] = field(default_factory=list)
    consultancy_contracts: list[ConsultancyContract] = field(default_factory=list)
    home_country: str = "TN"


def five_year_window(period_end: date) -> tuple[int, int]:
    """Return (first_year, last_year) inclusive for the rolling 5-year window."""
    return period_end.year - 4, period_end.year


def total_active_fte(faculty: list[FacultyMember]) -> float:
    """Sum of FTE fractions for active faculty (denominator for many KPIs)."""
    return sum(f.fte_fraction for f in faculty if f.is_active)
