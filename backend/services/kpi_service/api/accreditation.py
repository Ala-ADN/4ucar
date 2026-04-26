"""Accreditation compliance API — demo endpoints."""

from __future__ import annotations

from collections import Counter
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.services.kpi_service.domain.accreditation import (
    FRAMEWORKS,
    INSTITUTIONS,
    ControlStatusResult,
    EvidenceRecord,
    EvidenceStatus,
    Framework,
    FrameworkPosture,
    GapItem,
    approve_evidence,
    evaluate_control,
    get_evidence_portfolio,
    get_framework_posture,
    get_gap_analysis,
    get_network_summary,
)

router = APIRouter(prefix="/accreditation", tags=["accreditation"])

_DEFAULT_PERIOD = 2026


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve(framework_code: str, institution_code: str) -> tuple[str, str]:
    """Validate and normalise path params; raise 404 on unknown values."""
    fw_code = framework_code.upper()
    inst = institution_code.upper()
    if fw_code not in FRAMEWORKS:
        raise HTTPException(404, f"Framework not found. Available: {list(FRAMEWORKS.keys())}")
    if inst not in INSTITUTIONS:
        raise HTTPException(404, f"Institution not found. Available: {INSTITUTIONS}")
    return fw_code, inst


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class FrameworkSummary(BaseModel):
    code: str
    name: str
    full_name: str
    version: str
    description: str
    category: str
    total_controls: int

    @classmethod
    def from_domain(cls, fw: Framework) -> FrameworkSummary:
        return cls(
            code=fw.code,
            name=fw.name,
            full_name=fw.full_name,
            version=fw.version,
            description=fw.description,
            category=fw.category,
            total_controls=fw.total_controls,
        )


class EvidenceResponse(BaseModel):
    framework_code: str
    institution_code: str
    period_year: int
    total_evidence: int
    approved: int
    pending: int
    rejected: int
    records: list[EvidenceRecord]


class GapAnalysisResponse(BaseModel):
    framework_code: str
    institution_code: str
    period_year: int
    total_gaps: int
    gaps: list[GapItem]


class ApproveEvidenceRequest(BaseModel):
    test_id: str
    doc_name: Optional[str] = "Uploaded Document"
    template_id: Optional[str] = None


class ApproveEvidenceResponse(BaseModel):
    message: str
    evidence: EvidenceRecord
    updated_control_status: ControlStatusResult


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/frameworks", response_model=list[FrameworkSummary])
def list_frameworks():
    """List all accreditation frameworks."""
    return [FrameworkSummary.from_domain(fw) for fw in FRAMEWORKS.values()]


@router.get("/frameworks/{framework_code}", response_model=FrameworkSummary)
def get_framework(framework_code: str):
    """Get framework details."""
    fw = FRAMEWORKS.get(framework_code.upper())
    if not fw:
        raise HTTPException(404, f"Framework '{framework_code}' not found. Available: {list(FRAMEWORKS.keys())}")
    return FrameworkSummary.from_domain(fw)


@router.get("/institutions", response_model=list[str])
def list_institutions():
    """List demo institutions."""
    return INSTITUTIONS


@router.get("/network", response_model=list[dict])
def network_summary(period: int = Query(default=_DEFAULT_PERIOD, description="Period year")):
    """Aggregate compliance posture across all institutions and frameworks."""
    return get_network_summary(period)


@router.get("/{framework_code}/status/{institution_code}", response_model=FrameworkPosture)
def framework_status(
    framework_code: str,
    institution_code: str,
    period: int = Query(default=_DEFAULT_PERIOD),
):
    """Full control pass/fail status for one institution against one framework."""
    fw_code, inst = _resolve(framework_code, institution_code)
    return get_framework_posture(fw_code, inst, period)


@router.get("/{framework_code}/evidence/{institution_code}", response_model=EvidenceResponse)
def evidence_portfolio(
    framework_code: str,
    institution_code: str,
    period: int = Query(default=_DEFAULT_PERIOD),
):
    """Evidence portfolio for one institution against one framework."""
    fw_code, inst = _resolve(framework_code, institution_code)
    records = get_evidence_portfolio(fw_code, inst, period)
    counts = Counter(r.status for r in records)
    return EvidenceResponse(
        framework_code=fw_code,
        institution_code=inst,
        period_year=period,
        total_evidence=len(records),
        approved=counts[EvidenceStatus.APPROVED],
        pending=counts[EvidenceStatus.PENDING],
        rejected=counts[EvidenceStatus.REJECTED],
        records=records,
    )


@router.get("/{framework_code}/gaps/{institution_code}", response_model=GapAnalysisResponse)
def gap_analysis(
    framework_code: str,
    institution_code: str,
    period: int = Query(default=_DEFAULT_PERIOD),
):
    """Gap analysis sorted by priority (weight × distance to passing)."""
    fw_code, inst = _resolve(framework_code, institution_code)
    gaps = get_gap_analysis(fw_code, inst, period)
    return GapAnalysisResponse(
        framework_code=fw_code,
        institution_code=inst,
        period_year=period,
        total_gaps=len(gaps),
        gaps=gaps,
    )


@router.post(
    "/{framework_code}/controls/{control_id}/evidence/{institution_code}",
    response_model=ApproveEvidenceResponse,
)
def submit_and_approve_evidence(
    framework_code: str,
    control_id: str,
    institution_code: str,
    body: ApproveEvidenceRequest,
    period: int = Query(default=_DEFAULT_PERIOD),
):
    """Submit evidence for a control test and immediately approve it (demo).

    Simulates the document upload → review → approve flow that triggers
    real-time control status re-evaluation.
    """
    fw_code, inst = _resolve(framework_code, institution_code)

    fw = FRAMEWORKS[fw_code]
    control = next((c for c in fw.controls if c.control_id == control_id), None)
    if control is None:
        raise HTTPException(404, f"Control '{control_id}' not found in {fw_code}.")

    test = next((t for t in control.tests if t.test_id == body.test_id), None)
    if test is None:
        raise HTTPException(404, f"Test '{body.test_id}' not found. Valid: {[t.test_id for t in control.tests]}")

    record = approve_evidence(
        control_id=control_id,
        test_id=body.test_id,
        institution_code=inst,
        period_year=period,
        doc_name=body.doc_name or "Uploaded Document",
        template_id=body.template_id or test.template_id,
    )
    updated_status = evaluate_control(control, inst, period)

    return ApproveEvidenceResponse(
        message=f"Evidence approved. Control '{control_id}' re-evaluated to {updated_status.status.value}.",
        evidence=record,
        updated_control_status=updated_status,
    )
