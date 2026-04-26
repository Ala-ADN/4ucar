"""KPI domain layer - pure-function calculators decoupled from persistence.

Public API:
    Domain A (Research & Citations):
        InstitutionResearchInputs, compute_research_domain,
        compute_research_for_network
    Domain B (Academic Quality & Teaching):
        InstitutionAcademicInputs, Student, StudentStatus, Module, Program,
        compute_academic_domain, compute_academic_for_network
    Domain C (Employability & Industry Relations):
        InstitutionEmploymentInputs, GraduateSurveyResponse,
        EmployerSurveyResponse, IndustryPartnership, PfeProject, Alumnus,
        compute_employment_domain, compute_employment_for_network
    Domain D (Internationalization):
        InstitutionInternationalInputs, AcademicPartnership,
        compute_international_domain, compute_international_for_network
    Domain E (Finance & Resources):
        InstitutionFinanceInputs, BudgetLine, BudgetCategory, RevenueLine,
        RevenueSource, Asset, CompletedProject, Payslip,
        compute_finance_domain, compute_finance_for_network
    Domain F (Human Resources):
        InstitutionHrInputs, AdminStaff, VacancyEvent,
        compute_hr_domain, compute_hr_for_network
    Domain G (Sustainability & ESG):
        InstitutionEsgInputs, EnergyConsumption, WasteRecord,
        TransportSurveyResponse, Facility,
        compute_esg_domain, compute_esg_for_network
    Domain H (Accreditation & Compliance) - qualitative, returns ControlEvaluation:
        InstitutionAccreditationInputs, Framework, FrameworkControl, ControlTest,
        ApprovedDocument, Attestation, ControlWaiver, FrameworkScope, TestType,
        TestPeriodScope, ControlStatus, ControlEvaluation,
        compute_accreditation, compute_accreditation_for_network,
        framework_completion_score, gap_analysis
    Shared:
        FacultyMember, Publication, KpiResult
"""

from .accreditation import (
    framework_completion_score,
    gap_analysis,
)
from .computation import (
    compute_academic_domain,
    compute_academic_for_network,
    compute_accreditation,
    compute_accreditation_for_network,
    compute_employment_domain,
    compute_employment_for_network,
    compute_esg_domain,
    compute_esg_for_network,
    compute_finance_domain,
    compute_finance_for_network,
    compute_hr_domain,
    compute_hr_for_network,
    compute_international_domain,
    compute_international_for_network,
    compute_research_domain,
    compute_research_for_network,
)
from .inputs import (
    AcademicPartnership,
    AdminStaff,
    Alumnus,
    ApprovedDocument,
    Asset,
    Attestation,
    BudgetCategory,
    BudgetLine,
    CompletedProject,
    ConsultancyContract,
    ControlTest,
    ControlWaiver,
    DoctoralStudent,
    EmployerSurveyResponse,
    EnergyConsumption,
    Facility,
    FacultyMember,
    Framework,
    FrameworkControl,
    FrameworkScope,
    FundedProject,
    GraduateSurveyResponse,
    IndustryPartnership,
    InstitutionAcademicInputs,
    InstitutionAccreditationInputs,
    InstitutionEmploymentInputs,
    InstitutionEsgInputs,
    InstitutionFinanceInputs,
    InstitutionHrInputs,
    InstitutionInternationalInputs,
    InstitutionResearchInputs,
    Module,
    Payslip,
    PfeProject,
    Program,
    Publication,
    RevenueLine,
    RevenueSource,
    Student,
    StudentStatus,
    TestPeriodScope,
    TestType,
    TransportSurveyResponse,
    VacancyEvent,
    WasteRecord,
)
from .result import ControlEvaluation, ControlStatus, KpiResult

__all__ = [
    # Domain A inputs
    "ConsultancyContract",
    "DoctoralStudent",
    "FundedProject",
    "InstitutionResearchInputs",
    "Publication",
    # Domain B inputs
    "InstitutionAcademicInputs",
    "Module",
    "Program",
    "Student",
    "StudentStatus",
    # Domain C inputs
    "Alumnus",
    "EmployerSurveyResponse",
    "GraduateSurveyResponse",
    "IndustryPartnership",
    "InstitutionEmploymentInputs",
    "PfeProject",
    # Domain D inputs
    "AcademicPartnership",
    "InstitutionInternationalInputs",
    # Domain E inputs
    "Asset",
    "BudgetCategory",
    "BudgetLine",
    "CompletedProject",
    "InstitutionFinanceInputs",
    "Payslip",
    "RevenueLine",
    "RevenueSource",
    # Domain F inputs
    "AdminStaff",
    "InstitutionHrInputs",
    "VacancyEvent",
    # Domain G inputs
    "EnergyConsumption",
    "Facility",
    "InstitutionEsgInputs",
    "TransportSurveyResponse",
    "WasteRecord",
    # Domain H (accreditation) inputs + result
    "ApprovedDocument",
    "Attestation",
    "ControlEvaluation",
    "ControlStatus",
    "ControlTest",
    "ControlWaiver",
    "Framework",
    "FrameworkControl",
    "FrameworkScope",
    "InstitutionAccreditationInputs",
    "TestPeriodScope",
    "TestType",
    # Shared
    "FacultyMember",
    "KpiResult",
    # Dispatchers
    "compute_research_domain",
    "compute_research_for_network",
    "compute_academic_domain",
    "compute_academic_for_network",
    "compute_employment_domain",
    "compute_employment_for_network",
    "compute_international_domain",
    "compute_international_for_network",
    "compute_finance_domain",
    "compute_finance_for_network",
    "compute_hr_domain",
    "compute_hr_for_network",
    "compute_esg_domain",
    "compute_esg_for_network",
    "compute_accreditation",
    "compute_accreditation_for_network",
    # Accreditation aggregations
    "framework_completion_score",
    "gap_analysis",
]
