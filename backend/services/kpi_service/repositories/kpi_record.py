"""KpiRecord repository - all DB access for the kpi_records table.

Upserts use Postgres ON CONFLICT against the
`uq_kpi_records_tenant_kpi_period` constraint, so re-running recompute
for the same period overwrites in place rather than accumulating
duplicates.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.kpi import KpiRecord


class KpiRecordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_many(self, records_kwargs: Sequence[dict[str, Any]]) -> int:
        """Insert-or-update many records in one statement.

        On conflict against (tenant_id, kpi_id, period_start, period_end)
        we overwrite the value/missing/warnings/inputs_used/computed_at/
        domain fields. Returns the row count submitted.
        """
        if not records_kwargs:
            return 0

        now = datetime.now(timezone.utc)
        rows = [{**kw, "computed_at": now} for kw in records_kwargs]

        stmt = pg_insert(KpiRecord).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_kpi_records_tenant_kpi_period",
            set_={
                "value": stmt.excluded.value,
                "missing_fields": stmt.excluded.missing_fields,
                "warnings": stmt.excluded.warnings,
                "inputs_used": stmt.excluded.inputs_used,
                "computed_at": stmt.excluded.computed_at,
                "domain": stmt.excluded.domain,
            },
        )
        await self.session.execute(stmt)
        return len(rows)

    async def list_for_tenant(
        self,
        tenant_id: UUID,
        *,
        domain: str | None = None,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> list[KpiRecord]:
        stmt = select(KpiRecord).where(KpiRecord.tenant_id == tenant_id)
        if domain:
            stmt = stmt.where(KpiRecord.domain == domain.upper())
        if period_start is not None:
            stmt = stmt.where(KpiRecord.period_start >= period_start)
        if period_end is not None:
            stmt = stmt.where(KpiRecord.period_end <= period_end)
        stmt = stmt.order_by(KpiRecord.kpi_id, KpiRecord.period_end.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_trend(
        self,
        tenant_id: UUID,
        kpi_id: str,
        *,
        limit: int = 12,
    ) -> list[KpiRecord]:
        """Most recent N records for one KPI, returned oldest-first for charting."""
        stmt = (
            select(KpiRecord)
            .where(KpiRecord.tenant_id == tenant_id, KpiRecord.kpi_id == kpi_id)
            .order_by(KpiRecord.period_end.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(reversed(result.scalars().all()))
