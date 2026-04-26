"""Accreditation compliance API.

All endpoints route through the typed Domain H engine
(`backend.services.kpi_service.domain.accreditation`) over inputs assembled
from the in-memory demo fixtures. The same shape (`InstitutionAccreditation
Inputs`) is what the production wiring will populate from the doc-service +
KPI computation pipeline — so the engine path is identical between demo
and production.
"""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.services.kpi_service.domain.accreditation import (
    evaluate_framework,
    framework_completion_score,
    gap_analysis,
)
from backend.services.kpi_service.domain.demo_fixtures import (
    DEMO_PERIOD_YEAR,
    EvidenceRecord,
    EvidenceStatus,
    build_inputs,
    evidence_for,
    list_institutions,
    submit_evidence,
)
from backend.services.kpi_service.domain.frameworks import (
    FRAMEWORK_METADATA,
    FRAMEWORKS,
    get_framework,
)
from backend.services.kpi_service.domain.inputs import (
    Framework,
    FrameworkControl,
)
from backend.services.kpi_service.domain.result import (
    ControlEvaluation,
    ControlStatus,
)

router = APIRouter(prefix="/accreditation", tags=["accreditation"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_framework(framework_code: str) -> Framework:
    fw = get_framework(framework_code)
    if fw is None:
        raise HTTPException(
            404, f"Framework not found. Available: {list(FRAMEWORKS.keys())}"
        )
    return fw


def _resolve(framework_code: str, institution_code: str) -> tuple[Framework, str]:
    fw = _resolve_framework(framework_code)
    inst = institution_code.upper()
    if inst not in list_institutions():
        raise HTTPException(
            404, f"Institution not found. Available: {list_institutions()}"
        )
    return fw, inst


def _evaluate_one(framework: Framework, institution: str) -> list[ControlEvaluation]:
    inputs = build_inputs(institution)
    if inputs is None:
        raise HTTPException(404, f"No demo state for institution {institution}")
    return evaluate_framework(inputs, framework)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class FrameworkSummary(BaseModel):
    code: str
    name: str
    full_name: str
    version: str | None
    description: str
    category: str
    total_controls: int

    @classmethod
    def from_domain(cls, fw: Framework) -> "FrameworkSummary":
        meta = FRAMEWORK_METADATA.get(fw.code, {})
        return cls(
            code=fw.code,
            name=fw.name,
            full_name=meta.get("full_name", fw.name),
            version=fw.version,
            description=meta.get("description", ""),
            category=meta.get("category", "OTHER"),
            total_controls=len(fw.controls),
        )


class TestDescriptor(BaseModel):
    test_id: str
    test_type: str
    name: str
    kpi_id: str | None = None
    threshold: float | None = None
    threshold_comparator: str | None = None
    required_template_codes: list[str] | None = None


class ControlDescriptor(BaseModel):
    control_id: str
    clause_ref: str
    name: str
    description: str | None
    weight: float
    requires_external_survey: bool
    tests: list[TestDescriptor]

    @classmethod
    def from_domain(cls, c: FrameworkControl) -> "ControlDescriptor":
        return cls(
            control_id=c.id,
            clause_ref=c.code,
            name=c.name,
            description=c.description,
            weight=c.weight,
            requires_external_survey=c.requires_external_survey,
            tests=[
                TestDescriptor(
                    test_id=t.id,
                    test_type=t.test_type.value,
                    name=t.name,
                    kpi_id=t.kpi_id,
                    threshold=t.threshold,
                    threshold_comparator=t.threshold_comparator,
                    required_template_codes=t.required_template_codes,
                )
                for t in c.tests
            ],
        )


class FrameworkDetail(FrameworkSummary):
    controls: list[ControlDescriptor]

    @classmethod
    def from_framework(cls, fw: Framework) -> "FrameworkDetail":
        summary = FrameworkSummary.from_domain(fw)
        return cls(
            **summary.model_dump(),
            controls=[ControlDescriptor.from_domain(c) for c in fw.controls],
        )


class ControlStatusOut(BaseModel):
    control_id: str
    clause_ref: str
    name: str
    framework_code: str
    weight: float
    status: str
    passing_test_ids: list[str]
    failing_test_ids: list[str]
    missing_evidence: dict
    not_applicable_reason: str | None = None

    @classmethod
    def from_evaluation(cls, ev: ControlEvaluation) -> "ControlStatusOut":
        return cls(
            control_id=ev.control_code,  # control.code in our domain
            clause_ref=ev.control_code,
            name=ev.name,
            framework_code=ev.framework_code,
            weight=ev.weight,
            status=ev.status.value,
            passing_test_ids=ev.passing_test_ids,
            failing_test_ids=ev.failing_test_ids,
            missing_evidence=ev.missing_evidence,
            not_applicable_reason=ev.not_applicable_reason,
        )


class FrameworkPostureOut(BaseModel):
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
    compliance_level: str
    controls: list[ControlStatusOut]


class EvidenceRecordOut(BaseModel):
    evidence_id: str
    institution_code: str
    framework_code: str
    control_id: str
    test_id: str
    template_code: str | None
    doc_name: str | None
    period_year: int
    status: str
    submitted_at: str
    approved_at: str | None = None
    notes: str | None = None

    @classmethod
    def from_record(cls, r: EvidenceRecord) -> "EvidenceRecordOut":
        return cls(
            evidence_id=r.evidence_id,
            institution_code=r.institution_code,
            framework_code=r.framework_code,
            control_id=r.control_id,
            test_id=r.test_id,
            template_code=r.template_code,
            doc_name=r.doc_name,
            period_year=r.period_year,
            status=r.status.value,
            submitted_at=r.submitted_at.isoformat(),
            approved_at=r.approved_at.isoformat() if r.approved_at else None,
            notes=r.notes,
        )


class EvidencePortfolioOut(BaseModel):
    framework_code: str
    institution_code: str
    period_year: int
    total_evidence: int
    approved: int
    pending: int
    rejected: int
    records: list[EvidenceRecordOut]


class GapItemOut(BaseModel):
    control_id: str
    clause_ref: str
    name: str
    weight: float
    status: str
    priority_score: float
    missing_test_ids: list[str]
    suggested_actions: list[str]


class GapAnalysisOut(BaseModel):
    framework_code: str
    institution_code: str
    period_year: int
    total_gaps: int
    gaps: list[GapItemOut]


class ApproveEvidenceRequest(BaseModel):
    test_id: str
    doc_name: str | None = "Uploaded Document"
    template_code: str | None = None


class ApproveEvidenceResponse(BaseModel):
    message: str
    evidence: EvidenceRecordOut
    updated_control_status: ControlStatusOut


# ---------------------------------------------------------------------------
# Posture / gap helpers
# ---------------------------------------------------------------------------


def _compliance_level(score_pct: float) -> str:
    if score_pct >= 85:
        return "COMPLIANT"
    if score_pct >= 60:
        return "PARTIAL"
    return "NON_COMPLIANT"


def _build_posture(
    framework: Framework,
    institution: str,
    evaluations: list[ControlEvaluation],
) -> FrameworkPostureOut:
    counts = Counter(e.status for e in evaluations)
    passing = counts.get(ControlStatus.PASSING, 0)
    failing = counts.get(ControlStatus.FAILING, 0)
    needs_ev = counts.get(ControlStatus.NEEDS_EVIDENCE, 0)
    not_app = counts.get(ControlStatus.NOT_APPLICABLE, 0)
    score_pct = round(framework_completion_score(evaluations), 1)
    return FrameworkPostureOut(
        framework_code=framework.code,
        framework_name=framework.name,
        institution_code=institution,
        period_year=DEMO_PERIOD_YEAR,
        passing=passing,
        failing=failing,
        needs_evidence=needs_ev,
        not_applicable=not_app,
        total=len(evaluations),
        score_pct=score_pct,
        compliance_level=_compliance_level(score_pct),
        controls=[ControlStatusOut.from_evaluation(e) for e in evaluations],
    )


def _suggest_actions(
    control: FrameworkControl, evaluation: ControlEvaluation, kpi_values: dict
) -> list[str]:
    actions: list[str] = []
    failing_or_needed = set(evaluation.failing_test_ids) | {
        m.get("kpi_id") for m in evaluation.missing_evidence.get("kpi_inputs_needed", []) if m
    }
    for test in control.tests:
        if test.id not in failing_or_needed and test.id not in evaluation.failing_test_ids:
            continue
        if test.test_type.value == "DOCUMENT_UPLOAD" and test.required_template_codes:
            actions.append(
                f"Upload '{test.required_template_codes[0]}': {test.name}"
            )
        elif test.test_type.value == "AUTOMATED_KPI" and test.kpi_id:
            current = kpi_values.get(test.kpi_id)
            current_str = f"{current:.2f}" if isinstance(current, (int, float)) else "N/A"
            actions.append(
                f"Improve {test.kpi_id} {test.threshold_comparator} {test.threshold} "
                f"(current: {current_str})"
            )
        elif test.test_type.value == "ATTESTATION":
            actions.append(f"Submit attestation: {test.name}")
    return actions


def _build_gaps(
    framework: Framework, institution: str, evaluations: list[ControlEvaluation]
) -> GapAnalysisOut:
    inputs = build_inputs(institution)
    kpi_values = dict(inputs.kpi_values) if inputs else {}
    controls_by_code = {c.code: c for c in framework.controls}

    gaps: list[GapItemOut] = []
    for ev in evaluations:
        if ev.status not in (ControlStatus.FAILING, ControlStatus.NEEDS_EVIDENCE):
            continue
        control = controls_by_code.get(ev.control_code)
        total_tests = ev.total_required_tests or (len(control.tests) if control else 1)
        passing_fraction = (
            len(ev.passing_test_ids) / total_tests if total_tests else 0.0
        )
        priority = round(ev.weight * (1 - passing_fraction), 2)
        gaps.append(
            GapItemOut(
                control_id=ev.control_code,
                clause_ref=ev.control_code,
                name=ev.name,
                weight=ev.weight,
                status=ev.status.value,
                priority_score=priority,
                missing_test_ids=ev.failing_test_ids,
                suggested_actions=_suggest_actions(control, ev, kpi_values) if control else [],
            )
        )
    gaps.sort(key=lambda g: g.priority_score, reverse=True)
    return GapAnalysisOut(
        framework_code=framework.code,
        institution_code=institution,
        period_year=DEMO_PERIOD_YEAR,
        total_gaps=len(gaps),
        gaps=gaps,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/frameworks", response_model=list[FrameworkSummary])
def list_frameworks() -> list[FrameworkSummary]:
    return [FrameworkSummary.from_domain(fw) for fw in FRAMEWORKS.values()]


@router.get("/frameworks/{framework_code}", response_model=FrameworkDetail)
def framework_detail(framework_code: str) -> FrameworkDetail:
    fw = _resolve_framework(framework_code)
    return FrameworkDetail.from_framework(fw)


@router.get("/institutions", response_model=list[str])
def institutions_list() -> list[str]:
    return list_institutions()


@router.get("/network", response_model=list[dict])
def network_summary(
    period: int = Query(default=DEMO_PERIOD_YEAR, description="Period year"),
) -> list[dict]:
    rows: list[dict] = []
    for inst in list_institutions():
        row: dict = {"institution_code": inst, "frameworks": {}}
        for fw_code, fw in FRAMEWORKS.items():
            evaluations = _evaluate_one(fw, inst)
            score = round(framework_completion_score(evaluations), 1)
            counts = Counter(e.status for e in evaluations)
            row["frameworks"][fw_code] = {
                "score_pct": score,
                "compliance_level": _compliance_level(score),
                "passing": counts.get(ControlStatus.PASSING, 0),
                "total": len(evaluations),
            }
        rows.append(row)
    return rows


@router.get("/{framework_code}/status/{institution_code}", response_model=FrameworkPostureOut)
def framework_status(
    framework_code: str,
    institution_code: str,
    period: int = Query(default=DEMO_PERIOD_YEAR),
) -> FrameworkPostureOut:
    fw, inst = _resolve(framework_code, institution_code)
    evaluations = _evaluate_one(fw, inst)
    return _build_posture(fw, inst, evaluations)


@router.get("/{framework_code}/evidence/{institution_code}", response_model=EvidencePortfolioOut)
def evidence_portfolio(
    framework_code: str,
    institution_code: str,
    period: int = Query(default=DEMO_PERIOD_YEAR),
) -> EvidencePortfolioOut:
    fw, inst = _resolve(framework_code, institution_code)
    records = evidence_for(inst, framework=fw.code)
    counts = Counter(r.status for r in records)
    return EvidencePortfolioOut(
        framework_code=fw.code,
        institution_code=inst,
        period_year=period,
        total_evidence=len(records),
        approved=counts.get(EvidenceStatus.APPROVED, 0),
        pending=counts.get(EvidenceStatus.PENDING, 0),
        rejected=counts.get(EvidenceStatus.REJECTED, 0),
        records=[EvidenceRecordOut.from_record(r) for r in records],
    )


@router.get("/{framework_code}/gaps/{institution_code}", response_model=GapAnalysisOut)
def gaps(
    framework_code: str,
    institution_code: str,
    period: int = Query(default=DEMO_PERIOD_YEAR),
) -> GapAnalysisOut:
    fw, inst = _resolve(framework_code, institution_code)
    evaluations = _evaluate_one(fw, inst)
    return _build_gaps(fw, inst, evaluations)


@router.post(
    "/{framework_code}/controls/{control_id}/evidence/{institution_code}",
    response_model=ApproveEvidenceResponse,
)
def submit_and_approve_evidence(
    framework_code: str,
    control_id: str,
    institution_code: str,
    body: ApproveEvidenceRequest,
    period: int = Query(default=DEMO_PERIOD_YEAR),
) -> ApproveEvidenceResponse:
    fw, inst = _resolve(framework_code, institution_code)
    control = next((c for c in fw.controls if c.id == control_id), None)
    if control is None:
        raise HTTPException(404, f"Control '{control_id}' not found in {fw.code}.")
    test = next((t for t in control.tests if t.id == body.test_id), None)
    if test is None:
        raise HTTPException(
            404,
            f"Test '{body.test_id}' not found. Valid: {[t.id for t in control.tests]}",
        )

    template_code = body.template_code
    if template_code is None and test.required_template_codes:
        template_code = test.required_template_codes[0]

    record = submit_evidence(
        institution=inst,
        framework=fw.code,
        control_id=control_id,
        test_id=body.test_id,
        template_code=template_code,
        doc_name=body.doc_name or "Uploaded Document",
        auto_approve=True,
    )
    if record is None:
        raise HTTPException(500, "Failed to record evidence")

    evaluations = _evaluate_one(fw, inst)
    updated = next((e for e in evaluations if e.control_code == control.code), None)
    if updated is None:
        raise HTTPException(500, "Evaluation did not return updated control state")

    return ApproveEvidenceResponse(
        message=(
            f"Evidence approved. Control '{control_id}' re-evaluated to "
            f"{updated.status.value}."
        ),
        evidence=EvidenceRecordOut.from_record(record),
        updated_control_status=ControlStatusOut.from_evaluation(updated),
    )
