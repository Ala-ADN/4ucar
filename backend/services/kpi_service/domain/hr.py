"""Domain F - Human Resources KPI calculators (HR-01..HR-09).

HR-01's tolerance band is configurable per institution via
`InstitutionHrInputs.workload_tolerance` (default 20% from the spec).
HR-06 aggregates absenteeism across faculty AND admin staff.
"""

from __future__ import annotations

from collections.abc import Callable
from statistics import median, pstdev

from .inputs import (
    InstitutionHrInputs,
    currently_enrolled,
    total_active_fte,
)
from .result import KpiResult, build_kpi_result

DOMAIN = "HR"


def _result(*, inputs: InstitutionHrInputs, **kw) -> KpiResult:
    return build_kpi_result(inputs, DOMAIN, **kw)


def _admin_active_fte(inputs: InstitutionHrInputs) -> float:
    return sum(a.fte_fraction for a in inputs.admin_staff if a.is_active)


# ---------------------------------------------------------------------------
# HR-01 Professor Workload Compliance Rate
# ---------------------------------------------------------------------------


def hr_01_workload_compliance(inputs: InstitutionHrInputs) -> KpiResult:
    active = [f for f in inputs.faculty if f.is_active]
    classified = [
        f for f in active
        if f.contracted_hours is not None and f.delivered_hours is not None
        and f.contracted_hours > 0
    ]
    missing: list[str] = []
    warnings: list[str] = []

    if not active:
        missing.append("active_faculty")
    if active and not classified:
        missing.append("faculty.contracted_hours / faculty.delivered_hours")
    if classified and len(classified) < len(active):
        warnings.append(
            f"{len(active) - len(classified)}/{len(active)} active faculty missing workload data"
        )

    if not classified:
        return _result(
            kpi_id="HR-01",
            name="Professor Workload Compliance Rate",
            formula=(
                "100 * count(faculty within +/- tolerance of contracted_hours) / "
                "count(active faculty with workload data)"
            ),
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"classified": 0, "tolerance": inputs.workload_tolerance},
        )

    tol = inputs.workload_tolerance
    compliant = sum(
        1
        for f in classified
        if abs((f.delivered_hours or 0) - f.contracted_hours) / f.contracted_hours <= tol
    )
    value = 100.0 * compliant / len(classified)
    return _result(
        kpi_id="HR-01",
        name="Professor Workload Compliance Rate",
        formula=(
            "100 * count(faculty within +/- tolerance of contracted_hours) / "
            "count(active faculty with workload data)"
        ),
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "classified": len(classified),
            "compliant": compliant,
            "tolerance": tol,
        },
    )


# ---------------------------------------------------------------------------
# HR-02 Teaching Load Balance Index (population std dev)
# ---------------------------------------------------------------------------


def hr_02_teaching_load_balance(inputs: InstitutionHrInputs) -> KpiResult:
    delivered = [
        f.delivered_hours
        for f in inputs.faculty
        if f.is_active and f.delivered_hours is not None
    ]
    missing: list[str] = []
    if len(delivered) < 2:
        if not delivered:
            missing.append("faculty.delivered_hours")
        return _result(
            kpi_id="HR-02",
            name="Teaching Load Balance Index",
            formula="population_stdev(delivered_hours over active faculty) - lower is better",
            unit="hours (stdev)",
            inputs=inputs,
            value=None,
            missing=missing or ["faculty.delivered_hours (need >=2 values)"],
            warnings=[],
            used={"datapoints": len(delivered)},
        )

    value = float(pstdev(delivered))
    return _result(
        kpi_id="HR-02",
        name="Teaching Load Balance Index",
        formula="population_stdev(delivered_hours over active faculty) - lower is better",
        unit="hours (stdev)",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=[],
        used={
            "datapoints": len(delivered),
            "min": min(delivered),
            "max": max(delivered),
            "mean": sum(delivered) / len(delivered),
        },
    )


# ---------------------------------------------------------------------------
# HR-03 Professor-per-Student Ratio (inverse of ACA-01)
# ---------------------------------------------------------------------------


def hr_03_professor_per_student(inputs: InstitutionHrInputs) -> KpiResult:
    fte = total_active_fte(inputs.faculty)
    enrolled = currently_enrolled(inputs.students)
    missing: list[str] = []
    if fte == 0:
        missing.append("active_faculty_fte")
    if not enrolled:
        if not inputs.students:
            missing.append("students")
        else:
            missing.append("students.status (enrolled denominator empty)")

    value = fte / len(enrolled) if enrolled else None
    return _result(
        kpi_id="HR-03",
        name="Professor-per-Student Ratio",
        formula="active FTE faculty / count(currently enrolled students)",
        unit="FTE/student",
        inputs=inputs,
        value=value,
        missing=missing,
        warnings=[],
        used={"active_fte": fte, "enrolled": len(enrolled)},
    )


# ---------------------------------------------------------------------------
# HR-04 Administrative Staff per Student
# ---------------------------------------------------------------------------


def hr_04_admin_per_student(inputs: InstitutionHrInputs) -> KpiResult:
    admin_fte = _admin_active_fte(inputs)
    enrolled = currently_enrolled(inputs.students)
    missing: list[str] = []
    if not inputs.admin_staff:
        missing.append("admin_staff")
    if not enrolled:
        if not inputs.students:
            missing.append("students")
        else:
            missing.append("students.status (enrolled denominator empty)")

    value = admin_fte / len(enrolled) if enrolled else None
    return _result(
        kpi_id="HR-04",
        name="Administrative Staff per Student",
        formula="admin FTE / count(currently enrolled students)",
        unit="FTE/student",
        inputs=inputs,
        value=value,
        missing=missing,
        warnings=[],
        used={"admin_fte": admin_fte, "enrolled": len(enrolled)},
    )


# ---------------------------------------------------------------------------
# HR-05 Faculty Training Fulfillment Rate - ISO 21001
# ---------------------------------------------------------------------------


def hr_05_faculty_training_fulfillment(inputs: InstitutionHrInputs) -> KpiResult:
    active = [f for f in inputs.faculty if f.is_active]
    classified = [
        f for f in active
        if f.training_hours_required is not None and f.training_hours_completed is not None
    ]
    missing: list[str] = []
    warnings: list[str] = []

    if not active:
        missing.append("active_faculty")
    if active and not classified:
        missing.append("faculty.training_hours_required / faculty.training_hours_completed")
    if classified and len(classified) < len(active):
        warnings.append(
            f"{len(active) - len(classified)}/{len(active)} active faculty missing training data"
        )

    required = sum(f.training_hours_required or 0 for f in classified)
    completed = sum(f.training_hours_completed or 0 for f in classified)
    if required == 0:
        return _result(
            kpi_id="HR-05",
            name="Faculty Training Fulfillment Rate",
            formula="100 * sum(training_hours_completed) / sum(training_hours_required)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing or ["faculty.training_hours_required (sum is zero)"],
            warnings=warnings,
            used={"classified": len(classified), "required_hours": 0},
        )

    value = 100.0 * completed / required
    return _result(
        kpi_id="HR-05",
        name="Faculty Training Fulfillment Rate",
        formula="100 * sum(training_hours_completed) / sum(training_hours_required)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "classified": len(classified),
            "required_hours": required,
            "completed_hours": completed,
        },
    )


# ---------------------------------------------------------------------------
# HR-06 Absenteeism Rate (staff: faculty + admin)
# ---------------------------------------------------------------------------


def hr_06_staff_absenteeism(inputs: InstitutionHrInputs) -> KpiResult:
    pairs: list[tuple[int, int]] = []
    for f in inputs.faculty:
        if f.is_active and f.scheduled_workdays and f.unexcused_absence_days is not None:
            pairs.append((f.unexcused_absence_days, f.scheduled_workdays))
    for a in inputs.admin_staff:
        if a.is_active and a.scheduled_workdays and a.unexcused_absence_days is not None:
            pairs.append((a.unexcused_absence_days, a.scheduled_workdays))

    missing: list[str] = []
    if not inputs.faculty and not inputs.admin_staff:
        missing.append("faculty / admin_staff")
    if not pairs:
        missing.append(
            "staff.scheduled_workdays / staff.unexcused_absence_days"
        )
        return _result(
            kpi_id="HR-06",
            name="Absenteeism Rate (staff)",
            formula="100 * sum(unexcused_absence_days) / sum(scheduled_workdays) over all staff",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=[],
            used={"staff_with_data": 0},
        )

    absent = sum(p[0] for p in pairs)
    scheduled = sum(p[1] for p in pairs)
    value = 100.0 * absent / scheduled if scheduled else None
    return _result(
        kpi_id="HR-06",
        name="Absenteeism Rate (staff)",
        formula="100 * sum(unexcused_absence_days) / sum(scheduled_workdays) over all staff",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=[],
        used={
            "staff_with_data": len(pairs),
            "total_absent_days": absent,
            "total_scheduled_days": scheduled,
        },
    )


# ---------------------------------------------------------------------------
# HR-07 Vacancy Fill Time (median days)
# ---------------------------------------------------------------------------


def hr_07_vacancy_fill_time(inputs: InstitutionHrInputs) -> KpiResult:
    fill_days = [
        (v.contract_signed_date - v.position_open_date).days
        for v in inputs.vacancy_events
        if v.position_open_date is not None and v.contract_signed_date is not None
    ]
    missing: list[str] = []
    warnings: list[str] = []

    if not inputs.vacancy_events:
        missing.append("vacancy_events")
    unfilled = sum(
        1
        for v in inputs.vacancy_events
        if v.position_open_date is not None and v.contract_signed_date is None
    )
    if unfilled:
        warnings.append(f"{unfilled} vacancies still open at period end (excluded)")

    if not fill_days:
        if inputs.vacancy_events and not missing:
            missing.append("vacancy_events.contract_signed_date (all open)")
        return _result(
            kpi_id="HR-07",
            name="Vacancy Fill Time",
            formula="median(contract_signed_date - position_open_date) over filled vacancies",
            unit="days",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"filled_events": 0, "unfilled_events": unfilled},
        )

    value = float(median(fill_days))
    return _result(
        kpi_id="HR-07",
        name="Vacancy Fill Time",
        formula="median(contract_signed_date - position_open_date) over filled vacancies",
        unit="days",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "filled_events": len(fill_days),
            "unfilled_events": unfilled,
            "min_days": min(fill_days),
            "max_days": max(fill_days),
        },
    )


# ---------------------------------------------------------------------------
# HR-08 Permanent-to-Contractual Faculty Ratio (% permanent)
# ---------------------------------------------------------------------------


def hr_08_permanent_faculty_ratio(inputs: InstitutionHrInputs) -> KpiResult:
    active = [f for f in inputs.faculty if f.is_active]
    classified = [f for f in active if f.is_permanent is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not active:
        missing.append("active_faculty")
    if active and not classified:
        missing.append("faculty.is_permanent")
    if classified and len(classified) < len(active):
        warnings.append(
            f"{len(active) - len(classified)}/{len(active)} active faculty missing is_permanent"
        )

    if not classified:
        return _result(
            kpi_id="HR-08",
            name="Permanent-to-Contractual Faculty Ratio",
            formula="100 * count(faculty.is_permanent=True) / count(active faculty with flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"classified": 0},
        )

    permanent = sum(1 for f in classified if f.is_permanent)
    value = 100.0 * permanent / len(classified)
    return _result(
        kpi_id="HR-08",
        name="Permanent-to-Contractual Faculty Ratio",
        formula="100 * count(faculty.is_permanent=True) / count(active faculty with flag)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={"classified": len(classified), "permanent": permanent},
    )


# ---------------------------------------------------------------------------
# HR-09 Faculty Expertise Match Rate
# ---------------------------------------------------------------------------


def hr_09_faculty_expertise_match(inputs: InstitutionHrInputs) -> KpiResult:
    active = [f for f in inputs.faculty if f.is_active]
    classified = [f for f in active if f.expertise_matches_courses is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not active:
        missing.append("active_faculty")
    if active and not classified:
        missing.append("faculty.expertise_matches_courses")
    if classified and len(classified) < len(active):
        warnings.append(
            f"{len(active) - len(classified)}/{len(active)} active faculty "
            "missing expertise_matches_courses"
        )

    if not classified:
        return _result(
            kpi_id="HR-09",
            name="Faculty Expertise Match Rate",
            formula="100 * count(faculty.expertise_matches_courses=True) / count(active with flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"classified": 0},
        )

    matched = sum(1 for f in classified if f.expertise_matches_courses)
    value = 100.0 * matched / len(classified)
    return _result(
        kpi_id="HR-09",
        name="Faculty Expertise Match Rate",
        formula="100 * count(faculty.expertise_matches_courses=True) / count(active with flag)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={"classified": len(classified), "matched": matched},
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

DOMAIN_F_CALCULATORS: list[Callable[[InstitutionHrInputs], KpiResult]] = [
    hr_01_workload_compliance,
    hr_02_teaching_load_balance,
    hr_03_professor_per_student,
    hr_04_admin_per_student,
    hr_05_faculty_training_fulfillment,
    hr_06_staff_absenteeism,
    hr_07_vacancy_fill_time,
    hr_08_permanent_faculty_ratio,
    hr_09_faculty_expertise_match,
]
