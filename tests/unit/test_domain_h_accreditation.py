"""Unit tests for Domain H (Accreditation & Compliance) evaluator.

The engine is qualitative: it returns ControlEvaluation with status
PASSING/FAILING/NEEDS_EVIDENCE/NOT_APPLICABLE. Tests verify the decision
tree and per-test-type semantics, not numeric values.
"""

from __future__ import annotations

from datetime import date

import pytest

from backend.services.kpi_service.domain import (
    ApprovedDocument,
    Attestation,
    ControlStatus,
    ControlTest,
    ControlWaiver,
    Framework,
    FrameworkControl,
    InstitutionAccreditationInputs,
    TestPeriodScope,
    TestType,
    compute_accreditation,
    framework_completion_score,
    gap_analysis,
)
from backend.services.kpi_service.domain.accreditation import (
    evaluate_control,
    evaluate_framework,
)

PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 12, 31)


def _inputs(**overrides) -> InstitutionAccreditationInputs:
    base = dict(
        institution_id="i1",
        institution_code="INSAT",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
    )
    base.update(overrides)
    return InstitutionAccreditationInputs(**base)


def _kpi_test(test_id: str, kpi_id: str, threshold: float) -> ControlTest:
    return ControlTest(
        id=test_id,
        test_type=TestType.AUTOMATED_KPI,
        name=f"KPI {kpi_id} >= {threshold}",
        kpi_id=kpi_id,
        threshold=threshold,
    )


def _doc_test(test_id: str, templates: list[str], count: int = 1) -> ControlTest:
    return ControlTest(
        id=test_id,
        test_type=TestType.DOCUMENT_UPLOAD,
        name=f"Upload {templates}",
        required_template_codes=templates,
        required_document_count=count,
        period_scope=TestPeriodScope.CURRENT_YEAR,
    )


def _attest_test(test_id: str) -> ControlTest:
    return ControlTest(
        id=test_id,
        test_type=TestType.ATTESTATION,
        name=f"Attestation {test_id}",
    )


# ---------------------------------------------------------------------------
# Per-test-type evaluation
# ---------------------------------------------------------------------------


class TestKpiTest:
    def test_passing_when_above_threshold(self):
        ctrl = FrameworkControl(
            id="c1", code="QS-CPF", name="Citations per Faculty",
            tests=[_kpi_test("t1", "RES-01", 5.0)],
        )
        fw = Framework(code="QS", name="QS", controls=[ctrl])
        result = evaluate_control(_inputs(kpi_values={"RES-01": 7.5}), fw, ctrl)
        assert result.status == ControlStatus.PASSING

    def test_failing_when_below(self):
        ctrl = FrameworkControl(
            id="c1", code="QS-CPF", name="Citations per Faculty",
            tests=[_kpi_test("t1", "RES-01", 5.0)],
        )
        fw = Framework(code="QS", name="QS", controls=[ctrl])
        result = evaluate_control(_inputs(kpi_values={"RES-01": 2.3}), fw, ctrl)
        assert result.status == ControlStatus.FAILING
        assert result.failing_test_ids == ["t1"]
        # KPI was on file but below threshold => FAILING (not NEEDS_EVIDENCE)
        assert result.missing_evidence["kpi_inputs_needed"][0]["kpi_id"] == "RES-01"

    def test_needs_evidence_when_kpi_missing(self):
        ctrl = FrameworkControl(
            id="c1", code="QS-CPF", name="Citations per Faculty",
            tests=[_kpi_test("t1", "RES-01", 5.0)],
        )
        fw = Framework(code="QS", name="QS", controls=[ctrl])
        result = evaluate_control(_inputs(kpi_values={}), fw, ctrl)
        assert result.status == ControlStatus.NEEDS_EVIDENCE


class TestDocumentTest:
    def test_passing_when_doc_present(self):
        ctrl = FrameworkControl(
            id="c1", code="ISO-7.5", name="Faculty records",
            tests=[_doc_test("t1", ["faculty_record"])],
        )
        fw = Framework(code="ISO", name="ISO 21001", controls=[ctrl])
        docs = [ApprovedDocument(
            document_id="d1", template_code="faculty_record",
            approved_at=date(2026, 5, 1), period_year=2026,
        )]
        result = evaluate_control(_inputs(approved_documents=docs), fw, ctrl)
        assert result.status == ControlStatus.PASSING

    def test_failing_when_count_below_required(self):
        ctrl = FrameworkControl(
            id="c1", code="X", name="X",
            tests=[_doc_test("t1", ["faculty_record"], count=3)],
        )
        fw = Framework(code="ISO", name="ISO", controls=[ctrl])
        docs = [
            ApprovedDocument(
                document_id=f"d{i}", template_code="faculty_record",
                approved_at=date(2026, 1, 1), period_year=2026,
            )
            for i in range(2)  # only 2 of 3 needed
        ]
        result = evaluate_control(_inputs(approved_documents=docs), fw, ctrl)
        assert result.status == ControlStatus.FAILING
        assert result.missing_evidence["templates_needed"][0]["have"] == 2
        assert result.missing_evidence["templates_needed"][0]["needed"] == 3

    def test_needs_evidence_when_no_docs(self):
        ctrl = FrameworkControl(
            id="c1", code="X", name="X",
            tests=[_doc_test("t1", ["faculty_record"])],
        )
        fw = Framework(code="ISO", name="ISO", controls=[ctrl])
        result = evaluate_control(_inputs(), fw, ctrl)
        assert result.status == ControlStatus.NEEDS_EVIDENCE

    def test_period_scope_excludes_old_doc(self):
        ctrl = FrameworkControl(
            id="c1", code="X", name="X",
            tests=[_doc_test("t1", ["faculty_record"])],
        )
        fw = Framework(code="ISO", name="ISO", controls=[ctrl])
        # period 2026, doc tagged 2023 -> out of CURRENT_YEAR scope
        docs = [ApprovedDocument(
            document_id="d1", template_code="faculty_record",
            approved_at=date(2023, 5, 1), period_year=2023,
        )]
        result = evaluate_control(_inputs(approved_documents=docs), fw, ctrl)
        assert result.status == ControlStatus.NEEDS_EVIDENCE


class TestAttestationTest:
    def test_passing_when_active_attestation(self):
        ctrl = FrameworkControl(
            id="c1", code="ARWU-AWARD", name="Staff Nobel/Fields",
            tests=[_attest_test("t1")],
        )
        fw = Framework(code="ARWU", name="ARWU", controls=[ctrl])
        result = evaluate_control(
            _inputs(attestations=[Attestation(test_id="t1", attested_by="dean")]),
            fw, ctrl,
        )
        assert result.status == ControlStatus.PASSING

    def test_inactive_attestation_does_not_pass(self):
        ctrl = FrameworkControl(
            id="c1", code="X", name="X", tests=[_attest_test("t1")],
        )
        fw = Framework(code="ARWU", name="ARWU", controls=[ctrl])
        result = evaluate_control(
            _inputs(attestations=[Attestation(test_id="t1", is_active=False)]),
            fw, ctrl,
        )
        assert result.status == ControlStatus.NEEDS_EVIDENCE


# ---------------------------------------------------------------------------
# Status decision tree
# ---------------------------------------------------------------------------


class TestStatusDecisionTree:
    def test_waiver_overrides_everything(self):
        ctrl = FrameworkControl(
            id="c1", code="X", name="X",
            tests=[_kpi_test("t1", "RES-01", 5.0)],
        )
        fw = Framework(code="QS", name="QS", controls=[ctrl])
        result = evaluate_control(
            _inputs(
                kpi_values={"RES-01": 100.0},  # would otherwise PASS
                waivers=[ControlWaiver(control_id="c1", reason="not in scope this year")],
            ),
            fw, ctrl,
        )
        assert result.status == ControlStatus.NOT_APPLICABLE
        assert result.not_applicable_reason == "not in scope this year"

    def test_external_survey_with_no_evidence_is_NA(self):
        ctrl = FrameworkControl(
            id="c1", code="QS-AR", name="Academic Reputation",
            requires_external_survey=True,
            tests=[_doc_test("t1", ["qs_academic_reputation_results"])],
        )
        fw = Framework(code="QS", name="QS", controls=[ctrl])
        result = evaluate_control(_inputs(), fw, ctrl)
        assert result.status == ControlStatus.NOT_APPLICABLE
        assert "external survey" in (result.not_applicable_reason or "")

    def test_external_survey_with_evidence_evaluates_normally(self):
        ctrl = FrameworkControl(
            id="c1", code="QS-AR", name="Academic Reputation",
            requires_external_survey=True,
            tests=[_doc_test("t1", ["qs_academic_reputation_results"])],
        )
        fw = Framework(code="QS", name="QS", controls=[ctrl])
        docs = [ApprovedDocument(
            document_id="d1", template_code="qs_academic_reputation_results",
            approved_at=date(2026, 5, 1), period_year=2026,
        )]
        result = evaluate_control(_inputs(approved_documents=docs), fw, ctrl)
        assert result.status == ControlStatus.PASSING

    def test_multiple_tests_all_must_pass(self):
        ctrl = FrameworkControl(
            id="c1", code="QS-FSR", name="Faculty/Student Ratio",
            tests=[
                _kpi_test("t1", "ACA-01", 25.0),
                _doc_test("t2", ["faculty_record"]),
            ],
        )
        fw = Framework(code="QS", name="QS", controls=[ctrl])
        # KPI fails, doc passes -> FAILING
        result = evaluate_control(
            _inputs(
                kpi_values={"ACA-01": 35.0},  # we need >=25 for "passing", here 35 passes; let's flip
            ),
            fw, ctrl,
        )
        # Hmm: with threshold>=25 and value=35, KPI test passes. Doc test fails (no doc).
        # So FAILING.
        assert result.status == ControlStatus.FAILING


# ---------------------------------------------------------------------------
# Aggregations
# ---------------------------------------------------------------------------


def _three_control_qs() -> Framework:
    return Framework(
        code="QS", name="QS",
        controls=[
            FrameworkControl(
                id="c1", code="QS-CPF", name="CPF", weight=0.20,
                tests=[_kpi_test("t1", "RES-01", 5.0)],
            ),
            FrameworkControl(
                id="c2", code="QS-FSR", name="FSR", weight=0.10,
                tests=[_kpi_test("t2", "ACA-01", 25.0)],
            ),
            FrameworkControl(
                id="c3", code="QS-AR", name="AR", weight=0.30,
                requires_external_survey=True,
                tests=[_doc_test("t3", ["qs_academic_reputation_results"])],
            ),
        ],
    )


def test_compute_accreditation_returns_per_framework():
    fw = _three_control_qs()
    inputs = _inputs(
        frameworks=[fw],
        kpi_values={"RES-01": 7.0, "ACA-01": 100.0},  # 7>=5 pass; 100>=25 pass
    )
    result = compute_accreditation(inputs)
    assert "QS" in result
    by_code = {e.control_code: e for e in result["QS"]}
    assert by_code["QS-CPF"].status == ControlStatus.PASSING
    assert by_code["QS-FSR"].status == ControlStatus.PASSING
    # AR has no evidence + requires_external_survey -> NOT_APPLICABLE
    assert by_code["QS-AR"].status == ControlStatus.NOT_APPLICABLE


def test_framework_completion_score_excludes_not_applicable():
    evaluations = evaluate_framework(
        _inputs(
            frameworks=[_three_control_qs()],
            kpi_values={"RES-01": 7.0, "ACA-01": 100.0},
        ),
        _three_control_qs(),
    )
    score = framework_completion_score(evaluations)
    # 2 PASSING (weights 0.20, 0.10), 1 NOT_APPLICABLE (excluded)
    # weighted = (0.20 + 0.10) / (0.20 + 0.10) = 100%
    assert score == 100.0


def test_framework_completion_score_partial():
    fw = _three_control_qs()
    evaluations = evaluate_framework(
        _inputs(frameworks=[fw], kpi_values={"RES-01": 7.0, "ACA-01": 5.0}),
        fw,
    )
    # CPF passes (0.20), FSR fails (0.10), AR NA (excluded)
    # weighted = 0.20 / (0.20 + 0.10) = 66.67%
    score = framework_completion_score(evaluations)
    assert score == pytest.approx(200 / 3)


def test_gap_analysis_sorts_by_weight():
    fw = _three_control_qs()
    evaluations = evaluate_framework(
        _inputs(frameworks=[fw], kpi_values={"RES-01": 1.0, "ACA-01": 5.0}),
        fw,
    )
    gaps = gap_analysis(evaluations)
    # CPF (weight 0.20) and FSR (0.10) are both failing; AR is NOT_APPLICABLE (excluded).
    assert [g.control_code for g in gaps] == ["QS-CPF", "QS-FSR"]


def test_iso_mini_framework_with_attestation_and_doc():
    """Mini ISO framework exercising all three test types and the
    template-link semantics from accreditation.md s11.
    """
    fw = Framework(
        code="ISO21001", name="ISO 21001",
        controls=[
            FrameworkControl(
                id="iso-4-1", code="ISO-4.1", name="Org context", weight=0.05,
                tests=[_attest_test("t-iso-4-1")],
            ),
            FrameworkControl(
                id="iso-7-1", code="ISO-7.1", name="Competence",
                tests=[_doc_test("t-iso-7-1", ["faculty_record", "hiring_dossier"])],
            ),
        ],
    )
    docs = [
        ApprovedDocument(document_id="d1", template_code="faculty_record",
                         approved_at=date(2026, 3, 1), period_year=2026),
        ApprovedDocument(document_id="d2", template_code="hiring_dossier",
                         approved_at=date(2026, 4, 1), period_year=2026),
    ]
    attestations = [Attestation(test_id="t-iso-4-1", attested_by="dean")]
    result = compute_accreditation(_inputs(
        frameworks=[fw], approved_documents=docs, attestations=attestations,
    ))
    by_code = {e.control_code: e for e in result["ISO21001"]}
    assert by_code["ISO-4.1"].status == ControlStatus.PASSING
    assert by_code["ISO-7.1"].status == ControlStatus.PASSING
