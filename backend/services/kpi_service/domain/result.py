"""Result types returned by the KPI domain layer.

Two distinct shapes:

    KpiResult           - quantitative metric (Domains A-G). Carries a value
                          and explicit data-quality flags.
    ControlEvaluation   - qualitative compliance verdict (Domain H,
                          accreditation engine). Carries a status enum,
                          per-test breakdown, and missing-evidence summary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import StrEnum
from typing import Any


@dataclass
class KpiResult:
    kpi_id: str
    name: str
    domain: str
    formula: str
    period_start: date
    period_end: date
    unit: str

    value: float | None
    missing_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    inputs_used: dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        return (
            self.value is not None
            and not self.missing_fields
            and not self.warnings
        )

    @property
    def is_estimated(self) -> bool:
        return self.value is not None and not self.is_complete

    def to_dict(self) -> dict[str, Any]:
        return {
            "kpi_id": self.kpi_id,
            "name": self.name,
            "domain": self.domain,
            "formula": self.formula,
            "period": f"{self.period_start.isoformat()}..{self.period_end.isoformat()}",
            "unit": self.unit,
            "value": self.value,
            "is_complete": self.is_complete,
            "is_estimated": self.is_estimated,
            "missing_fields": self.missing_fields,
            "warnings": self.warnings,
            "inputs_used": self.inputs_used,
        }


def build_kpi_result(
    inputs: Any,
    domain: str,
    *,
    kpi_id: str,
    name: str,
    formula: str,
    unit: str,
    value: float | None,
    missing: list[str] | None = None,
    warnings: list[str] | None = None,
    used: dict[str, Any] | None = None,
) -> KpiResult:
    """Factory for KpiResult that pulls period bounds off any object with
    `period_start` / `period_end` attrs (every Institution*Inputs bundle).
    """
    return KpiResult(
        kpi_id=kpi_id,
        name=name,
        domain=domain,
        formula=formula,
        unit=unit,
        period_start=inputs.period_start,
        period_end=inputs.period_end,
        value=value,
        missing_fields=missing or [],
        warnings=warnings or [],
        inputs_used=used or {},
    )


class ControlStatus(StrEnum):
    """Per accreditation.md s2.5 - aligned with Vanta/Drata conventions."""

    PASSING = "PASSING"
    FAILING = "FAILING"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass
class ControlEvaluation:
    """One control's status for one institution + period.

    `missing_evidence` mirrors accreditation.md's JSONB schema:
        {"templates_needed": [...], "kpi_inputs_needed": [...]}
    so the dashboard can render exact upload CTAs without re-deriving.
    """

    framework_code: str
    control_code: str
    name: str
    weight: float
    status: ControlStatus
    period_start: date
    period_end: date
    passing_test_ids: list[str] = field(default_factory=list)
    failing_test_ids: list[str] = field(default_factory=list)
    missing_evidence: dict[str, list[Any]] = field(
        default_factory=lambda: {"templates_needed": [], "kpi_inputs_needed": []}
    )
    not_applicable_reason: str | None = None

    @property
    def total_required_tests(self) -> int:
        return len(self.passing_test_ids) + len(self.failing_test_ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "framework_code": self.framework_code,
            "control_code": self.control_code,
            "name": self.name,
            "weight": self.weight,
            "status": self.status.value,
            "period": f"{self.period_start.isoformat()}..{self.period_end.isoformat()}",
            "passing_tests": len(self.passing_test_ids),
            "total_required_tests": self.total_required_tests,
            "failing_test_ids": self.failing_test_ids,
            "missing_evidence": self.missing_evidence,
            "not_applicable_reason": self.not_applicable_reason,
        }
