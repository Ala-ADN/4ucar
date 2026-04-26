"""Unit tests for Domain D (Internationalization) KPI calculators."""

from __future__ import annotations

from datetime import date

import pytest

from backend.services.kpi_service.domain import (
    AcademicPartnership,
    FacultyMember,
    InstitutionInternationalInputs,
    Program,
    Student,
    StudentStatus,
    compute_international_domain,
)
from backend.services.kpi_service.domain.international import (
    int_01_international_faculty_ratio,
    int_02_international_student_ratio,
    int_03_outgoing_student_mobility,
    int_04_incoming_student_mobility,
    int_05_international_partnerships,
    int_06_foreign_language_program_rate,
)

PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 12, 31)


def _inputs(**overrides) -> InstitutionInternationalInputs:
    base = dict(
        institution_id="inst-1",
        institution_code="INSAT",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
    )
    base.update(overrides)
    return InstitutionInternationalInputs(**base)


# ---------------------------------------------------------------------------
# INT-01
# ---------------------------------------------------------------------------


class TestInt01InternationalFaculty:
    def test_either_signal_counts_as_international(self):
        faculty = [
            # Foreign nationality
            FacultyMember(id="1", full_name="A", nationality_country="FR",
                          highest_degree_country="TN"),
            # Foreign degree
            FacultyMember(id="2", full_name="B", nationality_country="TN",
                          highest_degree_country="DE"),
            # Both local
            FacultyMember(id="3", full_name="C", nationality_country="TN",
                          highest_degree_country="TN"),
        ]
        result = int_01_international_faculty_ratio(_inputs(faculty=faculty))
        assert result.value == pytest.approx(200 / 3)

    def test_partial_signal_warning(self):
        faculty = [
            FacultyMember(id="1", full_name="A", nationality_country="FR"),  # degree unknown
            FacultyMember(id="2", full_name="B", nationality_country="TN",
                          highest_degree_country="TN"),
        ]
        result = int_01_international_faculty_ratio(_inputs(faculty=faculty))
        assert result.value == 50.0
        assert any("only one signal" in w for w in result.warnings)
        assert not result.is_complete

    def test_unclassified_warning(self):
        faculty = [
            FacultyMember(id="1", full_name="A", nationality_country="FR",
                          highest_degree_country="TN"),
            FacultyMember(id="2", full_name="B"),  # both unknown -> excluded
        ]
        result = int_01_international_faculty_ratio(_inputs(faculty=faculty))
        assert result.value == 100.0  # 1/1 of classified
        assert any("missing both nationality and degree" in w for w in result.warnings)

    def test_no_signals_at_all(self):
        faculty = [FacultyMember(id="1", full_name="A")]
        result = int_01_international_faculty_ratio(_inputs(faculty=faculty))
        assert result.value is None
        assert "faculty.nationality_country / faculty.highest_degree_country" in result.missing_fields

    def test_inactive_faculty_excluded(self):
        faculty = [
            FacultyMember(id="1", full_name="A", is_active=False,
                          nationality_country="FR", highest_degree_country="FR"),
            FacultyMember(id="2", full_name="B", is_active=True,
                          nationality_country="TN", highest_degree_country="TN"),
        ]
        result = int_01_international_faculty_ratio(_inputs(faculty=faculty))
        assert result.value == 0.0


# ---------------------------------------------------------------------------
# INT-02
# ---------------------------------------------------------------------------


class TestInt02InternationalStudent:
    def test_pct(self):
        students = [
            Student(id="1", status=StudentStatus.ACTIVE, nationality_country="TN"),
            Student(id="2", status=StudentStatus.ACTIVE, nationality_country="FR"),
            Student(id="3", status=StudentStatus.ACTIVE, nationality_country="DZ"),
            Student(id="4", status=StudentStatus.ACTIVE, nationality_country="TN"),
        ]
        result = int_02_international_student_ratio(_inputs(students=students))
        assert result.value == 50.0

    def test_excludes_non_enrolled(self):
        students = [
            Student(id="1", status=StudentStatus.ACTIVE, nationality_country="FR"),
            Student(id="2", status=StudentStatus.GRADUATED, nationality_country="DE"),
        ]
        result = int_02_international_student_ratio(_inputs(students=students))
        assert result.value == 100.0

    def test_no_nationality_data(self):
        students = [Student(id="1", status=StudentStatus.ACTIVE)]
        result = int_02_international_student_ratio(_inputs(students=students))
        assert result.value is None
        assert "students.nationality_country" in result.missing_fields


# ---------------------------------------------------------------------------
# INT-03 / 04
# ---------------------------------------------------------------------------


class TestInt03Int04Mobility:
    def test_int_03_outgoing(self):
        students = [
            Student(id="1", status=StudentStatus.ACTIVE, is_outgoing_exchange=True),
            Student(id="2", status=StudentStatus.ACTIVE, is_outgoing_exchange=False),
            Student(id="3", status=StudentStatus.ACTIVE, is_outgoing_exchange=True),
        ]
        result = int_03_outgoing_student_mobility(_inputs(students=students))
        assert result.value == pytest.approx(200 / 3)

    def test_int_04_incoming(self):
        students = [
            Student(id="1", status=StudentStatus.ACTIVE, is_incoming_exchange=True),
            Student(id="2", status=StudentStatus.ACTIVE, is_incoming_exchange=False),
        ]
        result = int_04_incoming_student_mobility(_inputs(students=students))
        assert result.value == 50.0

    def test_int_04_excludes_non_enrolled(self):
        students = [
            Student(id="1", status=StudentStatus.ACTIVE, is_incoming_exchange=True),
            Student(id="2", status=StudentStatus.GRADUATED, is_incoming_exchange=True),  # excluded
        ]
        result = int_04_incoming_student_mobility(_inputs(students=students))
        assert result.value == 100.0


# ---------------------------------------------------------------------------
# INT-05
# ---------------------------------------------------------------------------


class TestInt05InternationalPartnerships:
    def test_counts_active_foreign(self):
        partnerships = [
            AcademicPartnership(id="1", partner_name="Sorbonne", partner_country="FR",
                                is_active=True),
            AcademicPartnership(id="2", partner_name="TUM", partner_country="DE",
                                is_active=True),
            AcademicPartnership(id="3", partner_name="Local", partner_country="TN",
                                is_active=True),
            AcademicPartnership(id="4", partner_name="MIT", partner_country="US",
                                is_active=False),
        ]
        result = int_05_international_partnerships(_inputs(academic_partnerships=partnerships))
        assert result.value == 2.0

    def test_no_partnerships(self):
        result = int_05_international_partnerships(_inputs())
        assert result.value is None
        assert "academic_partnerships" in result.missing_fields

    def test_warns_on_missing_country(self):
        partnerships = [
            AcademicPartnership(id="1", partner_name="A", partner_country="FR", is_active=True),
            AcademicPartnership(id="2", partner_name="B", partner_country=None, is_active=True),
        ]
        result = int_05_international_partnerships(_inputs(academic_partnerships=partnerships))
        assert result.value == 1.0
        assert any("missing partner_country" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# INT-06
# ---------------------------------------------------------------------------


class TestInt06ForeignLanguagePrograms:
    def test_pct_with_default_official_languages(self):
        programs = [
            Program(id="1", name="A", teaching_languages=["fr"]),  # local
            Program(id="2", name="B", teaching_languages=["en"]),  # foreign
            Program(id="3", name="C", teaching_languages=["fr", "en"]),  # foreign (mixed)
            Program(id="4", name="D", teaching_languages=["ar", "fr"]),  # local
        ]
        result = int_06_foreign_language_program_rate(_inputs(programs=programs))
        assert result.value == 50.0

    def test_custom_official_languages(self):
        programs = [
            Program(id="1", name="A", teaching_languages=["en"]),
            Program(id="2", name="B", teaching_languages=["fr"]),
        ]
        # If institution officially teaches in English, EN is local and FR is foreign.
        result = int_06_foreign_language_program_rate(
            _inputs(programs=programs, official_languages=frozenset({"en"}))
        )
        assert result.value == 50.0

    def test_excludes_inactive(self):
        programs = [
            Program(id="1", name="A", is_active=True, teaching_languages=["en"]),
            Program(id="2", name="B", is_active=False, teaching_languages=["en"]),
        ]
        result = int_06_foreign_language_program_rate(_inputs(programs=programs))
        assert result.value == 100.0
        assert result.inputs_used["active_programs"] == 1

    def test_missing_languages_data(self):
        programs = [Program(id="1", name="A", is_active=True, teaching_languages=None)]
        result = int_06_foreign_language_program_rate(_inputs(programs=programs))
        assert result.value is None
        assert "programs.teaching_languages" in result.missing_fields


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def test_dispatcher_runs_all_six():
    results = compute_international_domain(_inputs())
    assert {r.kpi_id for r in results} == {f"INT-{i:02d}" for i in range(1, 7)}
    for r in results:
        if r.value is None:
            assert r.missing_fields, f"{r.kpi_id} returned None without missing_fields"


def test_realistic_insat_fixture():
    faculty = [
        FacultyMember(
            id=f"f{i}",
            full_name=f"F{i}",
            nationality_country="FR" if i % 7 == 0 else "TN",
            highest_degree_country="DE" if i % 5 == 0 else "TN",
        )
        for i in range(20)
    ]
    students = [
        Student(
            id=f"s{i}",
            status=StudentStatus.ACTIVE,
            nationality_country="LY" if i % 11 == 0 else "TN",
            is_outgoing_exchange=(i % 17 == 0),
            is_incoming_exchange=(i % 19 == 0),
        )
        for i in range(200)
    ]
    programs = [
        Program(id="p1", name="Networks", is_active=True, teaching_languages=["fr"]),
        Program(id="p2", name="MBA", is_active=True, teaching_languages=["en", "fr"]),
        Program(id="p3", name="Arabic Lit", is_active=True, teaching_languages=["ar"]),
    ]
    partnerships = [
        AcademicPartnership(id="1", partner_name="Sorbonne", partner_country="FR", is_active=True),
        AcademicPartnership(id="2", partner_name="TUM", partner_country="DE", is_active=True),
        AcademicPartnership(id="3", partner_name="UTunis", partner_country="TN", is_active=True),
    ]
    inputs = _inputs(
        faculty=faculty, students=students, programs=programs,
        academic_partnerships=partnerships,
    )
    results = {r.kpi_id: r for r in compute_international_domain(inputs)}
    assert {r for r in results} == {f"INT-{i:02d}" for i in range(1, 7)}
    # All should produce a value with this fixture.
    for kpi_id, r in results.items():
        assert r.value is not None, f"{kpi_id} unexpectedly missing"
