"""Unit tests for Domain F (Human Resources) KPI calculators."""

from __future__ import annotations

from datetime import date

import pytest

from backend.services.kpi_service.domain import (
    AdminStaff,
    FacultyMember,
    InstitutionHrInputs,
    Student,
    StudentStatus,
    VacancyEvent,
    compute_hr_domain,
)
from backend.services.kpi_service.domain.hr import (
    hr_01_workload_compliance,
    hr_02_teaching_load_balance,
    hr_03_professor_per_student,
    hr_04_admin_per_student,
    hr_05_faculty_training_fulfillment,
    hr_06_staff_absenteeism,
    hr_07_vacancy_fill_time,
    hr_08_permanent_faculty_ratio,
    hr_09_faculty_expertise_match,
)

PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 12, 31)


def _inputs(**overrides) -> InstitutionHrInputs:
    base = dict(
        institution_id="i1",
        institution_code="INSAT",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
    )
    base.update(overrides)
    return InstitutionHrInputs(**base)


class TestHr01WorkloadCompliance:
    def test_within_tolerance(self):
        faculty = [
            # 100 contracted, 90 delivered -> -10% (within +/-20)
            FacultyMember(id="1", full_name="A", contracted_hours=100, delivered_hours=90),
            # 100 contracted, 130 delivered -> +30% (outside)
            FacultyMember(id="2", full_name="B", contracted_hours=100, delivered_hours=130),
            # exactly contracted
            FacultyMember(id="3", full_name="C", contracted_hours=100, delivered_hours=100),
        ]
        result = hr_01_workload_compliance(_inputs(faculty=faculty))
        assert result.value == pytest.approx(200 / 3)

    def test_custom_tolerance(self):
        faculty = [
            FacultyMember(id="1", full_name="A", contracted_hours=100, delivered_hours=105),
        ]
        result = hr_01_workload_compliance(_inputs(faculty=faculty, workload_tolerance=0.01))
        assert result.value == 0.0  # 5% > 1%


class TestHr02TeachingLoadBalance:
    def test_pop_stdev(self):
        faculty = [
            FacultyMember(id="1", full_name="A", delivered_hours=100),
            FacultyMember(id="2", full_name="B", delivered_hours=120),
            FacultyMember(id="3", full_name="C", delivered_hours=80),
        ]
        result = hr_02_teaching_load_balance(_inputs(faculty=faculty))
        # population stdev of [100, 120, 80] = sqrt(800/3) ~= 16.33
        assert result.value == pytest.approx(16.3299, abs=0.01)

    def test_needs_two_values(self):
        faculty = [FacultyMember(id="1", full_name="A", delivered_hours=100)]
        result = hr_02_teaching_load_balance(_inputs(faculty=faculty))
        assert result.value is None


class TestHr03ProfessorPerStudent:
    def test_inverse_of_aca_01(self):
        faculty = [FacultyMember(id="f", full_name="F", fte_fraction=2.0)]
        students = [Student(id=f"s{i}", status=StudentStatus.ACTIVE) for i in range(20)]
        result = hr_03_professor_per_student(_inputs(faculty=faculty, students=students))
        assert result.value == pytest.approx(0.1)


class TestHr04AdminPerStudent:
    def test_basic(self):
        admin = [AdminStaff(id=f"a{i}", fte_fraction=1.0) for i in range(5)]
        students = [Student(id=f"s{i}", status=StudentStatus.ACTIVE) for i in range(100)]
        result = hr_04_admin_per_student(_inputs(admin_staff=admin, students=students))
        assert result.value == 0.05


class TestHr05TrainingFulfillment:
    def test_aggregate(self):
        faculty = [
            FacultyMember(id="1", full_name="A", training_hours_required=20, training_hours_completed=15),
            FacultyMember(id="2", full_name="B", training_hours_required=10, training_hours_completed=10),
        ]
        result = hr_05_faculty_training_fulfillment(_inputs(faculty=faculty))
        # 25 / 30 = 83.33%
        assert result.value == pytest.approx(83.333, abs=0.01)


class TestHr06StaffAbsenteeism:
    def test_aggregates_faculty_and_admin(self):
        faculty = [
            FacultyMember(id="f1", full_name="F1", scheduled_workdays=200, unexcused_absence_days=5),
        ]
        admin = [
            AdminStaff(id="a1", scheduled_workdays=200, unexcused_absence_days=15),
        ]
        result = hr_06_staff_absenteeism(_inputs(faculty=faculty, admin_staff=admin))
        # 20 / 400 = 5%
        assert result.value == 5.0


class TestHr07VacancyFillTime:
    def test_median_excludes_unfilled(self):
        events = [
            VacancyEvent(id="1", position_open_date=date(2026, 1, 1),
                         contract_signed_date=date(2026, 2, 1)),  # 31 days
            VacancyEvent(id="2", position_open_date=date(2026, 1, 1),
                         contract_signed_date=date(2026, 4, 1)),  # 90 days
            VacancyEvent(id="3", position_open_date=date(2026, 1, 1),
                         contract_signed_date=None),  # excluded
        ]
        result = hr_07_vacancy_fill_time(_inputs(vacancy_events=events))
        assert result.value == 60.5  # median of [31, 90]
        assert any("still open" in w for w in result.warnings)


class TestHr08PermanentRatio:
    def test_basic(self):
        faculty = [
            FacultyMember(id="1", full_name="A", is_permanent=True),
            FacultyMember(id="2", full_name="B", is_permanent=False),
            FacultyMember(id="3", full_name="C", is_permanent=True),
        ]
        result = hr_08_permanent_faculty_ratio(_inputs(faculty=faculty))
        assert result.value == pytest.approx(200 / 3)


class TestHr09ExpertiseMatch:
    def test_basic(self):
        faculty = [
            FacultyMember(id="1", full_name="A", expertise_matches_courses=True),
            FacultyMember(id="2", full_name="B", expertise_matches_courses=False),
        ]
        result = hr_09_faculty_expertise_match(_inputs(faculty=faculty))
        assert result.value == 50.0


def test_dispatcher_runs_all_nine():
    results = compute_hr_domain(_inputs())
    assert {r.kpi_id for r in results} == {f"HR-{i:02d}" for i in range(1, 10)}
