"""Pydantic request/response schemas for the KPI HTTP surface."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.services.kpi_service.domain.catalog import KpiDescriptor
from backend.services.kpi_service.domain.result import KpiResult


class KpiDefinitionRead(BaseModel):
    kpi_id: str
    name: str
    domain: str
    formula: str
    unit: str

    @classmethod
    def from_descriptor(cls, d: KpiDescriptor) -> KpiDefinitionRead:
        return cls(
            kpi_id=d.kpi_id, name=d.name, domain=d.domain,
            formula=d.formula, unit=d.unit,
        )


class KpiRecordRead(BaseModel):
    """One persisted KpiRecord, joined against its catalog descriptor.

    `is_complete` and `is_estimated` are derived (matching the KpiResult
    property semantics) so the dashboard never has to recompute them.
    """

    model_config = ConfigDict(from_attributes=True)

    kpi_id: str
    name: str
    domain: str
    formula: str
    unit: str
    period_start: date
    period_end: date
    value: float | None
    is_complete: bool
    is_estimated: bool
    missing_fields: list[str]
    warnings: list[str]
    inputs_used: dict[str, Any]
    computed_at: datetime

    @classmethod
    def from_orm_with_descriptor(
        cls, record: Any, descriptor: KpiDescriptor
    ) -> KpiRecordRead:
        return cls(
            kpi_id=record.kpi_id,
            name=descriptor.name,
            domain=record.domain,
            formula=descriptor.formula,
            unit=descriptor.unit,
            period_start=record.period_start,
            period_end=record.period_end,
            value=float(record.value) if record.value is not None else None,
            is_complete=record.is_complete,
            is_estimated=record.is_estimated,
            missing_fields=list(record.missing_fields or []),
            warnings=list(record.warnings or []),
            inputs_used=dict(record.inputs_used or {}),
            computed_at=record.computed_at,
        )


class KpiTrendPoint(BaseModel):
    period_start: date
    period_end: date
    value: float | None
    is_complete: bool


class KpiTrendRead(BaseModel):
    kpi_id: str
    name: str
    domain: str
    unit: str
    points: list[KpiTrendPoint]


class KpiRecomputeRequest(BaseModel):
    period_start: date
    period_end: date


class KpiRecomputeResponse(BaseModel):
    tenant_id: UUID
    period_start: date
    period_end: date
    records_computed: int = Field(description="Total KpiRecord rows upserted")
    complete: int = Field(description="value present, no missing/warnings")
    estimated: int = Field(description="value present but warnings/missing")
    uncomputable: int = Field(description="value=None, blocked by missing data")


def kpi_result_to_record_kwargs(
    result: KpiResult,
    *,
    tenant_id: UUID,
) -> dict[str, Any]:
    """Translate a KpiResult into kwargs for KpiRecord(...) / upsert."""
    return {
        "tenant_id": tenant_id,
        "kpi_id": result.kpi_id,
        "domain": result.domain,
        "period_start": result.period_start,
        "period_end": result.period_end,
        "value": result.value,
        "missing_fields": result.missing_fields,
        "warnings": result.warnings,
        "inputs_used": result.inputs_used,
    }
