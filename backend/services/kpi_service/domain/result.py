"""KpiResult — the uniform return type for every KPI calculator.

The result carries *both* a value and an explicit data-quality verdict so
downstream consumers (dashboards, alert engine, audit reports) can render
"insufficient data" states without re-deriving them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
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
    is_complete: bool
    missing_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    inputs_used: dict[str, Any] = field(default_factory=dict)

    @property
    def is_estimated(self) -> bool:
        """True when value is non-None but partial data forced an approximation."""
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
