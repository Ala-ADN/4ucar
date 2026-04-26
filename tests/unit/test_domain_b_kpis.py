"""Unit tests for Domain B (Academic Quality & Teaching) KPI calculators."""

from __future__ import annotations

from datetime import date

import pytest

from backend.services.kpi_service.domain import (
    FacultyMember,
    InstitutionAcademicInputs,
    Module,
    Program,
    Student,
    StudentStatus,
    compute_academic_domain,
)
from backend.services.kpi_service.domain.academic import (
    aca_01_student_faculty_ratio,
    aca_02_success_rate,
    aca_03_dropout_rate,
    aca_04_repetition_rate,
    aca_05_curriculum_coverage_rate,
    aca_06_faculty_with_phds,
    aca_07_double_degree_programs,
    aca_08_professional_certifications,
    aca_09_accredited_programs,
    aca_10_average_grade_performance,
    aca_11_absenteeism_rate,
    aca_12_remediation_rate,
)

PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 12, 31)


def _inputs(**overrides) -> InstitutionAcademicInputs:
    base = dict(
        institution_id="inst-1",
        institution_code="INSAT",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        faculty=[],
        students=[],
        modules=[],
        programs=[],
    )
    base.update(overrides)
    return InstitutionAcademicInputs(**base)


# ---------------------------------------------------------------------------
# ACA-01
# ---------------------------------------------------------------------------


class TestAca01StudentFacultyRatio:
    def test_basic(self):
        faculty = [FacultyMember(id=str(i), full_name=str(i)) for i in range(4)]
        students = [Student(id=str(i), status=StudentStatus.ACTIVE) for i in range(40)]
        result = aca_01_student_faculty_ratio(_inputs(faculty=faculty, students=students))
        assert result.value == 10.0
        assert result.is_complete

    def test_excludes_dropouts_and_graduated(self):
        faculty = [FacultyMember(id="f", full_name="F")]
        students = [
            Student(id="s1", status=StudentStatus.ACTIVE),
            Student(id="s2", status=StudentStatus.REPEATING),
            Student(id="s3", status=StudentStatus.DROPPED_OUT),
            Student(id="s4", status=StudentStatus.GRADUATED),
            Student(id="s5", status=StudentStatus.ON_LEAVE),
        ]
        result = aca_01_student_faculty_ratio(_inputs(faculty=faculty, students=students))
        assert result.value == 2.0  # ACTIVE + REPEATING

    def test_no_faculty(self):
        result = aca_01_student_faculty_ratio(
            _inputs(students=[Student(id="s", status=StudentStatus.ACTIVE)])
        )
        assert result.value is None
        assert "active_faculty_fte" in result.missing_fields


# ---------------------------------------------------------------------------
# ACA-02
# ---------------------------------------------------------------------------


class TestAca02SuccessRate:
    def test_pct(self):
        students = [
            Student(id="1", cohort_year=2024, passed_all_modules=True),
            Student(id="2", cohort_year=2024, passed_all_modules=False),
            Student(id="3", cohort_year=2024, passed_all_modules=True),
            Student(id="4", cohort_year=2025, passed_all_modules=True),
        ]
        result = aca_02_success_rate(_inputs(students=students))
        assert result.value == 75.0
        assert result.inputs_used["per_cohort"]["2024"]["rate"] == pytest.approx(2 / 3)
        assert result.inputs_used["per_cohort"]["2025"]["rate"] == 1.0

    def test_no_verdict_data(self):
        result = aca_02_success_rate(_inputs(students=[Student(id="s")]))
        assert result.value is None
        assert "students.passed_all_modules" in result.missing_fields


# ---------------------------------------------------------------------------
# ACA-03
# ---------------------------------------------------------------------------


class TestAca03DropoutRate:
    def test_pct(self):
        students = [
            Student(id="1", cohort_year=2023, status=StudentStatus.GRADUATED),
            Student(id="2", cohort_year=2023, status=StudentStatus.DROPPED_OUT),
            Student(id="3", cohort_year=2023, status=StudentStatus.DROPPED_OUT),
            Student(id="4", cohort_year=2023, status=StudentStatus.ACTIVE),
        ]
        result = aca_03_dropout_rate(_inputs(students=students))
        assert result.value == 50.0
        assert result.inputs_used["per_cohort"]["2023"]["rate"] == 0.5


# ---------------------------------------------------------------------------
# ACA-04
# ---------------------------------------------------------------------------


class TestAca04RepetitionRate:
    def test_pct(self):
        students = [
            Student(id="1", status=StudentStatus.ACTIVE),
            Student(id="2", status=StudentStatus.ACTIVE),
            Student(id="3", status=StudentStatus.REPEATING),
            Student(id="4", status=StudentStatus.GRADUATED),  # not in denominator
        ]
        result = aca_04_repetition_rate(_inputs(students=students))
        assert result.value == pytest.approx(100 / 3)


# ---------------------------------------------------------------------------
# ACA-05
# ---------------------------------------------------------------------------


class TestAca05CurriculumCoverage:
    def test_mean_coverage(self):
        modules = [
            Module(id="1", code="A", name="A", required_hours=100, delivered_hours=90),
            Module(id="2", code="B", name="B", required_hours=50, delivered_hours=50),
        ]
        result = aca_05_curriculum_coverage_rate(_inputs(modules=modules))
        assert result.value == pytest.approx(95.0)

    def test_partial_data_warns(self):
        modules = [
            Module(id="1", code="A", name="A", required_hours=100, delivered_hours=80),
            Module(id="2", code="B", name="B", required_hours=None, delivered_hours=None),
        ]
        result = aca_05_curriculum_coverage_rate(_inputs(modules=modules))
        assert result.value == 80.0
        assert any("missing required/delivered" in w for w in result.warnings)
        assert not result.is_complete


# ---------------------------------------------------------------------------
# ACA-06
# ---------------------------------------------------------------------------


class TestAca06FacultyWithPhds:
    def test_pct(self):
        faculty = [
            FacultyMember(id="1", full_name="A", holds_phd=True),
            FacultyMember(id="2", full_name="B", holds_phd=True),
            FacultyMember(id="3", full_name="C", holds_phd=False),
            FacultyMember(id="4", full_name="D", holds_phd=False),
        ]
        result = aca_06_faculty_with_phds(_inputs(faculty=faculty))
        assert result.value == 50.0

    def test_missing_flag(self):
        faculty = [FacultyMember(id="1", full_name="A")]
        result = aca_06_faculty_with_phds(_inputs(faculty=faculty))
        assert result.value is None
        assert "faculty.holds_phd" in result.missing_fields


# ---------------------------------------------------------------------------
# ACA-07 / 08 / 09
# ---------------------------------------------------------------------------


class TestAca07DoubleDegree:
    def test_count(self):
        programs = [
            Program(id="1", name="A", double_degree_partner_country="FR"),
            Program(id="2", name="B", double_degree_partner_country=None),
            Program(id="3", name="C", double_degree_partner_country="DE", is_active=False),
        ]
        result = aca_07_double_degree_programs(_inputs(programs=programs))
        assert result.value == 1.0


class TestAca08ProfessionalCertifications:
    def test_pct(self):
        students = [
            Student(id="1", status=StudentStatus.ACTIVE, has_industry_certification=True),
            Student(id="2", status=StudentStatus.ACTIVE, has_industry_certification=False),
        ]
        result = aca_08_professional_certifications(_inputs(students=students))
        assert result.value == 50.0

    def test_only_counts_enrolled(self):
        students = [
            Student(id="1", status=StudentStatus.GRADUATED, has_industry_certification=True),
            Student(id="2", status=StudentStatus.ACTIVE, has_industry_certification=False),
        ]
        result = aca_08_professional_certifications(_inputs(students=students))
        assert result.value == 0.0


class TestAca09AccreditedPrograms:
    def test_pct(self):
        programs = [
            Program(id="1", name="A", has_external_accreditation=True),
            Program(id="2", name="B", has_external_accreditation=True),
            Program(id="3", name="C", has_external_accreditation=False),
        ]
        result = aca_09_accredited_programs(_inputs(programs=programs))
        assert result.value == pytest.approx(200 / 3)


# ---------------------------------------------------------------------------
# ACA-10
# ---------------------------------------------------------------------------


class TestAca10GpaIndex:
    def test_mean(self):
        students = [
            Student(id="1", gpa=3.5),
            Student(id="2", gpa=2.5),
            Student(id="3", gpa=4.0),
        ]
        result = aca_10_average_grade_performance(_inputs(students=students))
        assert result.value == pytest.approx(10 / 3)


# ---------------------------------------------------------------------------
# ACA-11
# ---------------------------------------------------------------------------


class TestAca11Absenteeism:
    def test_aggregate(self):
        modules = [
            Module(id="1", code="A", name="A", scheduled_class_hours=100, unexcused_absence_hours=10),
            Module(id="2", code="B", name="B", scheduled_class_hours=50, unexcused_absence_hours=5),
        ]
        result = aca_11_absenteeism_rate(_inputs(modules=modules))
        assert result.value == 10.0  # 15/150


# ---------------------------------------------------------------------------
# ACA-12
# ---------------------------------------------------------------------------


class TestAca12Remediation:
    def test_pct_of_at_risk_supported(self):
        students = [
            Student(id="1", is_at_risk=True, received_remediation_support=True),
            Student(id="2", is_at_risk=True, received_remediation_support=False),
            Student(id="3", is_at_risk=True, received_remediation_support=True),
            Student(id="4", is_at_risk=False),  # not in denominator
        ]
        result = aca_12_remediation_rate(_inputs(students=students))
        assert result.value == pytest.approx(200 / 3)

    def test_no_at_risk_returns_none_with_warning(self):
        students = [Student(id="1", is_at_risk=False)]
        result = aca_12_remediation_rate(_inputs(students=students))
        assert result.value is None
        assert any("at_risk" in w for w in result.warnings)

    def test_missing_support_flag(self):
        students = [Student(id="1", is_at_risk=True, received_remediation_support=None)]
        result = aca_12_remediation_rate(_inputs(students=students))
        assert result.value is None
        assert "students.received_remediation_support" in result.missing_fields


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def test_dispatcher_runs_all_twelve():
    results = compute_academic_domain(_inputs())
    assert {r.kpi_id for r in results} == {f"ACA-{i:02d}" for i in range(1, 13)}
    for r in results:
        if r.value is None:
            assert r.missing_fields, f"{r.kpi_id} returned None without missing_fields"


def test_realistic_insat_fixture():
    """A small but plausible INSAT fixture with mixed-quality data."""
    faculty = [
        FacultyMember(id=f"f{i}", full_name=f"F{i}", holds_phd=(i % 3 != 0))
        for i in range(15)
    ]
    students = [
        Student(
            id=f"s{i}",
            cohort_year=2024,
            status=StudentStatus.ACTIVE if i % 10 else StudentStatus.DROPPED_OUT,
            passed_all_modules=(i % 4 != 0),
            gpa=2.5 + (i % 5) * 0.3,
            has_industry_certification=(i % 3 == 0),
            is_at_risk=(i % 7 == 0),
            received_remediation_support=(i % 14 == 0),
        )
        for i in range(150)
    ]
    modules = [
        Module(
            id=f"m{i}",
            code=f"M{i}",
            name=f"Module {i}",
            required_hours=42,
            delivered_hours=40 + (i % 3),
            scheduled_class_hours=42 * 30,
            unexcused_absence_hours=20 + i,
        )
        for i in range(8)
    ]
    programs = [
        Program(id="p1", name="Networks", has_external_accreditation=True),
        Program(
            id="p2",
            name="Telecoms",
            has_external_accreditation=False,
            double_degree_partner_country="FR",
        ),
    ]
    inputs = _inputs(faculty=faculty, students=students, modules=modules, programs=programs)
    results = {r.kpi_id for r in compute_academic_domain(inputs)}
    assert results == {f"ACA-{i:02d}" for i in range(1, 13)}
