"""Accreditation compliance engine — demo implementation.

Vanta/Drata-style mapping: Frameworks → Controls → Tests → Evidence.
Approved documents auto-satisfy DOCUMENT_UPLOAD tests; KPI thresholds
auto-satisfy AUTOMATED_KPI tests. Control status re-evaluates in real time.

This module is self-contained with mock data for 4 UCAR institutions.
"""

from __future__ import annotations

import operator
import uuid
from collections import Counter
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, computed_field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestType(str, Enum):
    AUTOMATED_KPI = "AUTOMATED_KPI"
    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    ATTESTATION = "ATTESTATION"


class ControlStatusValue(str, Enum):
    PASSING = "PASSING"
    FAILING = "FAILING"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EvidenceStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------


class ControlTest(BaseModel):
    test_id: str
    test_type: TestType
    description: str
    template_id: Optional[str] = None
    kpi_id: Optional[str] = None
    kpi_threshold: Optional[float] = None
    kpi_operator: Optional[str] = None  # "gte", "lte", "gt", "lt"


class FrameworkControl(BaseModel):
    control_id: str
    framework_code: str
    clause_ref: str
    name: str
    description: str
    weight: float  # 1–5, used for gap priority
    tests: list[ControlTest]
    requires_external_survey: bool = False


class Framework(BaseModel):
    code: str
    name: str
    full_name: str
    version: str
    description: str
    category: str  # "QMS" | "EOMS" | "SUSTAINABILITY"
    controls: list[FrameworkControl]

    @computed_field
    @property
    def total_controls(self) -> int:
        return len(self.controls)


class EvidenceRecord(BaseModel):
    evidence_id: str
    control_id: str
    test_id: str
    institution_code: str
    period_year: int
    doc_template_id: Optional[str] = None
    doc_name: Optional[str] = None
    status: EvidenceStatus
    submitted_at: datetime
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None


class ControlStatusResult(BaseModel):
    control_id: str
    clause_ref: str
    name: str
    framework_code: str
    weight: float
    status: ControlStatusValue
    passing_tests: list[str]
    failing_tests: list[str]
    missing_test_ids: list[str]
    last_evaluated: datetime


class FrameworkPosture(BaseModel):
    framework_code: str
    framework_name: str
    institution_code: str
    period_year: int
    passing: int
    failing: int
    needs_evidence: int
    not_applicable: int
    total: int
    score_pct: float
    controls: list[ControlStatusResult]

    @computed_field
    @property
    def compliance_level(self) -> str:
        if self.score_pct >= 85:
            return "COMPLIANT"
        elif self.score_pct >= 60:
            return "PARTIAL"
        return "NON_COMPLIANT"


class GapItem(BaseModel):
    control_id: str
    clause_ref: str
    name: str
    weight: float
    status: ControlStatusValue
    priority_score: float  # weight * (1 - fraction_passing)
    missing_test_ids: list[str]
    suggested_actions: list[str]


# ---------------------------------------------------------------------------
# Framework seed data
# ---------------------------------------------------------------------------

_ISO9001_CONTROLS: list[FrameworkControl] = [
    FrameworkControl(
        control_id="iso9001-4.1",
        framework_code="ISO9001",
        clause_ref="4.1",
        name="Understanding the organization and its context",
        description="Determine external/internal issues relevant to purpose and strategic direction.",
        weight=3,
        tests=[
            ControlTest(
                test_id="iso9001-4.1-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Strategic context analysis document on file",
                template_id="TPLT_STRATEGIC_CONTEXT",
            )
        ],
    ),
    FrameworkControl(
        control_id="iso9001-4.2",
        framework_code="ISO9001",
        clause_ref="4.2",
        name="Interested parties",
        description="Determine relevant interested parties and their requirements.",
        weight=2,
        tests=[
            ControlTest(
                test_id="iso9001-4.2-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Stakeholder register approved",
                template_id="TPLT_STAKEHOLDER_REGISTER",
            )
        ],
    ),
    FrameworkControl(
        control_id="iso9001-5.1",
        framework_code="ISO9001",
        clause_ref="5.1",
        name="Leadership and commitment",
        description="Top management demonstrates leadership and commitment to QMS.",
        weight=4,
        tests=[
            ControlTest(
                test_id="iso9001-5.1-t1",
                test_type=TestType.ATTESTATION,
                description="Director attestation of QMS commitment",
                template_id="TPLT_LEADERSHIP_ATTESTATION",
            ),
            ControlTest(
                test_id="iso9001-5.1-t2",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Quality policy document published",
                template_id="TPLT_QUALITY_POLICY",
            ),
        ],
    ),
    FrameworkControl(
        control_id="iso9001-6.1",
        framework_code="ISO9001",
        clause_ref="6.1",
        name="Actions to address risks and opportunities",
        description="Plan actions to address identified risks and opportunities.",
        weight=4,
        tests=[
            ControlTest(
                test_id="iso9001-6.1-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Risk register with mitigation plans",
                template_id="TPLT_RISK_REGISTER",
            )
        ],
    ),
    FrameworkControl(
        control_id="iso9001-7.1",
        framework_code="ISO9001",
        clause_ref="7.1",
        name="Resources",
        description="Determine and provide necessary resources for QMS.",
        weight=3,
        tests=[
            ControlTest(
                test_id="iso9001-7.1-t1",
                test_type=TestType.AUTOMATED_KPI,
                description="Staff-to-student ratio meets minimum threshold",
                kpi_id="HR-01",
                kpi_threshold=0.05,
                kpi_operator="gte",
            ),
            ControlTest(
                test_id="iso9001-7.1-t2",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Infrastructure inventory current",
                template_id="TPLT_INFRA_INVENTORY",
            ),
        ],
    ),
    FrameworkControl(
        control_id="iso9001-7.5",
        framework_code="ISO9001",
        clause_ref="7.5",
        name="Documented information",
        description="QMS documented information is controlled and maintained.",
        weight=5,
        tests=[
            ControlTest(
                test_id="iso9001-7.5-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Document control procedure approved",
                template_id="TPLT_DOC_CONTROL_PROCEDURE",
            )
        ],
    ),
    FrameworkControl(
        control_id="iso9001-8.1",
        framework_code="ISO9001",
        clause_ref="8.1",
        name="Operational planning and control",
        description="Plan, implement and control processes for service provision.",
        weight=4,
        tests=[
            ControlTest(
                test_id="iso9001-8.1-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Operational procedures manual approved",
                template_id="TPLT_OPS_PROCEDURES",
            )
        ],
    ),
    FrameworkControl(
        control_id="iso9001-9.1",
        framework_code="ISO9001",
        clause_ref="9.1",
        name="Monitoring, measurement, analysis and evaluation",
        description="Determine what needs to be monitored and measured.",
        weight=4,
        tests=[
            ControlTest(
                test_id="iso9001-9.1-t1",
                test_type=TestType.AUTOMATED_KPI,
                description="Student success rate tracked and reported",
                kpi_id="ACA-01",
                kpi_threshold=0.65,
                kpi_operator="gte",
            ),
            ControlTest(
                test_id="iso9001-9.1-t2",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="KPI monitoring plan approved",
                template_id="TPLT_KPI_MONITORING_PLAN",
            ),
        ],
    ),
    FrameworkControl(
        control_id="iso9001-9.2",
        framework_code="ISO9001",
        clause_ref="9.2",
        name="Internal audit",
        description="Conduct internal audits at planned intervals.",
        weight=5,
        tests=[
            ControlTest(
                test_id="iso9001-9.2-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Internal audit report (last 12 months)",
                template_id="TPLT_INTERNAL_AUDIT_REPORT",
            )
        ],
    ),
    FrameworkControl(
        control_id="iso9001-10.2",
        framework_code="ISO9001",
        clause_ref="10.2",
        name="Nonconformity and corrective action",
        description="React to nonconformities and take corrective action.",
        weight=3,
        tests=[
            ControlTest(
                test_id="iso9001-10.2-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Corrective action log maintained",
                template_id="TPLT_CORRECTIVE_ACTION_LOG",
            )
        ],
    ),
]

_ISO21001_CONTROLS: list[FrameworkControl] = [
    FrameworkControl(
        control_id="iso21001-4.1",
        framework_code="ISO21001",
        clause_ref="4.1",
        name="Understanding the educational organization",
        description="Determine context factors that affect ability to achieve intended outcomes.",
        weight=3,
        tests=[
            ControlTest(
                test_id="iso21001-4.1-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="EOMS context analysis documented",
                template_id="TPLT_EOMS_CONTEXT",
            )
        ],
    ),
    FrameworkControl(
        control_id="iso21001-5.3",
        framework_code="ISO21001",
        clause_ref="5.3",
        name="Learner focus",
        description="Enhance learner satisfaction and meet learner needs.",
        weight=5,
        tests=[
            ControlTest(
                test_id="iso21001-5.3-t1",
                test_type=TestType.AUTOMATED_KPI,
                description="Student satisfaction score ≥ 3.5/5",
                kpi_id="ACA-06",
                kpi_threshold=3.5,
                kpi_operator="gte",
            ),
            ControlTest(
                test_id="iso21001-5.3-t2",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Learner feedback mechanism documented",
                template_id="TPLT_LEARNER_FEEDBACK",
            ),
        ],
    ),
    FrameworkControl(
        control_id="iso21001-6.1",
        framework_code="ISO21001",
        clause_ref="6.1",
        name="Risks and opportunities (educational)",
        description="Address risks affecting educational objectives.",
        weight=4,
        tests=[
            ControlTest(
                test_id="iso21001-6.1-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Educational risk register approved",
                template_id="TPLT_RISK_REGISTER",
            )
        ],
    ),
    FrameworkControl(
        control_id="iso21001-7.2",
        framework_code="ISO21001",
        clause_ref="7.2",
        name="Competence of educators",
        description="Ensure educator competence through training and development.",
        weight=4,
        tests=[
            ControlTest(
                test_id="iso21001-7.2-t1",
                test_type=TestType.AUTOMATED_KPI,
                description="Training hours per faculty ≥ 20h/year",
                kpi_id="HR-04",
                kpi_threshold=20,
                kpi_operator="gte",
            ),
            ControlTest(
                test_id="iso21001-7.2-t2",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Professional development plan on file",
                template_id="TPLT_PD_PLAN",
            ),
        ],
    ),
    FrameworkControl(
        control_id="iso21001-7.5",
        framework_code="ISO21001",
        clause_ref="7.5",
        name="Documented information (EOMS)",
        description="Maintain and control documented information for EOMS.",
        weight=5,
        tests=[
            ControlTest(
                test_id="iso21001-7.5-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="EOMS document control procedure",
                template_id="TPLT_DOC_CONTROL_PROCEDURE",
            )
        ],
    ),
    FrameworkControl(
        control_id="iso21001-8.3",
        framework_code="ISO21001",
        clause_ref="8.3",
        name="Design of educational products and services",
        description="Establish process for design and development of educational programs.",
        weight=4,
        tests=[
            ControlTest(
                test_id="iso21001-8.3-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Curriculum design process documented",
                template_id="TPLT_CURRICULUM_DESIGN",
            )
        ],
    ),
    FrameworkControl(
        control_id="iso21001-9.1",
        framework_code="ISO21001",
        clause_ref="9.1",
        name="Monitoring and measurement of educational outcomes",
        description="Monitor and measure educational processes and outcomes.",
        weight=5,
        tests=[
            ControlTest(
                test_id="iso21001-9.1-t1",
                test_type=TestType.AUTOMATED_KPI,
                description="Graduate employability rate ≥ 60%",
                kpi_id="EMP-01",
                kpi_threshold=0.60,
                kpi_operator="gte",
            ),
            ControlTest(
                test_id="iso21001-9.1-t2",
                test_type=TestType.AUTOMATED_KPI,
                description="Academic success rate ≥ 65%",
                kpi_id="ACA-01",
                kpi_threshold=0.65,
                kpi_operator="gte",
            ),
        ],
    ),
    FrameworkControl(
        control_id="iso21001-9.2",
        framework_code="ISO21001",
        clause_ref="9.2",
        name="Internal audit (EOMS)",
        description="Internal audits to verify EOMS conformance.",
        weight=5,
        tests=[
            ControlTest(
                test_id="iso21001-9.2-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="EOMS internal audit report",
                template_id="TPLT_INTERNAL_AUDIT_REPORT",
            )
        ],
    ),
]

_GREENMETRIC_CONTROLS: list[FrameworkControl] = [
    FrameworkControl(
        control_id="gm-setting",
        framework_code="GREENMETRIC",
        clause_ref="CAT-1",
        name="Setting and Infrastructure",
        description="Campus area, vegetation, sustainable buildings, and green space.",
        weight=3,
        tests=[
            ControlTest(
                test_id="gm-setting-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Campus sustainability report with green space data",
                template_id="TPLT_CAMPUS_SUSTAINABILITY",
            ),
            ControlTest(
                test_id="gm-setting-t2",
                test_type=TestType.AUTOMATED_KPI,
                description="Green area ratio ≥ 30% of campus",
                kpi_id="ESG-04",
                kpi_threshold=0.30,
                kpi_operator="gte",
            ),
        ],
    ),
    FrameworkControl(
        control_id="gm-energy",
        framework_code="GREENMETRIC",
        clause_ref="CAT-2",
        name="Energy and Climate Change",
        description="Energy efficiency, renewable energy, and climate change programs.",
        weight=5,
        tests=[
            ControlTest(
                test_id="gm-energy-t1",
                test_type=TestType.AUTOMATED_KPI,
                description="Renewable energy share ≥ 15%",
                kpi_id="ESG-02",
                kpi_threshold=0.15,
                kpi_operator="gte",
            ),
            ControlTest(
                test_id="gm-energy-t2",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Energy reduction action plan approved",
                template_id="TPLT_ENERGY_PLAN",
            ),
        ],
    ),
    FrameworkControl(
        control_id="gm-waste",
        framework_code="GREENMETRIC",
        clause_ref="CAT-3",
        name="Waste Management",
        description="Recycling programs, waste reduction, and hazardous waste handling.",
        weight=4,
        tests=[
            ControlTest(
                test_id="gm-waste-t1",
                test_type=TestType.AUTOMATED_KPI,
                description="Recycling rate ≥ 40%",
                kpi_id="ESG-03",
                kpi_threshold=0.40,
                kpi_operator="gte",
            ),
            ControlTest(
                test_id="gm-waste-t2",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Waste management policy document",
                template_id="TPLT_WASTE_MANAGEMENT",
            ),
        ],
    ),
    FrameworkControl(
        control_id="gm-water",
        framework_code="GREENMETRIC",
        clause_ref="CAT-4",
        name="Water Conservation",
        description="Water usage monitoring and conservation programs.",
        weight=4,
        tests=[
            ControlTest(
                test_id="gm-water-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Water conservation program documented",
                template_id="TPLT_WATER_CONSERVATION",
            )
        ],
    ),
    FrameworkControl(
        control_id="gm-transport",
        framework_code="GREENMETRIC",
        clause_ref="CAT-5",
        name="Transportation",
        description="Green transportation policy and sustainable mobility programs.",
        weight=3,
        tests=[
            ControlTest(
                test_id="gm-transport-t1",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Green transportation policy approved",
                template_id="TPLT_TRANSPORT_POLICY",
            )
        ],
    ),
    FrameworkControl(
        control_id="gm-education",
        framework_code="GREENMETRIC",
        clause_ref="CAT-6",
        name="Education and Research",
        description="Sustainability courses, research publications, and community engagement.",
        weight=5,
        tests=[
            ControlTest(
                test_id="gm-education-t1",
                test_type=TestType.AUTOMATED_KPI,
                description="Sustainability research publications ≥ 2/year",
                kpi_id="RES-01",
                kpi_threshold=2,
                kpi_operator="gte",
            ),
            ControlTest(
                test_id="gm-education-t2",
                test_type=TestType.DOCUMENT_UPLOAD,
                description="Sustainability education program documented",
                template_id="TPLT_SUSTAINABILITY_PROGRAM",
            ),
        ],
    ),
]

FRAMEWORKS: dict[str, Framework] = {
    "ISO9001": Framework(
        code="ISO9001",
        name="ISO 9001",
        full_name="ISO 9001:2015 Quality Management System",
        version="2015",
        description="International standard for quality management systems, ensuring consistent quality of products and services.",
        category="QMS",
        controls=_ISO9001_CONTROLS,
    ),
    "ISO21001": Framework(
        code="ISO21001",
        name="ISO 21001",
        full_name="ISO 21001:2018 Educational Organizations Management System",
        version="2018",
        description="Management system standard for educational organizations focused on enhancing learner satisfaction.",
        category="EOMS",
        controls=_ISO21001_CONTROLS,
    ),
    "GREENMETRIC": Framework(
        code="GREENMETRIC",
        name="UI GreenMetric",
        full_name="UI GreenMetric World University Rankings",
        version="2024",
        description="Sustainability ranking evaluating campus green practices across 6 categories.",
        category="SUSTAINABILITY",
        controls=_GREENMETRIC_CONTROLS,
    ),
}

# ---------------------------------------------------------------------------
# Mock evidence store (in-memory for demo)
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 4, 26, 10, 0, 0)
_PERIOD = 2026

# fmt: off
_MOCK_EVIDENCE: list[EvidenceRecord] = [
    # --- INSAT (strong ISO9001) ---
    EvidenceRecord(evidence_id="ev-001", control_id="iso9001-4.1", test_id="iso9001-4.1-t1", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_STRATEGIC_CONTEXT", doc_name="INSAT Strategic Context 2026.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-002", control_id="iso9001-4.2", test_id="iso9001-4.2-t1", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_STAKEHOLDER_REGISTER", doc_name="INSAT Stakeholder Register.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-003", control_id="iso9001-5.1", test_id="iso9001-5.1-t1", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_LEADERSHIP_ATTESTATION", doc_name="Director Attestation Q1 2026.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-004", control_id="iso9001-5.1", test_id="iso9001-5.1-t2", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_QUALITY_POLICY", doc_name="INSAT Quality Policy 2026.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-005", control_id="iso9001-6.1", test_id="iso9001-6.1-t1", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_RISK_REGISTER", doc_name="INSAT Risk Register 2026.xlsx", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-006", control_id="iso9001-7.5", test_id="iso9001-7.5-t1", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_DOC_CONTROL_PROCEDURE", doc_name="Doc Control Procedure v2.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-007", control_id="iso9001-8.1", test_id="iso9001-8.1-t1", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_OPS_PROCEDURES", doc_name="INSAT Ops Procedures Manual.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-008", control_id="iso9001-9.2", test_id="iso9001-9.2-t1", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_INTERNAL_AUDIT_REPORT", doc_name="Internal Audit Report 2025.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    # Pending (not yet approved)
    EvidenceRecord(evidence_id="ev-009", control_id="iso9001-9.1", test_id="iso9001-9.1-t2", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_KPI_MONITORING_PLAN", doc_name="KPI Monitoring Plan Draft.pdf", status=EvidenceStatus.PENDING, submitted_at=_NOW),
    # --- INSAT ISO21001 ---
    EvidenceRecord(evidence_id="ev-020", control_id="iso21001-4.1", test_id="iso21001-4.1-t1", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_EOMS_CONTEXT", doc_name="INSAT EOMS Context 2026.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-021", control_id="iso21001-7.5", test_id="iso21001-7.5-t1", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_DOC_CONTROL_PROCEDURE", doc_name="EOMS Doc Control Procedure.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-022", control_id="iso21001-8.3", test_id="iso21001-8.3-t1", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_CURRICULUM_DESIGN", doc_name="Curriculum Design Process INSAT.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-023", control_id="iso21001-9.2", test_id="iso21001-9.2-t1", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_INTERNAL_AUDIT_REPORT", doc_name="EOMS Internal Audit 2025.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    # --- INSAT GreenMetric ---
    EvidenceRecord(evidence_id="ev-040", control_id="gm-setting", test_id="gm-setting-t1", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_CAMPUS_SUSTAINABILITY", doc_name="INSAT Campus Report 2025.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-041", control_id="gm-energy", test_id="gm-energy-t2", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_ENERGY_PLAN", doc_name="INSAT Energy Plan 2026.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-042", control_id="gm-waste", test_id="gm-waste-t2", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_WASTE_MANAGEMENT", doc_name="Waste Management Policy.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-043", control_id="gm-education", test_id="gm-education-t2", institution_code="INSAT", period_year=_PERIOD, doc_template_id="TPLT_SUSTAINABILITY_PROGRAM", doc_name="Sustainability Education Program.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),

    # --- ENIT (mid tier) ---
    EvidenceRecord(evidence_id="ev-100", control_id="iso9001-5.1", test_id="iso9001-5.1-t1", institution_code="ENIT", period_year=_PERIOD, doc_template_id="TPLT_LEADERSHIP_ATTESTATION", doc_name="ENIT Director Attestation.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-101", control_id="iso9001-5.1", test_id="iso9001-5.1-t2", institution_code="ENIT", period_year=_PERIOD, doc_template_id="TPLT_QUALITY_POLICY", doc_name="ENIT Quality Policy.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-102", control_id="iso9001-7.5", test_id="iso9001-7.5-t1", institution_code="ENIT", period_year=_PERIOD, doc_template_id="TPLT_DOC_CONTROL_PROCEDURE", doc_name="ENIT Doc Control v1.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-103", control_id="iso9001-9.2", test_id="iso9001-9.2-t1", institution_code="ENIT", period_year=_PERIOD, doc_template_id="TPLT_INTERNAL_AUDIT_REPORT", doc_name="ENIT Audit Report 2025.pdf", status=EvidenceStatus.PENDING, submitted_at=_NOW),
    EvidenceRecord(evidence_id="ev-120", control_id="iso21001-7.5", test_id="iso21001-7.5-t1", institution_code="ENIT", period_year=_PERIOD, doc_template_id="TPLT_DOC_CONTROL_PROCEDURE", doc_name="ENIT EOMS Doc Control.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-140", control_id="gm-energy", test_id="gm-energy-t2", institution_code="ENIT", period_year=_PERIOD, doc_template_id="TPLT_ENERGY_PLAN", doc_name="ENIT Energy Action Plan.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),

    # --- ENSI (early stage) ---
    EvidenceRecord(evidence_id="ev-200", control_id="iso9001-5.1", test_id="iso9001-5.1-t2", institution_code="ENSI", period_year=_PERIOD, doc_template_id="TPLT_QUALITY_POLICY", doc_name="ENSI Quality Policy Draft.pdf", status=EvidenceStatus.PENDING, submitted_at=_NOW),
    EvidenceRecord(evidence_id="ev-201", control_id="iso9001-7.5", test_id="iso9001-7.5-t1", institution_code="ENSI", period_year=_PERIOD, doc_template_id="TPLT_DOC_CONTROL_PROCEDURE", doc_name="ENSI Doc Control.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-240", control_id="gm-waste", test_id="gm-waste-t2", institution_code="ENSI", period_year=_PERIOD, doc_template_id="TPLT_WASTE_MANAGEMENT", doc_name="ENSI Waste Policy.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),

    # --- ISET (most advanced) ---
    EvidenceRecord(evidence_id="ev-300", control_id="iso9001-4.1", test_id="iso9001-4.1-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_STRATEGIC_CONTEXT", doc_name="ISET Strategic Context.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-301", control_id="iso9001-4.2", test_id="iso9001-4.2-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_STAKEHOLDER_REGISTER", doc_name="ISET Stakeholders 2026.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-302", control_id="iso9001-5.1", test_id="iso9001-5.1-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_LEADERSHIP_ATTESTATION", doc_name="ISET Director Attestation.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-303", control_id="iso9001-5.1", test_id="iso9001-5.1-t2", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_QUALITY_POLICY", doc_name="ISET Quality Policy 2026.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-304", control_id="iso9001-6.1", test_id="iso9001-6.1-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_RISK_REGISTER", doc_name="ISET Risk Register.xlsx", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-305", control_id="iso9001-7.1", test_id="iso9001-7.1-t2", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_INFRA_INVENTORY", doc_name="ISET Infra Inventory 2026.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-306", control_id="iso9001-7.5", test_id="iso9001-7.5-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_DOC_CONTROL_PROCEDURE", doc_name="ISET Doc Control Procedure.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-307", control_id="iso9001-8.1", test_id="iso9001-8.1-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_OPS_PROCEDURES", doc_name="ISET Ops Manual 2026.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-308", control_id="iso9001-9.1", test_id="iso9001-9.1-t2", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_KPI_MONITORING_PLAN", doc_name="ISET KPI Plan 2026.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-309", control_id="iso9001-9.2", test_id="iso9001-9.2-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_INTERNAL_AUDIT_REPORT", doc_name="ISET Internal Audit 2025.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-310", control_id="iso9001-10.2", test_id="iso9001-10.2-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_CORRECTIVE_ACTION_LOG", doc_name="ISET Corrective Actions 2026.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    # ISO21001 ISET
    EvidenceRecord(evidence_id="ev-320", control_id="iso21001-4.1", test_id="iso21001-4.1-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_EOMS_CONTEXT", doc_name="ISET EOMS Context.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-321", control_id="iso21001-5.3", test_id="iso21001-5.3-t2", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_LEARNER_FEEDBACK", doc_name="ISET Learner Feedback Process.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-322", control_id="iso21001-6.1", test_id="iso21001-6.1-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_RISK_REGISTER", doc_name="ISET Educational Risk Register.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-323", control_id="iso21001-7.2", test_id="iso21001-7.2-t2", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_PD_PLAN", doc_name="ISET Faculty PD Plan 2026.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-324", control_id="iso21001-7.5", test_id="iso21001-7.5-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_DOC_CONTROL_PROCEDURE", doc_name="ISET EOMS Doc Control.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-325", control_id="iso21001-8.3", test_id="iso21001-8.3-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_CURRICULUM_DESIGN", doc_name="ISET Curriculum Design.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-326", control_id="iso21001-9.2", test_id="iso21001-9.2-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_INTERNAL_AUDIT_REPORT", doc_name="ISET EOMS Audit 2025.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    # GreenMetric ISET
    EvidenceRecord(evidence_id="ev-340", control_id="gm-setting", test_id="gm-setting-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_CAMPUS_SUSTAINABILITY", doc_name="ISET Campus Report 2025.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-341", control_id="gm-energy", test_id="gm-energy-t2", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_ENERGY_PLAN", doc_name="ISET Energy Plan 2026.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-342", control_id="gm-waste", test_id="gm-waste-t2", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_WASTE_MANAGEMENT", doc_name="ISET Waste Management.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-343", control_id="gm-water", test_id="gm-water-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_WATER_CONSERVATION", doc_name="ISET Water Conservation.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-344", control_id="gm-transport", test_id="gm-transport-t1", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_TRANSPORT_POLICY", doc_name="ISET Green Transport Policy.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
    EvidenceRecord(evidence_id="ev-345", control_id="gm-education", test_id="gm-education-t2", institution_code="ISET", period_year=_PERIOD, doc_template_id="TPLT_SUSTAINABILITY_PROGRAM", doc_name="ISET Sustainability Program.pdf", status=EvidenceStatus.APPROVED, submitted_at=_NOW, approved_at=_NOW),
]
# fmt: on

# Mutable store keyed by evidence_id for demo mutations
_evidence_store: dict[str, EvidenceRecord] = {ev.evidence_id: ev for ev in _MOCK_EVIDENCE}

# Mock KPI values per institution (simulating computed KPI results)
_MOCK_KPI_VALUES: dict[str, dict[str, float]] = {
    "INSAT": {"ACA-01": 0.78, "HR-01": 0.08, "RES-01": 12, "ESG-02": 0.18, "ESG-03": 0.45, "ESG-04": 0.35, "HR-04": 28},
    "ENIT": {"ACA-01": 0.71, "HR-01": 0.06, "RES-01": 7, "ESG-02": 0.09, "ESG-03": 0.28, "ESG-04": 0.22, "HR-04": 15},
    "ENSI": {"ACA-01": 0.65, "HR-01": 0.05, "RES-01": 4, "ESG-02": 0.05, "ESG-03": 0.20, "ESG-04": 0.18, "HR-04": 10},
    "ISET": {"ACA-01": 0.82, "HR-01": 0.09, "RES-01": 18, "ESG-02": 0.22, "ESG-03": 0.55, "ESG-04": 0.40, "HR-04": 35},
}

INSTITUTIONS = ["INSAT", "ENIT", "ENSI", "ISET"]

# ---------------------------------------------------------------------------
# Evaluation engine
# ---------------------------------------------------------------------------

_KPI_OPS = {"gte": operator.ge, "lte": operator.le, "gt": operator.gt, "lt": operator.lt}


def _check_kpi_test(test: ControlTest, institution_code: str) -> bool:
    if test.kpi_id is None or test.kpi_threshold is None:
        return False
    value = _MOCK_KPI_VALUES.get(institution_code, {}).get(test.kpi_id)
    if value is None:
        return False
    cmp = _KPI_OPS.get(test.kpi_operator or "gte", operator.ge)
    return cmp(value, test.kpi_threshold)


def evaluate_control(
    control: FrameworkControl,
    institution_code: str,
    period_year: int,
) -> ControlStatusResult:
    # Single pass: bucket evidence records by test_id for O(1) lookup below
    ev_by_test: dict[str, list[EvidenceRecord]] = {}
    for ev in _evidence_store.values():
        if (
            ev.institution_code == institution_code
            and ev.control_id == control.control_id
            and ev.period_year == period_year
        ):
            ev_by_test.setdefault(ev.test_id, []).append(ev)

    passing: list[str] = []
    failing: list[str] = []
    missing: list[str] = []

    for test in control.tests:
        if test.test_type == TestType.AUTOMATED_KPI:
            if _check_kpi_test(test, institution_code):
                passing.append(test.test_id)
            else:
                failing.append(test.test_id)
        else:
            test_evidence = ev_by_test.get(test.test_id, [])
            if any(e.status == EvidenceStatus.APPROVED for e in test_evidence):
                passing.append(test.test_id)
            elif test_evidence:
                failing.append(test.test_id)
            else:
                missing.append(test.test_id)

    if not passing and not failing and missing and control.requires_external_survey:
        status = ControlStatusValue.NOT_APPLICABLE
    elif failing:
        status = ControlStatusValue.FAILING
    elif missing:
        status = ControlStatusValue.NEEDS_EVIDENCE
    else:
        status = ControlStatusValue.PASSING

    return ControlStatusResult(
        control_id=control.control_id,
        clause_ref=control.clause_ref,
        name=control.name,
        framework_code=control.framework_code,
        weight=control.weight,
        status=status,
        passing_tests=passing,
        failing_tests=failing,
        missing_test_ids=missing,
        last_evaluated=datetime.utcnow(),
    )


def get_framework_posture(
    framework_code: str,
    institution_code: str,
    period_year: int = _PERIOD,
) -> FrameworkPosture:
    fw = FRAMEWORKS[framework_code]
    control_results = [evaluate_control(c, institution_code, period_year) for c in fw.controls]

    counts = Counter(r.status for r in control_results)
    passing = counts[ControlStatusValue.PASSING]
    failing = counts[ControlStatusValue.FAILING]
    needs_ev = counts[ControlStatusValue.NEEDS_EVIDENCE]
    not_app = counts[ControlStatusValue.NOT_APPLICABLE]
    total = len(control_results)
    score_pct = round(passing / (total - not_app or 1) * 100, 1)

    return FrameworkPosture(
        framework_code=framework_code,
        framework_name=fw.name,
        institution_code=institution_code,
        period_year=period_year,
        passing=passing,
        failing=failing,
        needs_evidence=needs_ev,
        not_applicable=not_app,
        total=total,
        score_pct=score_pct,
        controls=control_results,
    )


def get_evidence_portfolio(
    framework_code: str,
    institution_code: str,
    period_year: int = _PERIOD,
) -> list[EvidenceRecord]:
    fw = FRAMEWORKS[framework_code]
    control_ids = {c.control_id for c in fw.controls}
    return [
        ev
        for ev in _evidence_store.values()
        if ev.institution_code == institution_code
        and ev.control_id in control_ids
        and ev.period_year == period_year
    ]


def get_gap_analysis(
    framework_code: str,
    institution_code: str,
    period_year: int = _PERIOD,
) -> list[GapItem]:
    fw = FRAMEWORKS[framework_code]
    gaps: list[GapItem] = []

    for control in fw.controls:
        result = evaluate_control(control, institution_code, period_year)
        if result.status == ControlStatusValue.PASSING:
            continue

        passing_fraction = len(result.passing_tests) / max(len(control.tests), 1)
        priority = round(control.weight * (1 - passing_fraction), 2)

        actions: list[str] = []
        for test in control.tests:
            if test.test_id in result.missing_test_ids or test.test_id in result.failing_tests:
                if test.test_type == TestType.DOCUMENT_UPLOAD and test.template_id:
                    actions.append(f"Upload '{test.template_id}': {test.description}")
                elif test.test_type == TestType.AUTOMATED_KPI and test.kpi_id:
                    kpi_val = _MOCK_KPI_VALUES.get(institution_code, {}).get(test.kpi_id)
                    current = f"{kpi_val:.2f}" if kpi_val is not None else "N/A"
                    actions.append(
                        f"Improve {test.kpi_id} to {test.kpi_operator} {test.kpi_threshold} (current: {current})"
                    )
                else:
                    actions.append(f"Complete required attestation: {test.description}")

        gaps.append(
            GapItem(
                control_id=control.control_id,
                clause_ref=control.clause_ref,
                name=control.name,
                weight=control.weight,
                status=result.status,
                priority_score=priority,
                missing_test_ids=result.missing_test_ids + result.failing_tests,
                suggested_actions=actions,
            )
        )

    return sorted(gaps, key=lambda g: g.priority_score, reverse=True)


def approve_evidence(
    control_id: str,
    test_id: str,
    institution_code: str,
    period_year: int,
    doc_name: str = "Uploaded Document",
    template_id: Optional[str] = None,
) -> EvidenceRecord:
    """Create and immediately approve a new evidence record (demo mutation)."""
    evidence_id = f"ev-demo-{uuid.uuid4().hex[:8]}"
    record = EvidenceRecord(
        evidence_id=evidence_id,
        control_id=control_id,
        test_id=test_id,
        institution_code=institution_code,
        period_year=period_year,
        doc_template_id=template_id,
        doc_name=doc_name,
        status=EvidenceStatus.APPROVED,
        submitted_at=datetime.utcnow(),
        approved_at=datetime.utcnow(),
        notes="Auto-approved via demo endpoint",
    )
    _evidence_store[evidence_id] = record
    return record


def get_network_summary(period_year: int = _PERIOD) -> list[dict]:
    """Aggregate posture across all institutions and frameworks."""
    rows = []
    for inst in INSTITUTIONS:
        inst_row: dict = {"institution_code": inst, "frameworks": {}}
        for fw_code in FRAMEWORKS:
            posture = get_framework_posture(fw_code, inst, period_year)
            inst_row["frameworks"][fw_code] = {
                "score_pct": posture.score_pct,
                "compliance_level": posture.compliance_level,
                "passing": posture.passing,
                "total": posture.total,
            }
        rows.append(inst_row)
    return rows
