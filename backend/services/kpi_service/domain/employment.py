"""Domain C - Employability & Industry Relations KPI calculators (EMP-01..EMP-08).

Survey-driven KPIs (EMP-01, EMP-02, EMP-03, EMP-07) report response counts in
`inputs_used` so dashboards can display non-response bias alongside the value.
"""

from __future__ import annotations

from collections.abc import Callable
from statistics import median

from .inputs import (
    InstitutionEmploymentInputs,
    currently_enrolled,
)
from .result import KpiResult, build_kpi_result

DOMAIN = "EMPLOYMENT"

ALUMNI_WINDOW_YEARS = 5


def _result(*, inputs: InstitutionEmploymentInputs, **kw) -> KpiResult:
    return build_kpi_result(inputs, DOMAIN, **kw)


# ---------------------------------------------------------------------------
# EMP-01 Graduate Employment Rate - QS 10% + 5%
# ---------------------------------------------------------------------------


def emp_01_graduate_employment_rate(inputs: InstitutionEmploymentInputs) -> KpiResult:
    surveys = inputs.graduate_surveys
    classified = [s for s in surveys if s.employed_within_12_months is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not surveys:
        missing.append("graduate_surveys")
    if surveys and not classified:
        missing.append("graduate_surveys.employed_within_12_months")

    response_rate_warning = None
    if surveys:
        response_count = sum(1 for s in surveys if s.responded)
        if response_count and response_count < len(surveys) * 0.5:
            response_rate_warning = (
                f"survey response rate {response_count}/{len(surveys)} below 50%"
            )
        if response_rate_warning:
            warnings.append(response_rate_warning)

    if classified and len(classified) < len(surveys):
        warnings.append(
            f"{len(surveys) - len(classified)}/{len(surveys)} surveys "
            "missing employed_within_12_months"
        )

    if not classified:
        return _result(
            kpi_id="EMP-01",
            name="Graduate Employment Rate",
            formula="100 * count(employed_within_12_months=True) / count(surveys with verdict)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"surveys_known": len(surveys), "with_employment_verdict": 0},
        )

    employed = sum(1 for s in classified if s.employed_within_12_months)
    value = 100.0 * employed / len(classified)
    return _result(
        kpi_id="EMP-01",
        name="Graduate Employment Rate",
        formula="100 * count(employed_within_12_months=True) / count(surveys with verdict)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "surveys_known": len(surveys),
            "with_employment_verdict": len(classified),
            "employed": employed,
        },
    )


# ---------------------------------------------------------------------------
# EMP-02 Employer Reputation Score - QS 10%
# ---------------------------------------------------------------------------


def emp_02_employer_reputation_score(inputs: InstitutionEmploymentInputs) -> KpiResult:
    responses = inputs.employer_surveys
    missing: list[str] = []
    if not responses:
        missing.append("employer_surveys")
        return _result(
            kpi_id="EMP-02",
            name="Employer Reputation Score",
            formula="weighted_mean(score, weight)",
            unit="score (0..100)",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=[],
            used={"responses": 0},
        )

    weight_sum = sum(r.weight for r in responses)
    if weight_sum == 0:
        return _result(
            kpi_id="EMP-02",
            name="Employer Reputation Score",
            formula="weighted_mean(score, weight)",
            unit="score (0..100)",
            inputs=inputs,
            value=None,
            missing=["employer_surveys.weight (all zero)"],
            warnings=[],
            used={"responses": len(responses)},
        )

    value = sum(r.score * r.weight for r in responses) / weight_sum
    return _result(
        kpi_id="EMP-02",
        name="Employer Reputation Score",
        formula="weighted_mean(score, weight)",
        unit="score (0..100)",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=[],
        used={
            "responses": len(responses),
            "total_weight": weight_sum,
            "min_score": min(r.score for r in responses),
            "max_score": max(r.score for r in responses),
        },
    )


# ---------------------------------------------------------------------------
# EMP-03 Time to First Employment - QS Employment Outcomes
# ---------------------------------------------------------------------------


def emp_03_time_to_first_employment(inputs: InstitutionEmploymentInputs) -> KpiResult:
    months = [
        s.months_to_first_employment
        for s in inputs.graduate_surveys
        if s.months_to_first_employment is not None
    ]
    missing: list[str] = []
    warnings: list[str] = []

    if not inputs.graduate_surveys:
        missing.append("graduate_surveys")
    if inputs.graduate_surveys and not months:
        missing.append("graduate_surveys.months_to_first_employment")

    employed_count = sum(
        1 for s in inputs.graduate_surveys if s.employed_within_12_months
    )
    if employed_count and len(months) < employed_count:
        warnings.append(
            f"{employed_count - len(months)}/{employed_count} employed graduates "
            "missing months_to_first_employment"
        )

    if not months:
        return _result(
            kpi_id="EMP-03",
            name="Time to First Employment",
            formula="median(months_to_first_employment) over employed graduates",
            unit="months",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"datapoints": 0},
        )

    value = float(median(months))
    return _result(
        kpi_id="EMP-03",
        name="Time to First Employment",
        formula="median(months_to_first_employment) over employed graduates",
        unit="months",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "datapoints": len(months),
            "min": min(months),
            "max": max(months),
        },
    )


# ---------------------------------------------------------------------------
# EMP-04 Industry Partnership Count - THE Industry Income proxy
# ---------------------------------------------------------------------------


def emp_04_industry_partnership_count(inputs: InstitutionEmploymentInputs) -> KpiResult:
    partnerships = inputs.industry_partnerships
    missing: list[str] = []
    if not partnerships:
        missing.append("industry_partnerships")

    active_private = [p for p in partnerships if p.is_active and p.is_private_sector]
    return _result(
        kpi_id="EMP-04",
        name="Industry Partnership Count",
        formula="count(industry_partnerships where is_active AND is_private_sector)",
        unit="partnerships",
        inputs=inputs,
        value=float(len(active_private)),
        missing=missing,
        warnings=[],
        used={
            "total_known": len(partnerships),
            "active_private_sector": len(active_private),
        },
    )


# ---------------------------------------------------------------------------
# EMP-05 Internship Placement Rate
# ---------------------------------------------------------------------------


def emp_05_internship_placement_rate(inputs: InstitutionEmploymentInputs) -> KpiResult:
    final_year = [s for s in inputs.students if s.is_final_year]
    required = [s for s in final_year if s.internship_required]
    classified = [s for s in required if s.completed_required_internship is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not inputs.students:
        missing.append("students")
        return _result(
            kpi_id="EMP-05",
            name="Internship Placement Rate",
            formula="100 * count(completed_required_internship=True) / count(final-year, internship-required, with completion flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"final_year_students": 0},
        )

    final_year_known = sum(1 for s in inputs.students if s.is_final_year is not None)
    if final_year_known < len(inputs.students):
        warnings.append(
            f"{len(inputs.students) - final_year_known}/{len(inputs.students)} students "
            "missing is_final_year"
        )
    if not final_year:
        missing.append("students.is_final_year (no final-year students)")
    if final_year and not required:
        # We know about final-year students but none have internship_required set.
        missing.append("students.internship_required")
    if required and not classified:
        missing.append("students.completed_required_internship")

    if not classified:
        return _result(
            kpi_id="EMP-05",
            name="Internship Placement Rate",
            formula="100 * count(completed_required_internship=True) / count(final-year, internship-required, with completion flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={
                "final_year_students": len(final_year),
                "internship_required": len(required),
                "with_completion_flag": 0,
            },
        )

    completed = sum(1 for s in classified if s.completed_required_internship)
    value = 100.0 * completed / len(classified)
    return _result(
        kpi_id="EMP-05",
        name="Internship Placement Rate",
        formula="100 * count(completed_required_internship=True) / count(final-year, internship-required, with completion flag)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "final_year_students": len(final_year),
            "internship_required": len(required),
            "with_completion_flag": len(classified),
            "completed": completed,
        },
    )


# ---------------------------------------------------------------------------
# EMP-06 PFE (Final Year Project) Industry Rate
# ---------------------------------------------------------------------------


def emp_06_pfe_industry_rate(inputs: InstitutionEmploymentInputs) -> KpiResult:
    pfes = inputs.pfe_projects
    classified = [p for p in pfes if p.hosted_by_industry is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not pfes:
        missing.append("pfe_projects")
    if pfes and not classified:
        missing.append("pfe_projects.hosted_by_industry")
    if classified and len(classified) < len(pfes):
        warnings.append(
            f"{len(pfes) - len(classified)}/{len(pfes)} PFE projects missing hosted_by_industry"
        )

    if not classified:
        return _result(
            kpi_id="EMP-06",
            name="PFE (Final Year Project) Industry Rate",
            formula="100 * count(pfe_projects.hosted_by_industry=True) / count(pfe_projects with flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"pfe_with_flag": 0},
        )

    industry = sum(1 for p in classified if p.hosted_by_industry)
    value = 100.0 * industry / len(classified)
    return _result(
        kpi_id="EMP-06",
        name="PFE (Final Year Project) Industry Rate",
        formula="100 * count(pfe_projects.hosted_by_industry=True) / count(pfe_projects with flag)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "pfe_total_known": len(pfes),
            "pfe_with_flag": len(classified),
            "hosted_by_industry": industry,
        },
    )


# ---------------------------------------------------------------------------
# EMP-07 Alumni Engagement Rate - QS EO proxy
# ---------------------------------------------------------------------------


def emp_07_alumni_engagement_rate(inputs: InstitutionEmploymentInputs) -> KpiResult:
    cutoff_year = inputs.period_end.year - ALUMNI_WINDOW_YEARS + 1
    in_window = [
        a
        for a in inputs.alumni
        if a.graduation_year is not None and a.graduation_year >= cutoff_year
    ]
    classified = [a for a in in_window if a.engaged_in_period is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not inputs.alumni:
        missing.append("alumni")
    if inputs.alumni and not in_window:
        warnings.append(
            f"no alumni with graduation_year >= {cutoff_year} (window: {ALUMNI_WINDOW_YEARS}y)"
        )
    if in_window and not classified:
        missing.append("alumni.engaged_in_period")
    if classified and len(classified) < len(in_window):
        warnings.append(
            f"{len(in_window) - len(classified)}/{len(in_window)} in-window alumni "
            "missing engaged_in_period"
        )

    if not classified:
        return _result(
            kpi_id="EMP-07",
            name="Alumni Engagement Rate",
            formula="100 * count(engaged_in_period=True) / count(alumni in 5y window with flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"alumni_in_window": len(in_window), "with_flag": 0},
        )

    engaged = sum(1 for a in classified if a.engaged_in_period)
    value = 100.0 * engaged / len(classified)
    return _result(
        kpi_id="EMP-07",
        name="Alumni Engagement Rate",
        formula="100 * count(engaged_in_period=True) / count(alumni in 5y window with flag)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "alumni_total_known": len(inputs.alumni),
            "alumni_in_window": len(in_window),
            "window_cutoff_year": cutoff_year,
            "engaged": engaged,
        },
    )


# ---------------------------------------------------------------------------
# EMP-08 Career Services Utilization
# ---------------------------------------------------------------------------


def emp_08_career_services_utilization(inputs: InstitutionEmploymentInputs) -> KpiResult:
    enrolled = currently_enrolled(inputs.students)
    classified = [s for s in enrolled if s.used_career_services is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not enrolled:
        missing.append("currently_enrolled_students")
    if enrolled and not classified:
        missing.append("students.used_career_services")
    if classified and len(classified) < len(enrolled):
        warnings.append(
            f"{len(enrolled) - len(classified)}/{len(enrolled)} enrolled students "
            "missing used_career_services"
        )

    if not classified:
        return _result(
            kpi_id="EMP-08",
            name="Career Services Utilization",
            formula="100 * count(used_career_services=True) / count(enrolled with flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"enrolled_with_flag": 0},
        )

    used = sum(1 for s in classified if s.used_career_services)
    value = 100.0 * used / len(classified)
    return _result(
        kpi_id="EMP-08",
        name="Career Services Utilization",
        formula="100 * count(used_career_services=True) / count(enrolled with flag)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={"enrolled_with_flag": len(classified), "used": used},
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

DOMAIN_C_CALCULATORS: list[Callable[[InstitutionEmploymentInputs], KpiResult]] = [
    emp_01_graduate_employment_rate,
    emp_02_employer_reputation_score,
    emp_03_time_to_first_employment,
    emp_04_industry_partnership_count,
    emp_05_internship_placement_rate,
    emp_06_pfe_industry_rate,
    emp_07_alumni_engagement_rate,
    emp_08_career_services_utilization,
]
