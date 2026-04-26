"""Typed input bundles for KPI computation, decoupled from persistence.

These dataclasses are the *contract* between the persistence layer and the KPI
calculators. The computation code never touches a database; it only consumes
these structures, which makes calculators testable in isolation and prevents
schema lock-in. Repositories (or integrations like OpenAlex) are responsible
for populating them.

Every numeric field that may be unknown is typed `| None` so the calculators
can flag missing inputs explicitly rather than silently treat them as zero.

Currently covers:
    - Domain A (Research & Citations) - InstitutionResearchInputs
    - Domain B (Academic Quality & Teaching) - InstitutionAcademicInputs
    - Domain C (Employability & Industry Relations) - InstitutionEmploymentInputs
    - Domain D (Internationalization) - InstitutionInternationalInputs
    - Domain E (Finance & Resources) - InstitutionFinanceInputs
    - Domain F (Human Resources) - InstitutionHrInputs
    - Domain G (Sustainability & ESG) - InstitutionEsgInputs
    - Domain H (Accreditation & Compliance) - InstitutionAccreditationInputs
      (framework/control/test/evidence model per .claude/accreditation.md,
       not numeric KPIs - the evaluator returns ControlEvaluation, not KpiResult)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum


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
    sdg_aligned: bool | None = None  # ESG-08
    doi: str | None = None
    source: str = "unknown"


@dataclass
class FacultyMember:
    """A single academic staff member.

    Shared across all domains. Each domain reads only the fields it needs;
    repositories populate whatever they have data for. The dataclass
    accumulates fields rather than splitting into per-domain subtypes
    because faculty are one entity, not eight.

    `home_country` is the institution's country (legacy Domain A field
    superseded by `inputs.home_country`); it is NOT the faculty member's
    nationality - use `nationality_country` for that.
    """

    id: str
    full_name: str
    is_active: bool = True
    fte_fraction: float = 1.0
    # --- Domain A ---
    h_index: int | None = None
    publications: list[Publication] = field(default_factory=list)
    # --- Domain B ---
    holds_phd: bool | None = None
    # --- Domain D ---
    home_country: str = "TN"
    nationality_country: str | None = None
    highest_degree_country: str | None = None
    # --- Domain F (HR) ---
    is_permanent: bool | None = None
    contracted_hours: int | None = None  # per period
    delivered_hours: int | None = None
    training_hours_required: int | None = None
    training_hours_completed: int | None = None
    scheduled_workdays: int | None = None
    unexcused_absence_days: int | None = None
    expertise_matches_courses: bool | None = None
    # --- Domain G (ESG) ---
    gender: str | None = None  # "F" | "M" | "X" | None


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


# ---------------------------------------------------------------------------
# Domain B — Academic Quality & Teaching
# ---------------------------------------------------------------------------


class StudentStatus(StrEnum):
    """Mutually-exclusive lifecycle states for a student in the period.

    A "currently enrolled" denominator is `ACTIVE + REPEATING`. ON_LEAVE
    students are not counted as enrolled.
    """

    ACTIVE = "active"
    REPEATING = "repeating"
    GRADUATED = "graduated"
    DROPPED_OUT = "dropped_out"
    ON_LEAVE = "on_leave"


@dataclass
class Student:
    """One student record scoped to one institution and one period.

    Cohort identity is `cohort_year` (the year of first enrollment in the
    program). KPI-specific fields stay `None` when their data isn't yet
    available so calculators can flag them explicitly.

    Domain B uses status / GPA / certification / at-risk fields.
    Domain C uses is_final_year / internship / career-services fields.
    """

    id: str
    cohort_year: int | None = None
    status: StudentStatus | None = None
    # --- Domain B ---
    passed_all_modules: bool | None = None
    gpa: float | None = None
    has_industry_certification: bool | None = None
    is_at_risk: bool | None = None
    received_remediation_support: bool | None = None
    # --- Domain C ---
    is_final_year: bool | None = None
    internship_required: bool | None = None
    completed_required_internship: bool | None = None
    used_career_services: bool | None = None
    # --- Domain D ---
    nationality_country: str | None = None
    is_outgoing_exchange: bool | None = None
    is_incoming_exchange: bool | None = None


@dataclass
class Module:
    """A teaching module/course offered in the period.

    Required vs delivered hours feed ACA-05; scheduled vs unexcused-absence
    hours feed ACA-11.
    """

    id: str
    code: str
    name: str
    required_hours: int | None = None
    delivered_hours: int | None = None
    scheduled_class_hours: int | None = None
    unexcused_absence_hours: int | None = None


@dataclass
class Program:
    """A degree program offered by the institution."""

    id: str
    name: str
    is_active: bool = True
    has_external_accreditation: bool | None = None
    double_degree_partner_country: str | None = None  # set when there's a foreign DD
    teaching_languages: list[str] | None = None  # ISO-639 codes; None == unknown


@dataclass
class InstitutionAcademicInputs:
    """Everything Domain B needs for one institution and one period."""

    institution_id: str
    institution_code: str
    period_start: date
    period_end: date
    faculty: list[FacultyMember] = field(default_factory=list)
    students: list[Student] = field(default_factory=list)
    modules: list[Module] = field(default_factory=list)
    programs: list[Program] = field(default_factory=list)
    home_country: str = "TN"


def currently_enrolled(students: list[Student]) -> list[Student]:
    """Students whose status counts toward the 'enrolled' denominator."""
    return [
        s
        for s in students
        if s.status in (StudentStatus.ACTIVE, StudentStatus.REPEATING)
    ]


# ---------------------------------------------------------------------------
# Domain C - Employability & Industry Relations
# ---------------------------------------------------------------------------


@dataclass
class GraduateSurveyResponse:
    """One response from the post-graduation employment outcomes survey.

    `responded` is True when we have *any* signal from the graduate; the
    employment fields stay None when the graduate did not answer those
    questions (vs answered "no" which is False). EMP-01 / EMP-03 calculators
    distinguish the two so non-response bias is visible.
    """

    graduate_id: str
    graduation_date: date | None = None
    responded: bool = True
    employed_within_12_months: bool | None = None
    months_to_first_employment: int | None = None


@dataclass
class EmployerSurveyResponse:
    """One employer's reputation rating in the structured survey.

    `score` is 0..100 (already normalized). `weight` lets the calculator
    weight by employer size, sector prestige, or stratified-sample weights.
    """

    response_id: str
    score: float
    weight: float = 1.0
    employer_country: str | None = None


@dataclass
class IndustryPartnership:
    """Formal agreement (MOU, contract) with an external partner."""

    id: str
    partner_name: str
    is_active: bool
    is_private_sector: bool = True
    start_date: date | None = None
    end_date: date | None = None


@dataclass
class PfeProject:
    """Final-year project (Projet de Fin d'Etudes)."""

    id: str
    student_id: str | None = None
    hosted_by_industry: bool | None = None
    completion_date: date | None = None


@dataclass
class Alumnus:
    """A graduate within the alumni-engagement window (typically 5 years)."""

    id: str
    graduation_year: int | None = None
    engaged_in_period: bool | None = None  # responded to survey OR attended event


@dataclass
class InstitutionEmploymentInputs:
    """Everything Domain C needs for one institution and one period."""

    institution_id: str
    institution_code: str
    period_start: date
    period_end: date
    students: list[Student] = field(default_factory=list)
    graduate_surveys: list[GraduateSurveyResponse] = field(default_factory=list)
    employer_surveys: list[EmployerSurveyResponse] = field(default_factory=list)
    industry_partnerships: list[IndustryPartnership] = field(default_factory=list)
    pfe_projects: list[PfeProject] = field(default_factory=list)
    alumni: list[Alumnus] = field(default_factory=list)
    home_country: str = "TN"


# ---------------------------------------------------------------------------
# Domain D - Internationalization
# ---------------------------------------------------------------------------

# Default official languages for Tunisian higher ed (Arabic + French). A
# program is "foreign-language" (INT-06) if any of its teaching languages
# falls outside this set. Override via `InstitutionInternationalInputs`.
DEFAULT_OFFICIAL_LANGUAGES: frozenset[str] = frozenset({"fr", "ar"})


@dataclass
class AcademicPartnership:
    """Formal academic agreement (MOU, convention, exchange) with another
    higher-education institution. Distinct from `IndustryPartnership` (which
    is private-sector); INT-05 only counts academic partners.
    """

    id: str
    partner_name: str
    partner_country: str | None = None
    is_active: bool = True
    agreement_type: str | None = None  # MOU | convention | exchange | erasmus | ...


@dataclass
class InstitutionInternationalInputs:
    """Everything Domain D needs for one institution and one period.

    `official_languages` defaults to {fr, ar} for Tunisia; override per
    institution if its statute differs.
    """

    institution_id: str
    institution_code: str
    period_start: date
    period_end: date
    faculty: list[FacultyMember] = field(default_factory=list)
    students: list[Student] = field(default_factory=list)
    programs: list[Program] = field(default_factory=list)
    academic_partnerships: list[AcademicPartnership] = field(default_factory=list)
    home_country: str = "TN"
    official_languages: frozenset[str] = DEFAULT_OFFICIAL_LANGUAGES


# ---------------------------------------------------------------------------
# Domain E - Finance & Resources
# ---------------------------------------------------------------------------


class BudgetCategory(StrEnum):
    """Coarse budget classification used by FIN-01..FIN-03.

    `RESEARCH` is excluded from the FIN-02 "operating expenditure" sum since
    it is funded externally (and reported separately by FIN-03/RES-06). The
    remaining categories are aggregated for cost-per-student.
    """

    OPERATIONS = "operations"
    SALARIES = "salaries"
    RESEARCH = "research"
    INFRASTRUCTURE = "infrastructure"
    OTHER = "other"


OPERATING_CATEGORIES: frozenset[BudgetCategory] = frozenset(
    {BudgetCategory.OPERATIONS, BudgetCategory.SALARIES, BudgetCategory.INFRASTRUCTURE,
     BudgetCategory.OTHER}
)


class RevenueSource(StrEnum):
    """Revenue stream classification for FIN-04 diversification index.

    Only `PUBLIC_FUNDING` (state subsidy) counts as public; everything else
    is "diversified" revenue.
    """

    PUBLIC_FUNDING = "public_funding"
    TUITION = "tuition"
    RESEARCH = "research"
    CONSULTANCY = "consultancy"
    DONATION = "donation"
    OTHER = "other"


@dataclass
class BudgetLine:
    """One line of the institution's budget for the period (TND)."""

    id: str
    category: BudgetCategory | None = None
    allocated_tnd: float | None = None
    actual_tnd: float | None = None


@dataclass
class RevenueLine:
    """One realised revenue stream in the period (TND)."""

    id: str
    source: RevenueSource | None = None
    amount_tnd: float | None = None


@dataclass
class Asset:
    """An inventory/capital asset registered to the institution (FIN-05)."""

    id: str
    name: str | None = None
    is_in_active_use: bool | None = None
    registered_at: date | None = None


@dataclass
class CompletedProject:
    """A project that completed in the period - feeds FIN-06.

    Distinct from `FundedProject` (still-running funded research). The
    repository may sometimes derive these from the same source records,
    but the lifecycles differ.
    """

    id: str
    title: str | None = None
    budget_allocated_tnd: float | None = None
    budget_actual_tnd: float | None = None
    completion_date: date | None = None


@dataclass
class Payslip:
    """One payroll-cycle payslip - feeds FIN-07."""

    id: str
    period: str | None = None  # e.g. "2026-04"
    employee_id: str | None = None
    issued_without_correction: bool | None = None


@dataclass
class InstitutionFinanceInputs:
    """Everything Domain E needs for one institution and one period.

    `funded_projects` mirrors the Domain A field so FIN-03 can compute
    external research funding from the same source of truth.
    """

    institution_id: str
    institution_code: str
    period_start: date
    period_end: date
    budget_lines: list[BudgetLine] = field(default_factory=list)
    revenue_lines: list[RevenueLine] = field(default_factory=list)
    assets: list[Asset] = field(default_factory=list)
    completed_projects: list[CompletedProject] = field(default_factory=list)
    payslips: list[Payslip] = field(default_factory=list)
    funded_projects: list[FundedProject] = field(default_factory=list)
    students: list[Student] = field(default_factory=list)
    home_country: str = "TN"


# ---------------------------------------------------------------------------
# Domain F - Human Resources
# ---------------------------------------------------------------------------

# Tolerance band for HR-01 "within +/-X% of contracted hours". A faculty
# member is considered compliant when their delivered hours fall within
# [contracted * (1 - tol), contracted * (1 + tol)].
DEFAULT_WORKLOAD_TOLERANCE: float = 0.20


@dataclass
class AdminStaff:
    """Non-teaching administrative employee. Used by HR-04 (admin/student
    ratio) and HR-06 (staff absenteeism, aggregated with faculty).
    """

    id: str
    full_name: str | None = None
    is_active: bool = True
    fte_fraction: float = 1.0
    role: str | None = None
    scheduled_workdays: int | None = None
    unexcused_absence_days: int | None = None


@dataclass
class VacancyEvent:
    """One hiring event for HR-07. `contract_signed_date is None` means
    the vacancy is still open at period end (excluded from the median).
    """

    id: str
    position_open_date: date | None = None
    contract_signed_date: date | None = None


@dataclass
class InstitutionHrInputs:
    """Everything Domain F needs for one institution and one period."""

    institution_id: str
    institution_code: str
    period_start: date
    period_end: date
    faculty: list[FacultyMember] = field(default_factory=list)
    admin_staff: list[AdminStaff] = field(default_factory=list)
    vacancy_events: list[VacancyEvent] = field(default_factory=list)
    students: list[Student] = field(default_factory=list)
    workload_tolerance: float = DEFAULT_WORKLOAD_TOLERANCE
    home_country: str = "TN"


# ---------------------------------------------------------------------------
# Domain G - Sustainability & ESG
# ---------------------------------------------------------------------------


@dataclass
class EnergyConsumption:
    """One sub-period energy consumption reading.

    `is_renewable` is per-record so a meter that switched mid-period (e.g.
    new solar array) records two rows. ESG-03 aggregates renewable kWh
    over total kWh.
    """

    id: str
    period_start: date | None = None
    period_end: date | None = None
    kwh_consumed: float | None = None
    co2e_kg: float | None = None
    is_renewable: bool | None = None


@dataclass
class WasteRecord:
    """Waste generation/recycling record (ESG-04)."""

    id: str
    record_date: date | None = None
    waste_total_kg: float | None = None
    waste_recycled_kg: float | None = None


@dataclass
class TransportSurveyResponse:
    """One green-transport survey response (ESG-05).

    `uses_sustainable_transport` covers walking/cycling/public-transit/EV;
    the survey conductor decides what counts at collection time.
    """

    respondent_id: str
    is_student: bool | None = None
    uses_sustainable_transport: bool | None = None


@dataclass
class Facility:
    """A campus facility (building, lab, common area) for ESG-06."""

    id: str
    name: str | None = None
    is_accessibility_compliant: bool | None = None


@dataclass
class InstitutionEsgInputs:
    """Everything Domain G needs for one institution and one period.

    Reuses `faculty` for ESG-07 (gender) and `faculty[*].publications` for
    ESG-08 (SDG-aligned research).
    """

    institution_id: str
    institution_code: str
    period_start: date
    period_end: date
    faculty: list[FacultyMember] = field(default_factory=list)
    students: list[Student] = field(default_factory=list)
    energy_consumption: list[EnergyConsumption] = field(default_factory=list)
    waste_records: list[WasteRecord] = field(default_factory=list)
    transport_responses: list[TransportSurveyResponse] = field(default_factory=list)
    facilities: list[Facility] = field(default_factory=list)
    home_country: str = "TN"


# ---------------------------------------------------------------------------
# Domain H - Governance & Compliance
# ---------------------------------------------------------------------------


class FrameworkScope(StrEnum):
    """Per accreditation.md s2.1: where a control's status is evaluated.

    INSTITUTION = each institution gets its own status row.
    NETWORK     = the aggregate UCAR-wide value satisfies the control;
                  per-institution rows show contribution only.
    """

    INSTITUTION = "INSTITUTION"
    NETWORK = "NETWORK"


class TestType(StrEnum):
    """Per accreditation.md s2.3."""

    AUTOMATED_KPI = "AUTOMATED_KPI"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    ATTESTATION = "ATTESTATION"


class TestPeriodScope(StrEnum):
    """How far back to look for evidence."""

    CURRENT_SEMESTER = "CURRENT_SEMESTER"
    CURRENT_YEAR = "CURRENT_YEAR"
    ROLLING_3Y = "ROLLING_3Y"


@dataclass
class ControlTest:
    """One test that verifies a control. Per accreditation.md s2.3."""

    id: str
    test_type: TestType
    name: str = ""
    is_required: bool = True
    # AUTOMATED_KPI fields
    kpi_id: str | None = None
    threshold: float | None = None  # value >= threshold => passing
    threshold_comparator: str = ">="  # one of ">=", "<=", "==", ">", "<"
    # DOCUMENT_UPLOAD fields
    required_template_codes: list[str] | None = None
    required_document_count: int = 1
    period_scope: TestPeriodScope = TestPeriodScope.CURRENT_YEAR


@dataclass
class FrameworkControl:
    """Atomic requirement within a framework. Per accreditation.md s2.2."""

    id: str
    code: str
    name: str
    weight: float = 0.0
    category: str | None = None
    description: str | None = None
    requires_external_survey: bool = False
    owner_role: str | None = None
    tests: list[ControlTest] = field(default_factory=list)


@dataclass
class Framework:
    """An external accreditation body or ranking methodology."""

    code: str  # "QS", "THE", "ARWU", "ISO21001", "MESRS"
    name: str
    version: str | None = None
    scope: FrameworkScope = FrameworkScope.INSTITUTION
    is_active: bool = True
    controls: list[FrameworkControl] = field(default_factory=list)


@dataclass
class ApprovedDocument:
    """One approved document on file - feeds DOCUMENT_UPLOAD tests."""

    document_id: str
    template_code: str
    approved_at: date | None = None
    period_year: int | None = None  # academic year tag from doc-service


@dataclass
class Attestation:
    """Submitted attestation that satisfies an ATTESTATION test."""

    test_id: str
    attested_by: str | None = None
    attestation_text: str | None = None
    attested_at: date | None = None
    is_active: bool = True  # may be withdrawn


@dataclass
class ControlWaiver:
    """Per-(institution, control) NOT_APPLICABLE marker with audit trail."""

    control_id: str
    reason: str
    waived_by: str | None = None
    waived_at: date | None = None


@dataclass
class InstitutionAccreditationInputs:
    """Everything Domain H needs to evaluate compliance for one institution.

    `kpi_values` is a precomputed lookup populated by the upstream KPI
    domains (A-G) - the accreditation evaluator never recomputes a KPI,
    it only reads. `None` means "no KPI record on file" which fails any
    AUTOMATED_KPI test.

    `approved_documents` is the institution's evidence portfolio: any
    approved document with its template_code. Period filtering happens
    inside the evaluator using `test.period_scope`.
    """

    institution_id: str
    institution_code: str
    period_start: date
    period_end: date
    frameworks: list[Framework] = field(default_factory=list)
    kpi_values: dict[str, float | None] = field(default_factory=dict)
    approved_documents: list[ApprovedDocument] = field(default_factory=list)
    attestations: list[Attestation] = field(default_factory=list)
    waivers: list[ControlWaiver] = field(default_factory=list)
    home_country: str = "TN"
