"""Catalog of accreditation frameworks evaluated by Domain H.

Frameworks are static reference data — controls and tests change rarely
and only through deliberate review. They are expressed as typed
`Framework` / `FrameworkControl` / `ControlTest` instances so the engine
in `.accreditation` can evaluate them against `InstitutionAccreditationInputs`
without any extra adapter layer.

Three frameworks are seeded:

  * **ISO 9001:2015** — generic Quality Management System (10 controls)
  * **ISO 21001:2018** — Educational Organizations Management System (8)
  * **UI GreenMetric**  — sustainability ranking (6 categories)

Every AUTOMATED_KPI test references a real KPI id from Domains A–G; the
engine reads `inputs.kpi_values[kpi_id]` to satisfy them. DOCUMENT_UPLOAD
tests reference `template_code`s expected to land in `approved_documents`,
and ATTESTATION tests are matched by `test.id` against `inputs.attestations`.
"""

from __future__ import annotations

from .inputs import (
    ControlTest,
    Framework,
    FrameworkControl,
    FrameworkScope,
    TestPeriodScope,
    TestType,
)

# Operator translation: the catalog reads naturally as "gte 0.30" but the
# engine expects symbolic comparators. Centralised so a future framework
# author can keep using the readable form.
_OP = {"gte": ">=", "lte": "<=", "gt": ">", "lt": "<", "eq": "=="}


def _kpi(
    test_id: str,
    description: str,
    kpi_id: str,
    threshold: float,
    op: str = "gte",
    *,
    period_scope: TestPeriodScope = TestPeriodScope.CURRENT_YEAR,
) -> ControlTest:
    return ControlTest(
        id=test_id,
        test_type=TestType.AUTOMATED_KPI,
        name=description,
        kpi_id=kpi_id,
        threshold=threshold,
        threshold_comparator=_OP[op],
        period_scope=period_scope,
    )


def _doc(
    test_id: str,
    description: str,
    template_code: str,
    *,
    required_count: int = 1,
    period_scope: TestPeriodScope = TestPeriodScope.CURRENT_YEAR,
) -> ControlTest:
    return ControlTest(
        id=test_id,
        test_type=TestType.DOCUMENT_UPLOAD,
        name=description,
        required_template_codes=[template_code],
        required_document_count=required_count,
        period_scope=period_scope,
    )


def _attestation(test_id: str, description: str) -> ControlTest:
    return ControlTest(
        id=test_id,
        test_type=TestType.ATTESTATION,
        name=description,
    )


def _control(
    control_id: str,
    clause: str,
    name: str,
    description: str,
    weight: float,
    tests: list[ControlTest],
    *,
    requires_external_survey: bool = False,
) -> FrameworkControl:
    """Wrap (control_id, clause, ...) as a typed control.

    `control_id` is the unique identifier the engine and waivers use.
    `clause` is the human-readable clause reference (e.g. "9.2") that the
    UI surfaces as `control_code` in the `ControlEvaluation` output.
    """
    return FrameworkControl(
        id=control_id,
        code=clause,
        name=name,
        description=description,
        weight=weight,
        tests=tests,
        requires_external_survey=requires_external_survey,
    )


# ---------------------------------------------------------------------------
# ISO 9001:2015 — Quality Management System
# ---------------------------------------------------------------------------

_ISO9001_CONTROLS: list[FrameworkControl] = [
    _control(
        "iso9001-4.1",
        "4.1",
        "Understanding the organization and its context",
        "Determine external/internal issues relevant to purpose and strategic direction.",
        weight=3,
        tests=[
            _doc("iso9001-4.1-t1", "Strategic context analysis on file", "TPLT_STRATEGIC_CONTEXT"),
        ],
    ),
    _control(
        "iso9001-4.2",
        "4.2",
        "Interested parties",
        "Determine relevant interested parties and their requirements.",
        weight=2,
        tests=[
            _doc("iso9001-4.2-t1", "Stakeholder register approved", "TPLT_STAKEHOLDER_REGISTER"),
        ],
    ),
    _control(
        "iso9001-5.1",
        "5.1",
        "Leadership and commitment",
        "Top management demonstrates leadership and commitment to QMS.",
        weight=4,
        tests=[
            _attestation("iso9001-5.1-t1", "Director attestation of QMS commitment"),
            _doc("iso9001-5.1-t2", "Quality policy document published", "TPLT_QUALITY_POLICY"),
        ],
    ),
    _control(
        "iso9001-6.1",
        "6.1",
        "Actions to address risks and opportunities",
        "Plan actions to address identified risks and opportunities.",
        weight=4,
        tests=[
            _doc("iso9001-6.1-t1", "Risk register with mitigation plans", "TPLT_RISK_REGISTER"),
        ],
    ),
    _control(
        "iso9001-7.1",
        "7.1",
        "Resources",
        "Determine and provide necessary resources for QMS.",
        weight=3,
        tests=[
            _kpi(
                "iso9001-7.1-t1",
                "Staff-to-student ratio at minimum threshold",
                "HR-01",
                0.05,
            ),
            _doc("iso9001-7.1-t2", "Infrastructure inventory current", "TPLT_INFRA_INVENTORY"),
        ],
    ),
    _control(
        "iso9001-7.5",
        "7.5",
        "Documented information",
        "QMS documented information is controlled and maintained.",
        weight=5,
        tests=[
            _doc(
                "iso9001-7.5-t1",
                "Document control procedure approved",
                "TPLT_DOC_CONTROL_PROCEDURE",
            ),
        ],
    ),
    _control(
        "iso9001-8.1",
        "8.1",
        "Operational planning and control",
        "Plan, implement, and control processes for service provision.",
        weight=4,
        tests=[
            _doc(
                "iso9001-8.1-t1",
                "Operational procedures manual approved",
                "TPLT_OPS_PROCEDURES",
            ),
        ],
    ),
    _control(
        "iso9001-9.1",
        "9.1",
        "Monitoring, measurement, analysis and evaluation",
        "Determine what needs to be monitored and measured.",
        weight=4,
        tests=[
            _kpi(
                "iso9001-9.1-t1",
                "Student academic success rate ≥ 65%",
                "ACA-01",
                0.65,
            ),
            _doc("iso9001-9.1-t2", "KPI monitoring plan approved", "TPLT_KPI_MONITORING_PLAN"),
        ],
    ),
    _control(
        "iso9001-9.2",
        "9.2",
        "Internal audit",
        "Conduct internal audits at planned intervals.",
        weight=5,
        tests=[
            _doc(
                "iso9001-9.2-t1",
                "Internal audit report (last 12 months)",
                "TPLT_INTERNAL_AUDIT_REPORT",
            ),
        ],
    ),
    _control(
        "iso9001-10.2",
        "10.2",
        "Nonconformity and corrective action",
        "React to nonconformities and take corrective action.",
        weight=3,
        tests=[
            _doc(
                "iso9001-10.2-t1",
                "Corrective action log maintained",
                "TPLT_CORRECTIVE_ACTION_LOG",
            ),
        ],
    ),
]

# ---------------------------------------------------------------------------
# ISO 21001:2018 — Educational Organizations Management System
# ---------------------------------------------------------------------------

_ISO21001_CONTROLS: list[FrameworkControl] = [
    _control(
        "iso21001-4.1",
        "4.1",
        "Understanding the educational organization",
        "Determine context factors that affect ability to achieve intended outcomes.",
        weight=3,
        tests=[
            _doc("iso21001-4.1-t1", "EOMS context analysis documented", "TPLT_EOMS_CONTEXT"),
        ],
    ),
    _control(
        "iso21001-5.3",
        "5.3",
        "Learner focus",
        "Enhance learner satisfaction and meet learner needs.",
        weight=5,
        requires_external_survey=True,
        tests=[
            _kpi(
                "iso21001-5.3-t1",
                "Student satisfaction score ≥ 3.5/5",
                "ACA-06",
                3.5,
            ),
            _doc("iso21001-5.3-t2", "Learner feedback mechanism documented", "TPLT_LEARNER_FEEDBACK"),
        ],
    ),
    _control(
        "iso21001-6.1",
        "6.1",
        "Risks and opportunities (educational)",
        "Address risks affecting educational objectives.",
        weight=4,
        tests=[
            _doc("iso21001-6.1-t1", "Educational risk register approved", "TPLT_RISK_REGISTER"),
        ],
    ),
    _control(
        "iso21001-7.2",
        "7.2",
        "Competence of educators",
        "Ensure educator competence through training and development.",
        weight=4,
        tests=[
            _kpi(
                "iso21001-7.2-t1",
                "Training hours per faculty ≥ 20h/year",
                "HR-04",
                20,
            ),
            _doc("iso21001-7.2-t2", "Professional development plan on file", "TPLT_PD_PLAN"),
        ],
    ),
    _control(
        "iso21001-7.5",
        "7.5",
        "Documented information (EOMS)",
        "Maintain and control documented information for EOMS.",
        weight=5,
        tests=[
            _doc(
                "iso21001-7.5-t1",
                "EOMS document control procedure",
                "TPLT_DOC_CONTROL_PROCEDURE",
            ),
        ],
    ),
    _control(
        "iso21001-8.3",
        "8.3",
        "Design of educational products and services",
        "Establish process for design and development of educational programs.",
        weight=4,
        tests=[
            _doc("iso21001-8.3-t1", "Curriculum design process documented", "TPLT_CURRICULUM_DESIGN"),
        ],
    ),
    _control(
        "iso21001-9.1",
        "9.1",
        "Monitoring and measurement of educational outcomes",
        "Monitor and measure educational processes and outcomes.",
        weight=5,
        tests=[
            _kpi(
                "iso21001-9.1-t1",
                "Graduate employability rate ≥ 60%",
                "EMP-01",
                0.60,
            ),
            _kpi(
                "iso21001-9.1-t2",
                "Academic success rate ≥ 65%",
                "ACA-01",
                0.65,
            ),
        ],
    ),
    _control(
        "iso21001-9.2",
        "9.2",
        "Internal audit (EOMS)",
        "Internal audits to verify EOMS conformance.",
        weight=5,
        tests=[
            _doc("iso21001-9.2-t1", "EOMS internal audit report", "TPLT_INTERNAL_AUDIT_REPORT"),
        ],
    ),
]

# ---------------------------------------------------------------------------
# UI GreenMetric — Sustainability ranking
# ---------------------------------------------------------------------------

_GREENMETRIC_CONTROLS: list[FrameworkControl] = [
    _control(
        "gm-setting",
        "CAT-1",
        "Setting and Infrastructure",
        "Campus area, vegetation, sustainable buildings, and green space.",
        weight=3,
        tests=[
            _doc(
                "gm-setting-t1",
                "Campus sustainability report with green-space data",
                "TPLT_CAMPUS_SUSTAINABILITY",
            ),
            _kpi(
                "gm-setting-t2",
                "Green-area ratio ≥ 30% of campus",
                "ESG-04",
                0.30,
            ),
        ],
    ),
    _control(
        "gm-energy",
        "CAT-2",
        "Energy and Climate Change",
        "Energy efficiency, renewable energy, and climate-change programs.",
        weight=5,
        tests=[
            _kpi(
                "gm-energy-t1",
                "Renewable-energy share ≥ 15%",
                "ESG-02",
                0.15,
            ),
            _doc("gm-energy-t2", "Energy reduction action plan approved", "TPLT_ENERGY_PLAN"),
        ],
    ),
    _control(
        "gm-waste",
        "CAT-3",
        "Waste Management",
        "Recycling programs, waste reduction, and hazardous waste handling.",
        weight=4,
        tests=[
            _kpi(
                "gm-waste-t1",
                "Recycling rate ≥ 40%",
                "ESG-03",
                0.40,
            ),
            _doc("gm-waste-t2", "Waste management policy document", "TPLT_WASTE_MANAGEMENT"),
        ],
    ),
    _control(
        "gm-water",
        "CAT-4",
        "Water Conservation",
        "Water usage monitoring and conservation programs.",
        weight=4,
        tests=[
            _doc("gm-water-t1", "Water conservation program documented", "TPLT_WATER_CONSERVATION"),
        ],
    ),
    _control(
        "gm-transport",
        "CAT-5",
        "Transportation",
        "Green transportation policy and sustainable mobility programs.",
        weight=3,
        tests=[
            _doc("gm-transport-t1", "Green transportation policy approved", "TPLT_TRANSPORT_POLICY"),
        ],
    ),
    _control(
        "gm-education",
        "CAT-6",
        "Education and Research",
        "Sustainability courses, research publications, and community engagement.",
        weight=5,
        tests=[
            _kpi(
                "gm-education-t1",
                "Sustainability research publications ≥ 2/yr",
                "RES-01",
                2,
            ),
            _doc(
                "gm-education-t2",
                "Sustainability education program documented",
                "TPLT_SUSTAINABILITY_PROGRAM",
            ),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Framework registry
# ---------------------------------------------------------------------------


FRAMEWORKS: dict[str, Framework] = {
    "ISO9001": Framework(
        code="ISO9001",
        name="ISO 9001",
        version="2015",
        scope=FrameworkScope.INSTITUTION,
        controls=_ISO9001_CONTROLS,
    ),
    "ISO21001": Framework(
        code="ISO21001",
        name="ISO 21001",
        version="2018",
        scope=FrameworkScope.INSTITUTION,
        controls=_ISO21001_CONTROLS,
    ),
    "GREENMETRIC": Framework(
        code="GREENMETRIC",
        name="UI GreenMetric",
        version="2024",
        scope=FrameworkScope.INSTITUTION,
        controls=_GREENMETRIC_CONTROLS,
    ),
}


# Surface-level descriptors useful for the API/UI without re-deriving from
# `Framework`. Kept tiny on purpose so it doesn't drift.
FRAMEWORK_METADATA: dict[str, dict[str, str]] = {
    "ISO9001": {
        "full_name": "ISO 9001:2015 Quality Management System",
        "description": (
            "International standard for quality management systems, ensuring "
            "consistent quality of products and services."
        ),
        "category": "QMS",
    },
    "ISO21001": {
        "full_name": "ISO 21001:2018 Educational Organizations Management System",
        "description": (
            "Management system standard for educational organizations focused "
            "on enhancing learner satisfaction."
        ),
        "category": "EOMS",
    },
    "GREENMETRIC": {
        "full_name": "UI GreenMetric World University Rankings",
        "description": (
            "Sustainability ranking evaluating campus green practices across "
            "six categories."
        ),
        "category": "SUSTAINABILITY",
    },
}


def get_framework(code: str) -> Framework | None:
    return FRAMEWORKS.get(code.upper())


def all_frameworks() -> list[Framework]:
    return [fw for fw in FRAMEWORKS.values() if fw.is_active]
