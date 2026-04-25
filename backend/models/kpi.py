"""KPI definitions, weight versions, records, institution scores."""


class KpiDefinition:
    """Catalog row in `ucar_global.kpi_definitions`."""


class KpiWeightVersion:
    """Audit-trail row in `ucar_global.kpi_weight_versions`."""


class KpiRecord:
    """Computed KPI value per tenant per period (TimescaleDB hypertable)."""


class InstitutionScore:
    """UCAR composite score + rank per period."""
