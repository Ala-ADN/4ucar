"""Unit tests for Domain C (Employability & Industry Relations) calculators."""

from __future__ import annotations

from datetime import date

import pytest

from backend.services.kpi_service.domain import (
    Alumnus,
    EmployerSurveyResponse,
    GraduateSurveyResponse,
    IndustryPartnership,
    InstitutionEmploymentInputs,
    PfeProject,
    Student,
    StudentStatus,
    compute_employment_domain,
)
from backend.services.kpi_service.domain.employment import (
    emp_01_graduate_employment_rate,
    emp_02_employer_reputation_score,
    emp_03_time_to_first_employment,
    emp_04_industry_partnership_count,
    emp_05_internship_placement_rate,
    emp_06_pfe_industry_rate,
    emp_07_alumni_engagement_rate,
    emp_08_career_services_utilization,
)

PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 12, 31)


def _inputs(**overrides) -> InstitutionEmploymentInputs:
    base = dict(
        institution_id="inst-1",
        institution_code="INSAT",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
    )
    base.update(overrides)
    return InstitutionEmploymentInputs(**base)


# ---------------------------------------------------------------------------
# EMP-01
# ---------------------------------------------------------------------------


class TestEmp01GraduateEmployment:
    def test_basic(self):
        surveys = [
            GraduateSurveyResponse(graduate_id="g1", employed_within_12_months=True),
            GraduateSurveyResponse(graduate_id="g2", employed_within_12_months=True),
            GraduateSurveyResponse(graduate_id="g3", employed_within_12_months=False),
            GraduateSurveyResponse(graduate_id="g4", employed_within_12_months=True),
        ]
        result = emp_01_graduate_employment_rate(_inputs(graduate_surveys=surveys))
        assert result.value == 75.0

    def test_partial_data_warns(self):
        surveys = [
            GraduateSurveyResponse(graduate_id="g1", employed_within_12_months=True),
            GraduateSurveyResponse(graduate_id="g2", employed_within_12_months=None),
        ]
        result = emp_01_graduate_employment_rate(_inputs(graduate_surveys=surveys))
        assert result.value == 100.0
        assert any("missing employed_within_12_months" in w for w in result.warnings)
        assert not result.is_complete

    def test_no_data(self):
        result = emp_01_graduate_employment_rate(_inputs())
        assert result.value is None
        assert "graduate_surveys" in result.missing_fields

    def test_low_response_rate_warning(self):
        surveys = [GraduateSurveyResponse(graduate_id=f"g{i}", responded=(i < 2),
                                          employed_within_12_months=True if i < 2 else None)
                   for i in range(10)]
        result = emp_01_graduate_employment_rate(_inputs(graduate_surveys=surveys))
        assert any("response rate" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# EMP-02
# ---------------------------------------------------------------------------


class TestEmp02EmployerReputation:
    def test_unweighted_mean(self):
        responses = [
            EmployerSurveyResponse(response_id="1", score=80.0),
            EmployerSurveyResponse(response_id="2", score=60.0),
        ]
        result = emp_02_employer_reputation_score(_inputs(employer_surveys=responses))
        assert result.value == 70.0

    def test_weighted_mean(self):
        responses = [
            EmployerSurveyResponse(response_id="1", score=80.0, weight=3.0),
            EmployerSurveyResponse(response_id="2", score=60.0, weight=1.0),
        ]
        result = emp_02_employer_reputation_score(_inputs(employer_surveys=responses))
        assert result.value == pytest.approx(75.0)

    def test_no_data(self):
        result = emp_02_employer_reputation_score(_inputs())
        assert result.value is None
        assert "employer_surveys" in result.missing_fields


# ---------------------------------------------------------------------------
# EMP-03
# ---------------------------------------------------------------------------


class TestEmp03TimeToFirstEmployment:
    def test_median(self):
        surveys = [
            GraduateSurveyResponse(graduate_id="g1", employed_within_12_months=True,
                                   months_to_first_employment=2),
            GraduateSurveyResponse(graduate_id="g2", employed_within_12_months=True,
                                   months_to_first_employment=4),
            GraduateSurveyResponse(graduate_id="g3", employed_within_12_months=True,
                                   months_to_first_employment=8),
        ]
        result = emp_03_time_to_first_employment(_inputs(graduate_surveys=surveys))
        assert result.value == 4.0

    def test_warns_on_employed_but_no_months(self):
        surveys = [
            GraduateSurveyResponse(graduate_id="g1", employed_within_12_months=True,
                                   months_to_first_employment=3),
            GraduateSurveyResponse(graduate_id="g2", employed_within_12_months=True,
                                   months_to_first_employment=None),
        ]
        result = emp_03_time_to_first_employment(_inputs(graduate_surveys=surveys))
        assert result.value == 3.0
        assert any("months_to_first_employment" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# EMP-04
# ---------------------------------------------------------------------------


class TestEmp04IndustryPartnerships:
    def test_counts_active_private(self):
        partnerships = [
            IndustryPartnership(id="1", partner_name="A", is_active=True, is_private_sector=True),
            IndustryPartnership(id="2", partner_name="B", is_active=True, is_private_sector=False),
            IndustryPartnership(id="3", partner_name="C", is_active=False, is_private_sector=True),
            IndustryPartnership(id="4", partner_name="D", is_active=True, is_private_sector=True),
        ]
        result = emp_04_industry_partnership_count(_inputs(industry_partnerships=partnerships))
        assert result.value == 2.0


# ---------------------------------------------------------------------------
# EMP-05
# ---------------------------------------------------------------------------


class TestEmp05InternshipPlacementRate:
    def test_rate(self):
        students = [
            Student(id="1", is_final_year=True, internship_required=True,
                    completed_required_internship=True),
            Student(id="2", is_final_year=True, internship_required=True,
                    completed_required_internship=False),
            Student(id="3", is_final_year=True, internship_required=True,
                    completed_required_internship=True),
            Student(id="4", is_final_year=False),  # excluded
            Student(id="5", is_final_year=True, internship_required=False),  # excluded
        ]
        result = emp_05_internship_placement_rate(_inputs(students=students))
        assert result.value == pytest.approx(200 / 3)

    def test_no_final_year_students(self):
        students = [Student(id="1", is_final_year=False)]
        result = emp_05_internship_placement_rate(_inputs(students=students))
        assert result.value is None
        assert any("is_final_year" in m for m in result.missing_fields)


# ---------------------------------------------------------------------------
# EMP-06
# ---------------------------------------------------------------------------


class TestEmp06PfeIndustry:
    def test_rate(self):
        pfes = [
            PfeProject(id="1", hosted_by_industry=True),
            PfeProject(id="2", hosted_by_industry=True),
            PfeProject(id="3", hosted_by_industry=False),
        ]
        result = emp_06_pfe_industry_rate(_inputs(pfe_projects=pfes))
        assert result.value == pytest.approx(200 / 3)

    def test_partial_data(self):
        pfes = [
            PfeProject(id="1", hosted_by_industry=True),
            PfeProject(id="2", hosted_by_industry=None),
        ]
        result = emp_06_pfe_industry_rate(_inputs(pfe_projects=pfes))
        assert result.value == 100.0
        assert any("missing hosted_by_industry" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# EMP-07
# ---------------------------------------------------------------------------


class TestEmp07AlumniEngagement:
    def test_5y_window(self):
        # period_end=2026 -> window starts 2022 (cutoff_year = 2026 - 5 + 1 = 2022)
        alumni = [
            Alumnus(id="1", graduation_year=2024, engaged_in_period=True),
            Alumnus(id="2", graduation_year=2023, engaged_in_period=False),
            Alumnus(id="3", graduation_year=2018, engaged_in_period=True),  # outside window
            Alumnus(id="4", graduation_year=2025, engaged_in_period=True),
        ]
        result = emp_07_alumni_engagement_rate(_inputs(alumni=alumni))
        assert result.value == pytest.approx(200 / 3)
        assert result.inputs_used["alumni_in_window"] == 3
        assert result.inputs_used["window_cutoff_year"] == 2022

    def test_no_in_window(self):
        alumni = [Alumnus(id="1", graduation_year=2010, engaged_in_period=True)]
        result = emp_07_alumni_engagement_rate(_inputs(alumni=alumni))
        assert result.value is None
        assert any("graduation_year" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# EMP-08
# ---------------------------------------------------------------------------


class TestEmp08CareerServices:
    def test_pct(self):
        students = [
            Student(id="1", status=StudentStatus.ACTIVE, used_career_services=True),
            Student(id="2", status=StudentStatus.ACTIVE, used_career_services=False),
            Student(id="3", status=StudentStatus.ACTIVE, used_career_services=True),
        ]
        result = emp_08_career_services_utilization(_inputs(students=students))
        assert result.value == pytest.approx(200 / 3)

    def test_only_enrolled_in_denominator(self):
        students = [
            Student(id="1", status=StudentStatus.ACTIVE, used_career_services=True),
            Student(id="2", status=StudentStatus.GRADUATED, used_career_services=True),  # excluded
        ]
        result = emp_08_career_services_utilization(_inputs(students=students))
        assert result.value == 100.0


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def test_dispatcher_runs_all_eight():
    results = compute_employment_domain(_inputs())
    assert {r.kpi_id for r in results} == {f"EMP-{i:02d}" for i in range(1, 9)}
    for r in results:
        if r.value is None:
            assert r.missing_fields, f"{r.kpi_id} returned None without missing_fields"


def test_realistic_insat_fixture():
    surveys = [
        GraduateSurveyResponse(
            graduate_id=f"g{i}",
            employed_within_12_months=(i % 5 != 0),
            months_to_first_employment=(i % 6) + 1 if i % 5 != 0 else None,
        )
        for i in range(120)
    ]
    employer_responses = [
        EmployerSurveyResponse(response_id=f"e{i}", score=50 + (i % 50), weight=1.0 + (i % 3))
        for i in range(40)
    ]
    partnerships = [
        IndustryPartnership(id=f"p{i}", partner_name=f"Co{i}", is_active=(i % 4 != 0))
        for i in range(15)
    ]
    students = [
        Student(
            id=f"s{i}",
            status=StudentStatus.ACTIVE,
            is_final_year=(i % 4 == 0),
            internship_required=(i % 4 == 0),
            completed_required_internship=(i % 8 == 0),
            used_career_services=(i % 3 == 0),
        )
        for i in range(200)
    ]
    pfes = [PfeProject(id=f"pfe{i}", hosted_by_industry=(i % 3 != 0)) for i in range(45)]
    alumni = [
        Alumnus(id=f"a{i}", graduation_year=2022 + (i % 5), engaged_in_period=(i % 4 == 0))
        for i in range(300)
    ]
    inputs = _inputs(
        students=students,
        graduate_surveys=surveys,
        employer_surveys=employer_responses,
        industry_partnerships=partnerships,
        pfe_projects=pfes,
        alumni=alumni,
    )
    results = compute_employment_domain(inputs)
    assert {r.kpi_id for r in results} == {f"EMP-{i:02d}" for i in range(1, 9)}
    # All KPIs should produce a value (no missing data in this fixture).
    for r in results:
        assert r.value is not None, f"{r.kpi_id} unexpectedly missing"
