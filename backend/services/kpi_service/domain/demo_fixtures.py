"""In-memory demo fixtures for the accreditation API.

Pre-canned evidence portfolios + KPI snapshots for four UCAR institutions
(INSAT, ENIT, ENSI, ISET). The accreditation engine is pure — these
fixtures are *only* exercised by the API layer to demo realtime status
flips during walkthroughs. Production wires up the same `Institution
AccreditationInputs` shape from real data sources (doc-service for
approved documents, the KPI computation pipeline for kpi_values, etc.).

Mutability is deliberate but tightly scoped: `submit_evidence()` appends
to the in-process store. Restarting the service resets the demo to the
seeded state below.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum

from .inputs import (
    ApprovedDocument,
    Attestation,
    InstitutionAccreditationInputs,
)
from .frameworks import all_frameworks

INSTITUTIONS: list[str] = ["INSAT", "ENIT", "ENSI", "ISET"]
DEMO_PERIOD_YEAR = 2026
DEMO_PERIOD_START = date(DEMO_PERIOD_YEAR, 1, 1)
DEMO_PERIOD_END = date(DEMO_PERIOD_YEAR, 12, 31)


# ---------------------------------------------------------------------------
# Evidence catalog (richer than ApprovedDocument so the UI can render
# pending/rejected states; only APPROVED entries become ApprovedDocument
# rows fed to the engine).
# ---------------------------------------------------------------------------


class EvidenceStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


@dataclass
class EvidenceRecord:
    evidence_id: str
    institution_code: str
    framework_code: str
    control_id: str
    test_id: str
    template_code: str | None
    doc_name: str | None
    period_year: int
    status: EvidenceStatus
    submitted_at: datetime
    approved_at: datetime | None = None
    notes: str | None = None


@dataclass
class _InstitutionDemo:
    code: str
    evidence: list[EvidenceRecord] = field(default_factory=list)
    attestations: list[Attestation] = field(default_factory=list)
    kpi_values: dict[str, float | None] = field(default_factory=dict)


_NOW = datetime(DEMO_PERIOD_YEAR, 4, 26, 10, 0, 0)


def _ev(
    evidence_id: str,
    institution: str,
    framework: str,
    control: str,
    test: str,
    template: str,
    doc_name: str,
    *,
    status: EvidenceStatus = EvidenceStatus.APPROVED,
) -> EvidenceRecord:
    return EvidenceRecord(
        evidence_id=evidence_id,
        institution_code=institution,
        framework_code=framework,
        control_id=control,
        test_id=test,
        template_code=template,
        doc_name=doc_name,
        period_year=DEMO_PERIOD_YEAR,
        status=status,
        submitted_at=_NOW,
        approved_at=_NOW if status == EvidenceStatus.APPROVED else None,
    )


def _attestation(test_id: str, attested_by: str) -> Attestation:
    return Attestation(
        test_id=test_id,
        attested_by=attested_by,
        attestation_text="Director attestation submitted via demo portal.",
        attested_at=_NOW.date(),
        is_active=True,
    )


# ---------------------------------------------------------------------------
# Seeded institution states — mirrors the maturity tiers from the original
# demo (INSAT advanced, ENIT mid, ENSI early, ISET most advanced).
# ---------------------------------------------------------------------------


def _seed_institutions() -> dict[str, _InstitutionDemo]:
    insat = _InstitutionDemo(code="INSAT")
    enit = _InstitutionDemo(code="ENIT")
    ensi = _InstitutionDemo(code="ENSI")
    iset = _InstitutionDemo(code="ISET")

    # --- INSAT — strong ISO9001 + GreenMetric, partial ISO21001 -----------
    insat.attestations = [_attestation("iso9001-5.1-t1", "INSAT Director")]
    insat.evidence = [
        _ev("ev-001", "INSAT", "ISO9001", "iso9001-4.1", "iso9001-4.1-t1", "TPLT_STRATEGIC_CONTEXT", "INSAT Strategic Context 2026.pdf"),
        _ev("ev-002", "INSAT", "ISO9001", "iso9001-4.2", "iso9001-4.2-t1", "TPLT_STAKEHOLDER_REGISTER", "INSAT Stakeholder Register.pdf"),
        _ev("ev-004", "INSAT", "ISO9001", "iso9001-5.1", "iso9001-5.1-t2", "TPLT_QUALITY_POLICY", "INSAT Quality Policy 2026.pdf"),
        _ev("ev-005", "INSAT", "ISO9001", "iso9001-6.1", "iso9001-6.1-t1", "TPLT_RISK_REGISTER", "INSAT Risk Register 2026.xlsx"),
        _ev("ev-006", "INSAT", "ISO9001", "iso9001-7.5", "iso9001-7.5-t1", "TPLT_DOC_CONTROL_PROCEDURE", "Doc Control Procedure v2.pdf"),
        _ev("ev-007", "INSAT", "ISO9001", "iso9001-8.1", "iso9001-8.1-t1", "TPLT_OPS_PROCEDURES", "INSAT Ops Procedures Manual.pdf"),
        _ev("ev-008", "INSAT", "ISO9001", "iso9001-9.2", "iso9001-9.2-t1", "TPLT_INTERNAL_AUDIT_REPORT", "Internal Audit Report 2025.pdf"),
        _ev("ev-009", "INSAT", "ISO9001", "iso9001-9.1", "iso9001-9.1-t2", "TPLT_KPI_MONITORING_PLAN", "KPI Monitoring Plan Draft.pdf", status=EvidenceStatus.PENDING),
        _ev("ev-020", "INSAT", "ISO21001", "iso21001-4.1", "iso21001-4.1-t1", "TPLT_EOMS_CONTEXT", "INSAT EOMS Context 2026.pdf"),
        _ev("ev-021", "INSAT", "ISO21001", "iso21001-7.5", "iso21001-7.5-t1", "TPLT_DOC_CONTROL_PROCEDURE", "EOMS Doc Control Procedure.pdf"),
        _ev("ev-022", "INSAT", "ISO21001", "iso21001-8.3", "iso21001-8.3-t1", "TPLT_CURRICULUM_DESIGN", "Curriculum Design Process INSAT.pdf"),
        _ev("ev-023", "INSAT", "ISO21001", "iso21001-9.2", "iso21001-9.2-t1", "TPLT_INTERNAL_AUDIT_REPORT", "EOMS Internal Audit 2025.pdf"),
        _ev("ev-040", "INSAT", "GREENMETRIC", "gm-setting", "gm-setting-t1", "TPLT_CAMPUS_SUSTAINABILITY", "INSAT Campus Report 2025.pdf"),
        _ev("ev-041", "INSAT", "GREENMETRIC", "gm-energy", "gm-energy-t2", "TPLT_ENERGY_PLAN", "INSAT Energy Plan 2026.pdf"),
        _ev("ev-042", "INSAT", "GREENMETRIC", "gm-waste", "gm-waste-t2", "TPLT_WASTE_MANAGEMENT", "Waste Management Policy.pdf"),
        _ev("ev-043", "INSAT", "GREENMETRIC", "gm-education", "gm-education-t2", "TPLT_SUSTAINABILITY_PROGRAM", "Sustainability Education Program.pdf"),
    ]
    insat.kpi_values = {
        "ACA-01": 0.78,
        "ACA-06": 3.7,
        "EMP-01": 0.72,
        "HR-01": 0.08,
        "HR-04": 28,
        "RES-01": 12,
        "ESG-02": 0.18,
        "ESG-03": 0.45,
        "ESG-04": 0.35,
    }

    # --- ENIT — mid tier ---------------------------------------------------
    enit.attestations = [_attestation("iso9001-5.1-t1", "ENIT Director")]
    enit.evidence = [
        _ev("ev-101", "ENIT", "ISO9001", "iso9001-5.1", "iso9001-5.1-t2", "TPLT_QUALITY_POLICY", "ENIT Quality Policy.pdf"),
        _ev("ev-102", "ENIT", "ISO9001", "iso9001-7.5", "iso9001-7.5-t1", "TPLT_DOC_CONTROL_PROCEDURE", "ENIT Doc Control v1.pdf"),
        _ev("ev-103", "ENIT", "ISO9001", "iso9001-9.2", "iso9001-9.2-t1", "TPLT_INTERNAL_AUDIT_REPORT", "ENIT Audit Report 2025.pdf", status=EvidenceStatus.PENDING),
        _ev("ev-120", "ENIT", "ISO21001", "iso21001-7.5", "iso21001-7.5-t1", "TPLT_DOC_CONTROL_PROCEDURE", "ENIT EOMS Doc Control.pdf"),
        _ev("ev-140", "ENIT", "GREENMETRIC", "gm-energy", "gm-energy-t2", "TPLT_ENERGY_PLAN", "ENIT Energy Action Plan.pdf"),
    ]
    enit.kpi_values = {
        "ACA-01": 0.71,
        "ACA-06": 3.2,
        "EMP-01": 0.58,
        "HR-01": 0.06,
        "HR-04": 15,
        "RES-01": 7,
        "ESG-02": 0.09,
        "ESG-03": 0.28,
        "ESG-04": 0.22,
    }

    # --- ENSI — early stage -----------------------------------------------
    ensi.evidence = [
        _ev("ev-200", "ENSI", "ISO9001", "iso9001-5.1", "iso9001-5.1-t2", "TPLT_QUALITY_POLICY", "ENSI Quality Policy Draft.pdf", status=EvidenceStatus.PENDING),
        _ev("ev-201", "ENSI", "ISO9001", "iso9001-7.5", "iso9001-7.5-t1", "TPLT_DOC_CONTROL_PROCEDURE", "ENSI Doc Control.pdf"),
        _ev("ev-240", "ENSI", "GREENMETRIC", "gm-waste", "gm-waste-t2", "TPLT_WASTE_MANAGEMENT", "ENSI Waste Policy.pdf"),
    ]
    ensi.kpi_values = {
        "ACA-01": 0.65,
        "ACA-06": 2.9,
        "EMP-01": 0.45,
        "HR-01": 0.05,
        "HR-04": 10,
        "RES-01": 4,
        "ESG-02": 0.05,
        "ESG-03": 0.20,
        "ESG-04": 0.18,
    }

    # --- ISET — most advanced ---------------------------------------------
    iset.attestations = [_attestation("iso9001-5.1-t1", "ISET Director")]
    iset.evidence = [
        _ev("ev-300", "ISET", "ISO9001", "iso9001-4.1", "iso9001-4.1-t1", "TPLT_STRATEGIC_CONTEXT", "ISET Strategic Context.pdf"),
        _ev("ev-301", "ISET", "ISO9001", "iso9001-4.2", "iso9001-4.2-t1", "TPLT_STAKEHOLDER_REGISTER", "ISET Stakeholders 2026.pdf"),
        _ev("ev-303", "ISET", "ISO9001", "iso9001-5.1", "iso9001-5.1-t2", "TPLT_QUALITY_POLICY", "ISET Quality Policy 2026.pdf"),
        _ev("ev-304", "ISET", "ISO9001", "iso9001-6.1", "iso9001-6.1-t1", "TPLT_RISK_REGISTER", "ISET Risk Register.xlsx"),
        _ev("ev-305", "ISET", "ISO9001", "iso9001-7.1", "iso9001-7.1-t2", "TPLT_INFRA_INVENTORY", "ISET Infra Inventory 2026.pdf"),
        _ev("ev-306", "ISET", "ISO9001", "iso9001-7.5", "iso9001-7.5-t1", "TPLT_DOC_CONTROL_PROCEDURE", "ISET Doc Control Procedure.pdf"),
        _ev("ev-307", "ISET", "ISO9001", "iso9001-8.1", "iso9001-8.1-t1", "TPLT_OPS_PROCEDURES", "ISET Ops Manual 2026.pdf"),
        _ev("ev-308", "ISET", "ISO9001", "iso9001-9.1", "iso9001-9.1-t2", "TPLT_KPI_MONITORING_PLAN", "ISET KPI Plan 2026.pdf"),
        _ev("ev-309", "ISET", "ISO9001", "iso9001-9.2", "iso9001-9.2-t1", "TPLT_INTERNAL_AUDIT_REPORT", "ISET Internal Audit 2025.pdf"),
        _ev("ev-310", "ISET", "ISO9001", "iso9001-10.2", "iso9001-10.2-t1", "TPLT_CORRECTIVE_ACTION_LOG", "ISET Corrective Actions 2026.pdf"),
        _ev("ev-320", "ISET", "ISO21001", "iso21001-4.1", "iso21001-4.1-t1", "TPLT_EOMS_CONTEXT", "ISET EOMS Context.pdf"),
        _ev("ev-321", "ISET", "ISO21001", "iso21001-5.3", "iso21001-5.3-t2", "TPLT_LEARNER_FEEDBACK", "ISET Learner Feedback Process.pdf"),
        _ev("ev-322", "ISET", "ISO21001", "iso21001-6.1", "iso21001-6.1-t1", "TPLT_RISK_REGISTER", "ISET Educational Risk Register.pdf"),
        _ev("ev-323", "ISET", "ISO21001", "iso21001-7.2", "iso21001-7.2-t2", "TPLT_PD_PLAN", "ISET Faculty PD Plan 2026.pdf"),
        _ev("ev-324", "ISET", "ISO21001", "iso21001-7.5", "iso21001-7.5-t1", "TPLT_DOC_CONTROL_PROCEDURE", "ISET EOMS Doc Control.pdf"),
        _ev("ev-325", "ISET", "ISO21001", "iso21001-8.3", "iso21001-8.3-t1", "TPLT_CURRICULUM_DESIGN", "ISET Curriculum Design.pdf"),
        _ev("ev-326", "ISET", "ISO21001", "iso21001-9.2", "iso21001-9.2-t1", "TPLT_INTERNAL_AUDIT_REPORT", "ISET EOMS Audit 2025.pdf"),
        _ev("ev-340", "ISET", "GREENMETRIC", "gm-setting", "gm-setting-t1", "TPLT_CAMPUS_SUSTAINABILITY", "ISET Campus Report 2025.pdf"),
        _ev("ev-341", "ISET", "GREENMETRIC", "gm-energy", "gm-energy-t2", "TPLT_ENERGY_PLAN", "ISET Energy Plan 2026.pdf"),
        _ev("ev-342", "ISET", "GREENMETRIC", "gm-waste", "gm-waste-t2", "TPLT_WASTE_MANAGEMENT", "ISET Waste Management.pdf"),
        _ev("ev-343", "ISET", "GREENMETRIC", "gm-water", "gm-water-t1", "TPLT_WATER_CONSERVATION", "ISET Water Conservation.pdf"),
        _ev("ev-344", "ISET", "GREENMETRIC", "gm-transport", "gm-transport-t1", "TPLT_TRANSPORT_POLICY", "ISET Green Transport Policy.pdf"),
        _ev("ev-345", "ISET", "GREENMETRIC", "gm-education", "gm-education-t2", "TPLT_SUSTAINABILITY_PROGRAM", "ISET Sustainability Program.pdf"),
    ]
    iset.kpi_values = {
        "ACA-01": 0.82,
        "ACA-06": 4.1,
        "EMP-01": 0.78,
        "HR-01": 0.09,
        "HR-04": 35,
        "RES-01": 18,
        "ESG-02": 0.22,
        "ESG-03": 0.55,
        "ESG-04": 0.40,
    }

    return {inst.code: inst for inst in (insat, enit, ensi, iset)}


# Module-level mutable state for the demo.
_STATE: dict[str, _InstitutionDemo] = _seed_institutions()


# ---------------------------------------------------------------------------
# Public read API
# ---------------------------------------------------------------------------


def list_institutions() -> list[str]:
    return list(_STATE.keys())


def get_institution(code: str) -> _InstitutionDemo | None:
    return _STATE.get(code.upper())


def evidence_for(institution: str, *, framework: str | None = None) -> list[EvidenceRecord]:
    inst = _STATE.get(institution.upper())
    if inst is None:
        return []
    if framework is None:
        return list(inst.evidence)
    fw = framework.upper()
    return [e for e in inst.evidence if e.framework_code == fw]


def kpi_values_for(institution: str) -> dict[str, float | None]:
    inst = _STATE.get(institution.upper())
    return dict(inst.kpi_values) if inst else {}


def build_inputs(
    institution: str,
    *,
    period_start: date = DEMO_PERIOD_START,
    period_end: date = DEMO_PERIOD_END,
) -> InstitutionAccreditationInputs | None:
    """Translate the demo state into engine-ready typed inputs.

    Only APPROVED evidence becomes ApprovedDocument rows — pending /
    rejected items are visible via `evidence_for()` but don't satisfy
    any control test.
    """
    inst = _STATE.get(institution.upper())
    if inst is None:
        return None
    approved_docs = [
        ApprovedDocument(
            document_id=e.evidence_id,
            template_code=e.template_code or "",
            approved_at=e.approved_at.date() if e.approved_at else None,
            period_year=e.period_year,
        )
        for e in inst.evidence
        if e.status == EvidenceStatus.APPROVED and e.template_code
    ]
    return InstitutionAccreditationInputs(
        institution_id=inst.code,
        institution_code=inst.code,
        period_start=period_start,
        period_end=period_end,
        frameworks=all_frameworks(),
        kpi_values=dict(inst.kpi_values),
        approved_documents=approved_docs,
        attestations=list(inst.attestations),
    )


# ---------------------------------------------------------------------------
# Mutation helpers (demo "approve evidence" flow)
# ---------------------------------------------------------------------------


def submit_evidence(
    institution: str,
    framework: str,
    control_id: str,
    test_id: str,
    *,
    template_code: str | None = None,
    doc_name: str = "Uploaded Document",
    auto_approve: bool = True,
) -> EvidenceRecord | None:
    inst = _STATE.get(institution.upper())
    if inst is None:
        return None
    record = EvidenceRecord(
        evidence_id=f"ev-demo-{uuid.uuid4().hex[:8]}",
        institution_code=institution.upper(),
        framework_code=framework.upper(),
        control_id=control_id,
        test_id=test_id,
        template_code=template_code,
        doc_name=doc_name,
        period_year=DEMO_PERIOD_YEAR,
        status=EvidenceStatus.APPROVED if auto_approve else EvidenceStatus.PENDING,
        submitted_at=datetime.utcnow(),
        approved_at=datetime.utcnow() if auto_approve else None,
        notes="Auto-approved via demo endpoint" if auto_approve else None,
    )
    inst.evidence.append(record)
    return record


def submit_attestation(
    institution: str,
    test_id: str,
    *,
    attested_by: str = "Director (demo)",
) -> Attestation | None:
    inst = _STATE.get(institution.upper())
    if inst is None:
        return None
    inst.attestations = [a for a in inst.attestations if a.test_id != test_id]
    record = Attestation(
        test_id=test_id,
        attested_by=attested_by,
        attestation_text="Submitted via demo portal.",
        attested_at=date.today(),
        is_active=True,
    )
    inst.attestations.append(record)
    return record


def reset() -> None:
    """Restore all institutions to seeded state. Useful for demo restarts."""
    global _STATE
    _STATE = _seed_institutions()
