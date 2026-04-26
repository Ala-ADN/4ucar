"""Domain B - Academic Quality & Teaching KPI calculators (ACA-01..ACA-12).

Per-cohort metrics (ACA-02, ACA-03) report the institution-wide rate as
`value`, with a per-cohort breakdown placed in `inputs_used["per_cohort"]`.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from .inputs import (
    InstitutionAcademicInputs,
    Student,
    StudentStatus,
    currently_enrolled,
    total_active_fte,
)
from .result import KpiResult, build_kpi_result

DOMAIN = "ACADEMIC"


def _result(*, inputs: InstitutionAcademicInputs, **kw) -> KpiResult:
    return build_kpi_result(inputs, DOMAIN, **kw)


def _per_cohort_breakdown(
    students: list[Student],
    *,
    numerator_pred: Callable[[Student], bool],
    denominator_pred: Callable[[Student], bool],
) -> dict[str, dict]:
    """Group students by cohort_year and report numerator/denominator/rate."""
    by_cohort: dict[int | None, list[Student]] = defaultdict(list)
    for s in students:
        by_cohort[s.cohort_year].append(s)
    out: dict[str, dict] = {}
    for cohort, members in sorted(by_cohort.items(), key=lambda kv: (kv[0] is None, kv[0])):
        denom = sum(1 for s in members if denominator_pred(s))
        numer = sum(1 for s in members if numerator_pred(s))
        out[str(cohort) if cohort is not None else "unknown"] = {
            "denominator": denom,
            "numerator": numer,
            "rate": (numer / denom) if denom else None,
        }
    return out


# ---------------------------------------------------------------------------
# ACA-01 Student-Faculty Ratio - QS 20% / THE 4.5%
# ---------------------------------------------------------------------------


def aca_01_student_faculty_ratio(inputs: InstitutionAcademicInputs) -> KpiResult:
    fte = total_active_fte(inputs.faculty)
    enrolled = currently_enrolled(inputs.students)
    missing: list[str] = []
    warnings: list[str] = []
    if fte == 0:
        missing.append("active_faculty_fte")
    if not enrolled:
        if not inputs.students:
            missing.append("students")
        else:
            warnings.append("no students with status in {ACTIVE, REPEATING}")

    students_without_status = sum(1 for s in inputs.students if s.status is None)
    if students_without_status:
        warnings.append(f"{students_without_status}/{len(inputs.students)} students missing status")

    value = len(enrolled) / fte if fte > 0 else None
    return _result(
        kpi_id="ACA-01",
        name="Student-Faculty Ratio",
        formula="count(currently enrolled students) / active FTE faculty",
        unit="students/FTE",
        inputs=inputs,
        value=value,
        missing=missing,
        warnings=warnings,
        used={
            "currently_enrolled": len(enrolled),
            "students_known": len(inputs.students),
            "active_fte": fte,
        },
    )


# ---------------------------------------------------------------------------
# ACA-02 Success Rate (per cohort, aggregated) - THE Teaching proxy
# ---------------------------------------------------------------------------


def aca_02_success_rate(inputs: InstitutionAcademicInputs) -> KpiResult:
    classified = [s for s in inputs.students if s.passed_all_modules is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not inputs.students:
        missing.append("students")
    if inputs.students and not classified:
        missing.append("students.passed_all_modules")
    if classified and len(classified) < len(inputs.students):
        warnings.append(
            f"{len(inputs.students) - len(classified)}/{len(inputs.students)} "
            "students missing passed_all_modules"
        )

    if not classified:
        return _result(
            kpi_id="ACA-02",
            name="Success Rate",
            formula="100 * count(passed_all_modules=True) / count(students with verdict)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"students_with_verdict": 0},
        )

    passed = sum(1 for s in classified if s.passed_all_modules)
    value = 100.0 * passed / len(classified)
    breakdown = _per_cohort_breakdown(
        classified,
        numerator_pred=lambda s: bool(s.passed_all_modules),
        denominator_pred=lambda s: True,
    )
    return _result(
        kpi_id="ACA-02",
        name="Success Rate",
        formula="100 * count(passed_all_modules=True) / count(students with verdict)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "students_with_verdict": len(classified),
            "passed": passed,
            "per_cohort": breakdown,
        },
    )


# ---------------------------------------------------------------------------
# ACA-03 Dropout Rate (per cohort, aggregated)
# ---------------------------------------------------------------------------


def aca_03_dropout_rate(inputs: InstitutionAcademicInputs) -> KpiResult:
    classified = [s for s in inputs.students if s.status is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not inputs.students:
        missing.append("students")
    if inputs.students and not classified:
        missing.append("students.status")
    if classified and len(classified) < len(inputs.students):
        warnings.append(
            f"{len(inputs.students) - len(classified)}/{len(inputs.students)} students missing status"
        )

    if not classified:
        return _result(
            kpi_id="ACA-03",
            name="Dropout Rate",
            formula="100 * count(status=DROPPED_OUT) / count(students with known status)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"cohort_size": 0},
        )

    dropped = sum(1 for s in classified if s.status == StudentStatus.DROPPED_OUT)
    value = 100.0 * dropped / len(classified)
    breakdown = _per_cohort_breakdown(
        classified,
        numerator_pred=lambda s: s.status == StudentStatus.DROPPED_OUT,
        denominator_pred=lambda s: True,
    )
    return _result(
        kpi_id="ACA-03",
        name="Dropout Rate",
        formula="100 * count(status=DROPPED_OUT) / count(students with known status)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "cohort_size": len(classified),
            "dropped_out": dropped,
            "per_cohort": breakdown,
        },
    )


# ---------------------------------------------------------------------------
# ACA-04 Repetition Rate
# ---------------------------------------------------------------------------


def aca_04_repetition_rate(inputs: InstitutionAcademicInputs) -> KpiResult:
    enrolled = currently_enrolled(inputs.students)
    missing: list[str] = []
    if not inputs.students:
        missing.append("students")
    if inputs.students and not enrolled:
        missing.append("students.status (enrolled denominator empty)")

    if not enrolled:
        return _result(
            kpi_id="ACA-04",
            name="Repetition Rate",
            formula="100 * count(status=REPEATING) / count(currently enrolled)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=[],
            used={"currently_enrolled": 0},
        )

    repeating = sum(1 for s in enrolled if s.status == StudentStatus.REPEATING)
    value = 100.0 * repeating / len(enrolled)
    return _result(
        kpi_id="ACA-04",
        name="Repetition Rate",
        formula="100 * count(status=REPEATING) / count(currently enrolled)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=[],
        used={"currently_enrolled": len(enrolled), "repeating": repeating},
    )


# ---------------------------------------------------------------------------
# ACA-05 Curriculum Coverage Rate - ISO 21001
# ---------------------------------------------------------------------------


def aca_05_curriculum_coverage_rate(inputs: InstitutionAcademicInputs) -> KpiResult:
    classified = [
        m for m in inputs.modules if m.required_hours and m.delivered_hours is not None
    ]
    missing: list[str] = []
    warnings: list[str] = []

    if not inputs.modules:
        missing.append("modules")
    if inputs.modules and not classified:
        missing.append("modules.required_hours / modules.delivered_hours")
    if classified and len(classified) < len(inputs.modules):
        warnings.append(
            f"{len(inputs.modules) - len(classified)}/{len(inputs.modules)} "
            "modules missing required/delivered hours"
        )

    if not classified:
        return _result(
            kpi_id="ACA-05",
            name="Curriculum Coverage Rate",
            formula="100 * mean(delivered_hours / required_hours) over modules",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"modules_with_data": 0},
        )

    rates = [(m.delivered_hours or 0) / (m.required_hours or 1) for m in classified]
    value = 100.0 * sum(rates) / len(rates)
    return _result(
        kpi_id="ACA-05",
        name="Curriculum Coverage Rate",
        formula="100 * mean(delivered_hours / required_hours) over modules",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "modules_with_data": len(classified),
            "mean_rate": sum(rates) / len(rates),
        },
    )


# ---------------------------------------------------------------------------
# ACA-06 Faculty with PhDs (%) - THE Teaching / QS regional
# ---------------------------------------------------------------------------


def aca_06_faculty_with_phds(inputs: InstitutionAcademicInputs) -> KpiResult:
    active = [f for f in inputs.faculty if f.is_active]
    classified = [f for f in active if f.holds_phd is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not active:
        missing.append("active_faculty")
    if active and not classified:
        missing.append("faculty.holds_phd")
    if classified and len(classified) < len(active):
        warnings.append(
            f"{len(active) - len(classified)}/{len(active)} active faculty missing holds_phd"
        )

    if not classified:
        return _result(
            kpi_id="ACA-06",
            name="Faculty with PhDs (%)",
            formula="100 * count(faculty.holds_phd=True) / count(active faculty with known status)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"active_faculty_with_phd_flag": 0},
        )

    with_phd = sum(1 for f in classified if f.holds_phd)
    value = 100.0 * with_phd / len(classified)
    return _result(
        kpi_id="ACA-06",
        name="Faculty with PhDs (%)",
        formula="100 * count(faculty.holds_phd=True) / count(active faculty with known status)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={"active_faculty_with_phd_flag": len(classified), "with_phd": with_phd},
    )


# ---------------------------------------------------------------------------
# ACA-07 Double Degree Programs
# ---------------------------------------------------------------------------


def aca_07_double_degree_programs(inputs: InstitutionAcademicInputs) -> KpiResult:
    active = [p for p in inputs.programs if p.is_active]
    missing: list[str] = []
    if not inputs.programs:
        missing.append("programs")

    dd = [p for p in active if p.double_degree_partner_country]
    return _result(
        kpi_id="ACA-07",
        name="Double Degree Programs",
        formula="count(active programs with double_degree_partner_country set)",
        unit="programs",
        inputs=inputs,
        value=float(len(dd)),
        missing=missing,
        warnings=[],
        used={
            "programs_known": len(inputs.programs),
            "active_programs": len(active),
            "double_degree_count": len(dd),
        },
    )


# ---------------------------------------------------------------------------
# ACA-08 Professional Certifications (students)
# ---------------------------------------------------------------------------


def aca_08_professional_certifications(inputs: InstitutionAcademicInputs) -> KpiResult:
    enrolled = currently_enrolled(inputs.students)
    classified = [s for s in enrolled if s.has_industry_certification is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not enrolled:
        missing.append("currently_enrolled_students")
    if enrolled and not classified:
        missing.append("students.has_industry_certification")
    if classified and len(classified) < len(enrolled):
        warnings.append(
            f"{len(enrolled) - len(classified)}/{len(enrolled)} "
            "enrolled students missing has_industry_certification"
        )

    if not classified:
        return _result(
            kpi_id="ACA-08",
            name="Professional Certifications (students)",
            formula="100 * count(has_industry_certification=True) / count(enrolled with flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"enrolled_with_flag": 0},
        )

    certified = sum(1 for s in classified if s.has_industry_certification)
    value = 100.0 * certified / len(classified)
    return _result(
        kpi_id="ACA-08",
        name="Professional Certifications (students)",
        formula="100 * count(has_industry_certification=True) / count(enrolled with flag)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={"enrolled_with_flag": len(classified), "certified": certified},
    )


# ---------------------------------------------------------------------------
# ACA-09 Accredited Programs
# ---------------------------------------------------------------------------


def aca_09_accredited_programs(inputs: InstitutionAcademicInputs) -> KpiResult:
    active = [p for p in inputs.programs if p.is_active]
    classified = [p for p in active if p.has_external_accreditation is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not active:
        missing.append("active_programs")
    if active and not classified:
        missing.append("programs.has_external_accreditation")
    if classified and len(classified) < len(active):
        warnings.append(
            f"{len(active) - len(classified)}/{len(active)} "
            "active programs missing has_external_accreditation"
        )

    if not classified:
        return _result(
            kpi_id="ACA-09",
            name="Accredited Programs",
            formula="100 * count(programs.has_external_accreditation=True) / count(active programs with flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"programs_with_flag": 0},
        )

    accredited = sum(1 for p in classified if p.has_external_accreditation)
    value = 100.0 * accredited / len(classified)
    return _result(
        kpi_id="ACA-09",
        name="Accredited Programs",
        formula="100 * count(programs.has_external_accreditation=True) / count(active programs with flag)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={"programs_with_flag": len(classified), "accredited": accredited},
    )


# ---------------------------------------------------------------------------
# ACA-10 Average Grade Performance Index
# ---------------------------------------------------------------------------


def aca_10_average_grade_performance(inputs: InstitutionAcademicInputs) -> KpiResult:
    with_gpa = [s for s in inputs.students if s.gpa is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not inputs.students:
        missing.append("students")
    if inputs.students and not with_gpa:
        missing.append("students.gpa")
    if with_gpa and len(with_gpa) < len(inputs.students):
        warnings.append(
            f"{len(inputs.students) - len(with_gpa)}/{len(inputs.students)} students missing gpa"
        )

    if not with_gpa:
        return _result(
            kpi_id="ACA-10",
            name="Average Grade Performance Index",
            formula="mean(student.gpa)",
            unit="GPA",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"students_with_gpa": 0},
        )

    mean_gpa = sum(s.gpa for s in with_gpa) / len(with_gpa)  # type: ignore[arg-type]
    return _result(
        kpi_id="ACA-10",
        name="Average Grade Performance Index",
        formula="mean(student.gpa)",
        unit="GPA",
        inputs=inputs,
        value=mean_gpa,
        missing=[],
        warnings=warnings,
        used={"students_with_gpa": len(with_gpa)},
    )


# ---------------------------------------------------------------------------
# ACA-11 Absenteeism Rate (students)
# ---------------------------------------------------------------------------


def aca_11_absenteeism_rate(inputs: InstitutionAcademicInputs) -> KpiResult:
    classified = [
        m
        for m in inputs.modules
        if m.scheduled_class_hours and m.unexcused_absence_hours is not None
    ]
    missing: list[str] = []
    warnings: list[str] = []

    if not inputs.modules:
        missing.append("modules")
    if inputs.modules and not classified:
        missing.append("modules.scheduled_class_hours / modules.unexcused_absence_hours")
    if classified and len(classified) < len(inputs.modules):
        warnings.append(
            f"{len(inputs.modules) - len(classified)}/{len(inputs.modules)} "
            "modules missing absence/schedule hours"
        )

    if not classified:
        return _result(
            kpi_id="ACA-11",
            name="Absenteeism Rate (students)",
            formula="100 * sum(unexcused_absence_hours) / sum(scheduled_class_hours)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"modules_with_data": 0},
        )

    absent = sum(m.unexcused_absence_hours or 0 for m in classified)
    scheduled = sum(m.scheduled_class_hours or 0 for m in classified)
    value = 100.0 * absent / scheduled if scheduled else None
    return _result(
        kpi_id="ACA-11",
        name="Absenteeism Rate (students)",
        formula="100 * sum(unexcused_absence_hours) / sum(scheduled_class_hours)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "modules_with_data": len(classified),
            "total_absent_hours": absent,
            "total_scheduled_hours": scheduled,
        },
    )


# ---------------------------------------------------------------------------
# ACA-12 Weak Student Remediation Rate - ISO 21001
# ---------------------------------------------------------------------------


def aca_12_remediation_rate(inputs: InstitutionAcademicInputs) -> KpiResult:
    classified = [s for s in inputs.students if s.is_at_risk is not None]
    at_risk = [s for s in classified if s.is_at_risk]
    missing: list[str] = []
    warnings: list[str] = []

    if not inputs.students:
        missing.append("students")
    if inputs.students and not classified:
        missing.append("students.is_at_risk")
    if classified and len(classified) < len(inputs.students):
        warnings.append(
            f"{len(inputs.students) - len(classified)}/{len(inputs.students)} "
            "students missing is_at_risk"
        )

    if not at_risk:
        # Either there's no at-risk population, or we don't know who's at risk.
        # Distinguish: if classified but none at risk, that's a valid 0/0 → None.
        msg = "no students flagged is_at_risk=True" if classified else "students.is_at_risk"
        if not classified:
            missing.append(msg)
        else:
            warnings.append(msg)
        return _result(
            kpi_id="ACA-12",
            name="Weak Student Remediation Rate",
            formula="100 * count(at_risk AND received_support) / count(at_risk)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"at_risk_students": 0},
        )

    with_support_flag = [s for s in at_risk if s.received_remediation_support is not None]
    if not with_support_flag:
        missing.append("students.received_remediation_support")
        return _result(
            kpi_id="ACA-12",
            name="Weak Student Remediation Rate",
            formula="100 * count(at_risk AND received_support) / count(at_risk)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"at_risk_students": len(at_risk), "with_support_flag": 0},
        )

    if len(with_support_flag) < len(at_risk):
        warnings.append(
            f"{len(at_risk) - len(with_support_flag)}/{len(at_risk)} "
            "at-risk students missing received_remediation_support"
        )

    supported = sum(1 for s in with_support_flag if s.received_remediation_support)
    value = 100.0 * supported / len(with_support_flag)
    return _result(
        kpi_id="ACA-12",
        name="Weak Student Remediation Rate",
        formula="100 * count(at_risk AND received_support) / count(at_risk)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "at_risk_students": len(at_risk),
            "with_support_flag": len(with_support_flag),
            "supported": supported,
        },
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

DOMAIN_B_CALCULATORS: list[Callable[[InstitutionAcademicInputs], KpiResult]] = [
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
]
