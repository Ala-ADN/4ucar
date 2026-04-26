"""Domain G - Sustainability & ESG KPI calculators (ESG-01..ESG-08).

ESG-07 uses faculty.gender ("F" counts as female; everything else - including
None - is excluded from the denominator). ESG-08 reads `sdg_aligned` off
`faculty[*].publications`.
"""

from __future__ import annotations

from collections.abc import Callable

from .inputs import (
    InstitutionEsgInputs,
    currently_enrolled,
)
from .result import KpiResult, build_kpi_result

DOMAIN = "ESG"


def _result(*, inputs: InstitutionEsgInputs, **kw) -> KpiResult:
    return build_kpi_result(inputs, DOMAIN, **kw)


def _per_student_kpi(
    inputs: InstitutionEsgInputs,
    *,
    kpi_id: str,
    name: str,
    formula: str,
    unit: str,
    field_attr: str,
    list_attr: str = "energy_consumption",
) -> KpiResult:
    """Shared shape for ESG-01 (kWh/student) and ESG-02 (CO2e/student)."""
    records = getattr(inputs, list_attr)
    classified = [r for r in records if getattr(r, field_attr) is not None]
    enrolled = currently_enrolled(inputs.students)
    missing: list[str] = []
    warnings: list[str] = []

    if not records:
        missing.append(list_attr)
    if records and not classified:
        missing.append(f"{list_attr}.{field_attr}")
    if classified and len(classified) < len(records):
        warnings.append(
            f"{len(records) - len(classified)}/{len(records)} records missing {field_attr}"
        )
    if not enrolled:
        if not inputs.students:
            missing.append("students")
        else:
            missing.append("students.status (enrolled denominator empty)")

    if not classified or not enrolled:
        return _result(
            kpi_id=kpi_id,
            name=name,
            formula=formula,
            unit=unit,
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"records_with_data": len(classified), "enrolled": len(enrolled)},
        )

    total = sum(getattr(r, field_attr) or 0.0 for r in classified)
    value = total / len(enrolled)
    return _result(
        kpi_id=kpi_id,
        name=name,
        formula=formula,
        unit=unit,
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "records_with_data": len(classified),
            "total": total,
            "enrolled": len(enrolled),
        },
    )


# ---------------------------------------------------------------------------
# ESG-01 Energy Consumption per Student
# ---------------------------------------------------------------------------


def esg_01_energy_per_student(inputs: InstitutionEsgInputs) -> KpiResult:
    return _per_student_kpi(
        inputs,
        kpi_id="ESG-01",
        name="Energy Consumption per Student",
        formula="sum(energy_consumption.kwh_consumed) / count(currently enrolled)",
        unit="kWh/student",
        field_attr="kwh_consumed",
    )


# ---------------------------------------------------------------------------
# ESG-02 Carbon Footprint per Student
# ---------------------------------------------------------------------------


def esg_02_carbon_per_student(inputs: InstitutionEsgInputs) -> KpiResult:
    return _per_student_kpi(
        inputs,
        kpi_id="ESG-02",
        name="Carbon Footprint per Student",
        formula="sum(energy_consumption.co2e_kg) / count(currently enrolled)",
        unit="kgCO2e/student",
        field_attr="co2e_kg",
    )


# ---------------------------------------------------------------------------
# ESG-03 Renewable Energy Rate
# ---------------------------------------------------------------------------


def esg_03_renewable_energy_rate(inputs: InstitutionEsgInputs) -> KpiResult:
    records = inputs.energy_consumption
    classified = [r for r in records if r.kwh_consumed is not None and r.is_renewable is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not records:
        missing.append("energy_consumption")
    if records and not classified:
        missing.append("energy_consumption.kwh_consumed / energy_consumption.is_renewable")
    if classified and len(classified) < len(records):
        warnings.append(
            f"{len(records) - len(classified)}/{len(records)} energy records "
            "missing kwh or is_renewable"
        )

    if not classified:
        return _result(
            kpi_id="ESG-03",
            name="Renewable Energy Rate",
            formula="100 * sum(kwh where is_renewable=True) / sum(kwh)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"records_with_data": 0},
        )

    total = sum(r.kwh_consumed or 0.0 for r in classified)
    if total == 0:
        return _result(
            kpi_id="ESG-03",
            name="Renewable Energy Rate",
            formula="100 * sum(kwh where is_renewable=True) / sum(kwh)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=["energy_consumption.kwh_consumed (sum is zero)"],
            warnings=warnings,
            used={"records_with_data": len(classified)},
        )

    renewable = sum(r.kwh_consumed or 0.0 for r in classified if r.is_renewable)
    value = 100.0 * renewable / total
    return _result(
        kpi_id="ESG-03",
        name="Renewable Energy Rate",
        formula="100 * sum(kwh where is_renewable=True) / sum(kwh)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "records_with_data": len(classified),
            "total_kwh": total,
            "renewable_kwh": renewable,
        },
    )


# ---------------------------------------------------------------------------
# ESG-04 Recycling Rate
# ---------------------------------------------------------------------------


def esg_04_recycling_rate(inputs: InstitutionEsgInputs) -> KpiResult:
    records = inputs.waste_records
    classified = [
        r for r in records
        if r.waste_total_kg is not None and r.waste_recycled_kg is not None
    ]
    missing: list[str] = []
    warnings: list[str] = []

    if not records:
        missing.append("waste_records")
    if records and not classified:
        missing.append("waste_records.waste_total_kg / waste_records.waste_recycled_kg")
    if classified and len(classified) < len(records):
        warnings.append(
            f"{len(records) - len(classified)}/{len(records)} waste records missing fields"
        )

    if not classified:
        return _result(
            kpi_id="ESG-04",
            name="Recycling Rate",
            formula="100 * sum(waste_recycled_kg) / sum(waste_total_kg)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"records_with_data": 0},
        )

    total = sum(r.waste_total_kg or 0.0 for r in classified)
    recycled = sum(r.waste_recycled_kg or 0.0 for r in classified)
    if total == 0:
        return _result(
            kpi_id="ESG-04",
            name="Recycling Rate",
            formula="100 * sum(waste_recycled_kg) / sum(waste_total_kg)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=["waste_records.waste_total_kg (sum is zero)"],
            warnings=warnings,
            used={"records_with_data": len(classified)},
        )

    value = 100.0 * recycled / total
    return _result(
        kpi_id="ESG-04",
        name="Recycling Rate",
        formula="100 * sum(waste_recycled_kg) / sum(waste_total_kg)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "records_with_data": len(classified),
            "total_kg": total,
            "recycled_kg": recycled,
        },
    )


# ---------------------------------------------------------------------------
# ESG-05 Green Transportation Rate
# ---------------------------------------------------------------------------


def esg_05_green_transportation_rate(inputs: InstitutionEsgInputs) -> KpiResult:
    responses = inputs.transport_responses
    classified = [r for r in responses if r.uses_sustainable_transport is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not responses:
        missing.append("transport_responses")
    if responses and not classified:
        missing.append("transport_responses.uses_sustainable_transport")
    if classified and len(classified) < len(responses):
        warnings.append(
            f"{len(responses) - len(classified)}/{len(responses)} responses missing flag"
        )

    if not classified:
        return _result(
            kpi_id="ESG-05",
            name="Green Transportation Rate",
            formula="100 * count(uses_sustainable_transport=True) / count(responses with flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"responses_with_flag": 0},
        )

    green = sum(1 for r in classified if r.uses_sustainable_transport)
    value = 100.0 * green / len(classified)
    return _result(
        kpi_id="ESG-05",
        name="Green Transportation Rate",
        formula="100 * count(uses_sustainable_transport=True) / count(responses with flag)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={"responses_with_flag": len(classified), "green": green},
    )


# ---------------------------------------------------------------------------
# ESG-06 Campus Accessibility Score
# ---------------------------------------------------------------------------


def esg_06_campus_accessibility(inputs: InstitutionEsgInputs) -> KpiResult:
    facilities = inputs.facilities
    classified = [f for f in facilities if f.is_accessibility_compliant is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not facilities:
        missing.append("facilities")
    if facilities and not classified:
        missing.append("facilities.is_accessibility_compliant")
    if classified and len(classified) < len(facilities):
        warnings.append(
            f"{len(facilities) - len(classified)}/{len(facilities)} facilities missing flag"
        )

    if not classified:
        return _result(
            kpi_id="ESG-06",
            name="Campus Accessibility Score",
            formula="100 * count(facilities.is_accessibility_compliant=True) / count(with flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"facilities_with_flag": 0},
        )

    compliant = sum(1 for f in classified if f.is_accessibility_compliant)
    value = 100.0 * compliant / len(classified)
    return _result(
        kpi_id="ESG-06",
        name="Campus Accessibility Score",
        formula="100 * count(facilities.is_accessibility_compliant=True) / count(with flag)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={"facilities_with_flag": len(classified), "compliant": compliant},
    )


# ---------------------------------------------------------------------------
# ESG-07 Gender Diversity Index (% female faculty)
# ---------------------------------------------------------------------------


def esg_07_gender_diversity(inputs: InstitutionEsgInputs) -> KpiResult:
    active = [f for f in inputs.faculty if f.is_active]
    classified = [f for f in active if f.gender is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not active:
        missing.append("active_faculty")
    if active and not classified:
        missing.append("faculty.gender")
    if classified and len(classified) < len(active):
        warnings.append(
            f"{len(active) - len(classified)}/{len(active)} active faculty missing gender"
        )

    if not classified:
        return _result(
            kpi_id="ESG-07",
            name="Gender Diversity Index",
            formula='100 * count(faculty.gender="F") / count(active faculty with gender)',
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"classified": 0},
        )

    female = sum(1 for f in classified if (f.gender or "").upper() == "F")
    value = 100.0 * female / len(classified)
    return _result(
        kpi_id="ESG-07",
        name="Gender Diversity Index",
        formula='100 * count(faculty.gender="F") / count(active faculty with gender)',
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={"classified": len(classified), "female": female},
    )


# ---------------------------------------------------------------------------
# ESG-08 SDG-Aligned Research Rate
# ---------------------------------------------------------------------------


def esg_08_sdg_aligned_research(inputs: InstitutionEsgInputs) -> KpiResult:
    pubs = [p for f in inputs.faculty if f.is_active for p in f.publications]
    classified = [p for p in pubs if p.sdg_aligned is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not pubs:
        missing.append("faculty[*].publications")
    if pubs and not classified:
        missing.append("publications.sdg_aligned")
    if classified and len(classified) < len(pubs):
        warnings.append(
            f"{len(pubs) - len(classified)}/{len(pubs)} publications missing sdg_aligned"
        )

    if not classified:
        return _result(
            kpi_id="ESG-08",
            name="SDG-Aligned Research Rate",
            formula="100 * count(publications.sdg_aligned=True) / count(publications with flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"publications_with_flag": 0},
        )

    aligned = sum(1 for p in classified if p.sdg_aligned)
    value = 100.0 * aligned / len(classified)
    return _result(
        kpi_id="ESG-08",
        name="SDG-Aligned Research Rate",
        formula="100 * count(publications.sdg_aligned=True) / count(publications with flag)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={"publications_with_flag": len(classified), "sdg_aligned": aligned},
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

DOMAIN_G_CALCULATORS: list[Callable[[InstitutionEsgInputs], KpiResult]] = [
    esg_01_energy_per_student,
    esg_02_carbon_per_student,
    esg_03_renewable_energy_rate,
    esg_04_recycling_rate,
    esg_05_green_transportation_rate,
    esg_06_campus_accessibility,
    esg_07_gender_diversity,
    esg_08_sdg_aligned_research,
]
