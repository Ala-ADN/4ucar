"""Unit tests for Domain G (Sustainability & ESG) KPI calculators."""

from __future__ import annotations

from datetime import date

import pytest

from backend.services.kpi_service.domain import (
    EnergyConsumption,
    Facility,
    FacultyMember,
    InstitutionEsgInputs,
    Publication,
    Student,
    StudentStatus,
    TransportSurveyResponse,
    WasteRecord,
    compute_esg_domain,
)
from backend.services.kpi_service.domain.sustainability import (
    esg_01_energy_per_student,
    esg_02_carbon_per_student,
    esg_03_renewable_energy_rate,
    esg_04_recycling_rate,
    esg_05_green_transportation_rate,
    esg_06_campus_accessibility,
    esg_07_gender_diversity,
    esg_08_sdg_aligned_research,
)

PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 12, 31)


def _inputs(**overrides) -> InstitutionEsgInputs:
    base = dict(
        institution_id="i1",
        institution_code="INSAT",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
    )
    base.update(overrides)
    return InstitutionEsgInputs(**base)


class TestEsg01EnergyPerStudent:
    def test_basic(self):
        records = [
            EnergyConsumption(id="e1", kwh_consumed=100_000),
            EnergyConsumption(id="e2", kwh_consumed=50_000),
        ]
        students = [Student(id=f"s{i}", status=StudentStatus.ACTIVE) for i in range(150)]
        result = esg_01_energy_per_student(_inputs(energy_consumption=records, students=students))
        assert result.value == 1000.0


class TestEsg02CarbonPerStudent:
    def test_basic(self):
        records = [EnergyConsumption(id="e1", co2e_kg=30_000)]
        students = [Student(id=f"s{i}", status=StudentStatus.ACTIVE) for i in range(100)]
        result = esg_02_carbon_per_student(_inputs(energy_consumption=records, students=students))
        assert result.value == 300.0


class TestEsg03RenewableRate:
    def test_basic(self):
        records = [
            EnergyConsumption(id="e1", kwh_consumed=70_000, is_renewable=False),
            EnergyConsumption(id="e2", kwh_consumed=30_000, is_renewable=True),
        ]
        result = esg_03_renewable_energy_rate(_inputs(energy_consumption=records))
        assert result.value == 30.0


class TestEsg04RecyclingRate:
    def test_basic(self):
        records = [WasteRecord(id="w1", waste_total_kg=1000, waste_recycled_kg=400)]
        result = esg_04_recycling_rate(_inputs(waste_records=records))
        assert result.value == 40.0


class TestEsg05GreenTransport:
    def test_basic(self):
        responses = [
            TransportSurveyResponse(respondent_id="r1", uses_sustainable_transport=True),
            TransportSurveyResponse(respondent_id="r2", uses_sustainable_transport=False),
            TransportSurveyResponse(respondent_id="r3", uses_sustainable_transport=True),
            TransportSurveyResponse(respondent_id="r4", uses_sustainable_transport=True),
        ]
        result = esg_05_green_transportation_rate(_inputs(transport_responses=responses))
        assert result.value == 75.0


class TestEsg06Accessibility:
    def test_basic(self):
        facilities = [
            Facility(id="f1", is_accessibility_compliant=True),
            Facility(id="f2", is_accessibility_compliant=True),
            Facility(id="f3", is_accessibility_compliant=False),
            Facility(id="f4", is_accessibility_compliant=True),
        ]
        result = esg_06_campus_accessibility(_inputs(facilities=facilities))
        assert result.value == 75.0


class TestEsg07GenderDiversity:
    def test_basic(self):
        faculty = [
            FacultyMember(id="1", full_name="A", gender="F"),
            FacultyMember(id="2", full_name="B", gender="M"),
            FacultyMember(id="3", full_name="C", gender="F"),
            FacultyMember(id="4", full_name="D", gender="M"),
        ]
        result = esg_07_gender_diversity(_inputs(faculty=faculty))
        assert result.value == 50.0

    def test_handles_X_and_lowercase(self):
        faculty = [
            FacultyMember(id="1", full_name="A", gender="f"),  # lowercase ok
            FacultyMember(id="2", full_name="B", gender="X"),  # not female
        ]
        result = esg_07_gender_diversity(_inputs(faculty=faculty))
        assert result.value == 50.0


class TestEsg08SdgAligned:
    def test_basic(self):
        faculty = [
            FacultyMember(
                id="1", full_name="A",
                publications=[
                    Publication(title="P1", year=2024, sdg_aligned=True),
                    Publication(title="P2", year=2024, sdg_aligned=False),
                    Publication(title="P3", year=2024, sdg_aligned=True),
                ],
            ),
        ]
        result = esg_08_sdg_aligned_research(_inputs(faculty=faculty))
        assert result.value == pytest.approx(200 / 3)

    def test_no_flag(self):
        faculty = [
            FacultyMember(id="1", full_name="A",
                          publications=[Publication(title="P1", year=2024)])
        ]
        result = esg_08_sdg_aligned_research(_inputs(faculty=faculty))
        assert result.value is None
        assert "publications.sdg_aligned" in result.missing_fields


def test_dispatcher_runs_all_eight():
    results = compute_esg_domain(_inputs())
    assert {r.kpi_id for r in results} == {f"ESG-{i:02d}" for i in range(1, 9)}
