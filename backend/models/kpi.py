"""KPI persistence models.

For now only `KpiRecord` is materialised. KPI definitions live in-memory
(see `backend.services.kpi_service.domain.catalog`) - they're derived from
the calculator registries and don't need a separate seed migration.

`KpiWeightVersion` and `InstitutionScore` will be added when ranking lands.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import (
    Date,
    DateTime,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.shared.db.base import Base


class KpiRecord(Base):
    """One computed KPI value for one tenant in one period.

    Mirrors `KpiResult` from the domain layer. `is_complete` and
    `is_estimated` are NOT stored - they're derived from the source fields
    via the same property logic as `KpiResult`.
    """

    __tablename__ = "kpi_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    kpi_id: Mapped[str] = mapped_column(String(10), nullable=False)
    domain: Mapped[str] = mapped_column(String(20), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)

    value: Mapped[float | None] = mapped_column(Numeric(15, 4), nullable=True)
    missing_fields: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    warnings: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    inputs_used: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "kpi_id", "period_start", "period_end",
            name="uq_kpi_records_tenant_kpi_period",
        ),
        Index("ix_kpi_records_tenant_period_end", "tenant_id", "period_end"),
        Index("ix_kpi_records_tenant_domain_period", "tenant_id", "domain", "period_end"),
    )

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
