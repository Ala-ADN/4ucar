"""Domain H - Accreditation & Compliance evaluator.

Implements the Vanta/Drata-style framework -> control -> test -> evidence
model from .claude/accreditation.md. Pure functions over typed inputs;
no DB, no I/O. The result type is `ControlEvaluation`, NOT `KpiResult` -
this domain is qualitative (PASSING/FAILING/NEEDS_EVIDENCE/NOT_APPLICABLE),
not numeric.

The evaluator never recomputes a KPI. Domains A-G compute KPI values; the
caller flattens those into `inputs.kpi_values` (kpi_id -> float | None) and
the AUTOMATED_KPI tests look them up. The same lookup pattern works for
documents (template_code -> approved doc on file) and attestations.

Status decision tree (per accreditation.md s7):
    1. Waived for this control                  -> NOT_APPLICABLE
    2. requires_external_survey AND no evidence -> NOT_APPLICABLE
    3. all required tests pass                  -> PASSING
    4. no evidence of any kind exists yet       -> NEEDS_EVIDENCE
    5. otherwise                                -> FAILING
"""

from __future__ import annotations

import operator
from collections.abc import Callable
from datetime import date, timedelta
from typing import Any

from .inputs import (
    ApprovedDocument,
    Attestation,
    ControlTest,
    ControlWaiver,
    Framework,
    FrameworkControl,
    InstitutionAccreditationInputs,
    TestPeriodScope,
    TestType,
)
from .result import ControlEvaluation, ControlStatus

DOMAIN = "ACCREDITATION"


# Threshold comparators -----------------------------------------------------

_COMPARATORS: dict[str, Callable[[Any, Any], bool]] = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
}


# ---------------------------------------------------------------------------
# Period filtering for documents
# ---------------------------------------------------------------------------


def _document_in_scope(
    doc: ApprovedDocument,
    *,
    period_start: date,
    period_end: date,
    scope: TestPeriodScope,
) -> bool:
    """A document satisfies a test only when its approval/period falls in scope.

    Falls back to `approved_at` when `period_year` is unset.
    """
    if scope == TestPeriodScope.ROLLING_3Y:
        cutoff = period_end - timedelta(days=365 * 3)
        if doc.approved_at:
            return cutoff <= doc.approved_at <= period_end
        if doc.period_year is not None:
            return period_end.year - 2 <= doc.period_year <= period_end.year
        return False

    if scope == TestPeriodScope.CURRENT_YEAR:
        if doc.period_year is not None:
            return doc.period_year == period_end.year
        if doc.approved_at:
            return doc.approved_at.year == period_end.year
        return False

    if scope == TestPeriodScope.CURRENT_SEMESTER:
        # Treat the period as the semester window itself.
        if doc.approved_at:
            return period_start <= doc.approved_at <= period_end
        if doc.period_year is not None:
            return doc.period_year == period_end.year
        return False

    return False


# ---------------------------------------------------------------------------
# Per-test evaluation
# ---------------------------------------------------------------------------


def _evaluate_kpi_test(
    test: ControlTest, inputs: InstitutionAccreditationInputs
) -> tuple[bool, dict | None]:
    """Returns (passed, missing_evidence_entry_or_None)."""
    if test.kpi_id is None or test.threshold is None:
        return False, {
            "kpi_id": test.kpi_id,
            "description": "test misconfigured: kpi_id or threshold missing",
        }
    value = inputs.kpi_values.get(test.kpi_id)
    if value is None:
        return False, {
            "kpi_id": test.kpi_id,
            "description": f"No KPI record on file for {test.kpi_id} in period",
        }
    cmp = _COMPARATORS.get(test.threshold_comparator, operator.ge)
    if cmp(value, test.threshold):
        return True, None
    return False, {
        "kpi_id": test.kpi_id,
        "description": (
            f"{test.kpi_id} = {value} {test.threshold_comparator} "
            f"{test.threshold} required"
        ),
    }


def _evaluate_document_test(
    test: ControlTest, in_scope: list[ApprovedDocument]
) -> tuple[bool, list[dict]]:
    """Returns (passed, list_of_missing_template_descriptors).

    `in_scope` is the pre-filtered list of approved documents within the
    test's period_scope - the caller computes it once and reuses for both
    the evidence-seen check and the count check.
    """
    required = test.required_template_codes or []
    if not required:
        return False, [{"name": "(no required_template_codes set)", "test_id": test.id}]

    missing: list[dict] = []
    satisfied = 0
    for tpl in required:
        count = sum(1 for d in in_scope if d.template_code == tpl)
        if count >= test.required_document_count:
            satisfied += 1
        else:
            missing.append(
                {
                    "name": tpl,
                    "needed": test.required_document_count,
                    "have": count,
                }
            )

    return satisfied == len(required), missing


# ---------------------------------------------------------------------------
# Per-control evaluation
# ---------------------------------------------------------------------------


def evaluate_control(
    inputs: InstitutionAccreditationInputs,
    framework: Framework,
    control: FrameworkControl,
    *,
    waivers_by_control: dict[str, ControlWaiver] | None = None,
    active_attestation_test_ids: set[str] | None = None,
) -> ControlEvaluation:
    """Evaluate one control to its current status.

    `waivers_by_control` and `active_attestation_test_ids` are precomputed
    indexes the dispatcher passes in to avoid O(controls * waivers) and
    O(tests * attestations) scans. When called directly (e.g. from tests),
    they are derived lazily from `inputs`.
    """
    if waivers_by_control is None:
        waivers_by_control = {w.control_id: w for w in inputs.waivers}
    if active_attestation_test_ids is None:
        active_attestation_test_ids = {
            a.test_id for a in inputs.attestations if a.is_active
        }

    base = ControlEvaluation(
        framework_code=framework.code,
        control_code=control.code,
        name=control.name,
        weight=control.weight,
        status=ControlStatus.NEEDS_EVIDENCE,
        period_start=inputs.period_start,
        period_end=inputs.period_end,
    )

    # 1. Explicit waiver wins.
    waiver = waivers_by_control.get(control.id)
    if waiver is not None:
        base.status = ControlStatus.NOT_APPLICABLE
        base.not_applicable_reason = waiver.reason
        return base

    missing_templates: list[dict] = []
    missing_kpi: list[dict] = []
    any_evidence_seen = False
    required_tests = [t for t in control.tests if t.is_required]

    for test in required_tests:
        if test.test_type == TestType.AUTOMATED_KPI:
            value = inputs.kpi_values.get(test.kpi_id) if test.kpi_id else None
            if value is not None:
                any_evidence_seen = True
            passed, miss = _evaluate_kpi_test(test, inputs)
            if passed:
                base.passing_test_ids.append(test.id)
            else:
                base.failing_test_ids.append(test.id)
                if miss:
                    missing_kpi.append(miss)

        elif test.test_type == TestType.DOCUMENT_UPLOAD:
            # Filter approved docs to this test's period scope ONCE - reused
            # for both the evidence-seen check and the per-template count.
            in_scope = [
                d
                for d in inputs.approved_documents
                if _document_in_scope(
                    d,
                    period_start=inputs.period_start,
                    period_end=inputs.period_end,
                    scope=test.period_scope,
                )
            ]
            templates = set(test.required_template_codes or [])
            if any(d.template_code in templates for d in in_scope):
                any_evidence_seen = True
            passed, miss = _evaluate_document_test(test, in_scope)
            if passed:
                base.passing_test_ids.append(test.id)
            else:
                base.failing_test_ids.append(test.id)
                missing_templates.extend(miss)

        elif test.test_type == TestType.ATTESTATION:
            if test.id in active_attestation_test_ids:
                any_evidence_seen = True
                base.passing_test_ids.append(test.id)
            else:
                base.failing_test_ids.append(test.id)
                missing_kpi.append({
                    "kpi_id": None,
                    "description": f"attestation required for test {test.id}",
                })

    base.missing_evidence = {
        "templates_needed": missing_templates,
        "kpi_inputs_needed": missing_kpi,
    }

    # 2. Survey-based control with no evidence -> NOT_APPLICABLE per spec s2.2.
    if control.requires_external_survey and not any_evidence_seen:
        base.status = ControlStatus.NOT_APPLICABLE
        base.not_applicable_reason = (
            "external survey not yet conducted (requires_external_survey=True)"
        )
        return base

    # 3. All required tests pass (and there is at least one).
    if required_tests and not base.failing_test_ids:
        base.status = ControlStatus.PASSING
        return base

    # 4. No evidence anywhere yet -> pre-failing.
    if not any_evidence_seen:
        base.status = ControlStatus.NEEDS_EVIDENCE
        return base

    # 5. Some evidence exists but tests are failing.
    base.status = ControlStatus.FAILING
    return base


# ---------------------------------------------------------------------------
# Framework + dispatcher entrypoints
# ---------------------------------------------------------------------------


def evaluate_framework(
    inputs: InstitutionAccreditationInputs,
    framework: Framework,
    *,
    waivers_by_control: dict[str, ControlWaiver] | None = None,
    active_attestation_test_ids: set[str] | None = None,
) -> list[ControlEvaluation]:
    """Evaluate every control in one framework for one institution.

    Indexes are passed through to `evaluate_control`; if omitted, each
    control re-derives them. The dispatcher should always pass them.
    """
    return [
        evaluate_control(
            inputs, framework, c,
            waivers_by_control=waivers_by_control,
            active_attestation_test_ids=active_attestation_test_ids,
        )
        for c in framework.controls
    ]


def evaluate_accreditation(
    inputs: InstitutionAccreditationInputs,
) -> dict[str, list[ControlEvaluation]]:
    """Evaluate every active framework, keyed by framework code."""
    waivers_by_control = {w.control_id: w for w in inputs.waivers}
    active_attestation_test_ids = {
        a.test_id for a in inputs.attestations if a.is_active
    }
    return {
        f.code: evaluate_framework(
            inputs, f,
            waivers_by_control=waivers_by_control,
            active_attestation_test_ids=active_attestation_test_ids,
        )
        for f in inputs.frameworks
        if f.is_active
    }


# ---------------------------------------------------------------------------
# Aggregations consumers ask for repeatedly
# ---------------------------------------------------------------------------


def framework_completion_score(evaluations: list[ControlEvaluation]) -> float:
    """Weighted % of passing controls within a framework. NOT_APPLICABLE is
    excluded from both numerator and denominator (accreditation convention).
    """
    applicable = [e for e in evaluations if e.status != ControlStatus.NOT_APPLICABLE]
    if not applicable:
        return 0.0
    total_weight = sum(e.weight for e in applicable) or float(len(applicable))
    passing_weight = sum(
        e.weight if e.weight else 1.0
        for e in applicable
        if e.status == ControlStatus.PASSING
    )
    if total_weight == 0:
        return 0.0
    # Normalise: if weights all 0 we used count above for both sides.
    if not any(e.weight for e in applicable):
        return 100.0 * sum(
            1 for e in applicable if e.status == ControlStatus.PASSING
        ) / len(applicable)
    return 100.0 * passing_weight / total_weight


def gap_analysis(
    evaluations: list[ControlEvaluation],
) -> list[ControlEvaluation]:
    """Per accreditation.md s5.4: failing/needs-evidence controls sorted by
    impact (weight) descending. PASSING and NOT_APPLICABLE are dropped.
    """
    gaps = [
        e
        for e in evaluations
        if e.status in (ControlStatus.FAILING, ControlStatus.NEEDS_EVIDENCE)
    ]
    return sorted(gaps, key=lambda e: e.weight, reverse=True)
