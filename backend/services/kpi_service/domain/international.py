"""Domain D - Internationalization KPI calculators (INT-01..INT-06).

A faculty member is "international" when *either* their nationality OR their
highest-degree country differs from the institution's country. If only one
of the two signals is known we use it (and warn). If neither is known the
faculty member is excluded from the denominator and counted as unclassified.
"""

from __future__ import annotations

from collections.abc import Callable

from .inputs import (
    FacultyMember,
    InstitutionInternationalInputs,
    Student,
    currently_enrolled,
)
from .result import KpiResult, build_kpi_result

DOMAIN = "INTERNATIONAL"


def _result(*, inputs: InstitutionInternationalInputs, **kw) -> KpiResult:
    return build_kpi_result(inputs, DOMAIN, **kw)


def _faculty_is_international(f: FacultyMember, home: str) -> bool | None:
    """Three-valued logic: True / False / None (unknown).

    Returns True when at least one signal indicates a foreign affiliation,
    False when both known signals agree on home country, and None when we
    have no signals at all.
    """
    nat = f.nationality_country
    deg = f.highest_degree_country
    if nat is None and deg is None:
        return None
    if nat is not None and nat != home:
        return True
    if deg is not None and deg != home:
        return True
    return False


# ---------------------------------------------------------------------------
# INT-01 International Faculty Ratio - QS 5%
# ---------------------------------------------------------------------------


def int_01_international_faculty_ratio(inputs: InstitutionInternationalInputs) -> KpiResult:
    active = [f for f in inputs.faculty if f.is_active]
    classified: list[tuple[FacultyMember, bool]] = []
    partial: list[FacultyMember] = []  # only one of two signals available

    for f in active:
        verdict = _faculty_is_international(f, inputs.home_country)
        if verdict is None:
            continue
        classified.append((f, verdict))
        if (f.nationality_country is None) ^ (f.highest_degree_country is None):
            partial.append(f)

    missing: list[str] = []
    warnings: list[str] = []

    if not active:
        missing.append("active_faculty")
    elif not classified:
        missing.append("faculty.nationality_country / faculty.highest_degree_country")
    elif len(classified) < len(active):
        warnings.append(
            f"{len(active) - len(classified)}/{len(active)} active faculty "
            "missing both nationality and degree country"
        )
    if partial:
        warnings.append(
            f"{len(partial)}/{len(classified)} classified faculty had only one signal "
            "(used the available one)"
        )

    if not classified:
        return _result(
            kpi_id="INT-01",
            name="International Faculty Ratio",
            formula="100 * count(international faculty) / count(active faculty with signal)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"classified": 0},
        )

    international = sum(1 for _, v in classified if v)
    value = 100.0 * international / len(classified)
    return _result(
        kpi_id="INT-01",
        name="International Faculty Ratio",
        formula="100 * count(international faculty) / count(active faculty with signal)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "active_faculty": len(active),
            "classified": len(classified),
            "international": international,
            "home_country": inputs.home_country,
        },
    )


# ---------------------------------------------------------------------------
# INT-02 International Student Ratio - QS 5%
# ---------------------------------------------------------------------------


def int_02_international_student_ratio(inputs: InstitutionInternationalInputs) -> KpiResult:
    enrolled = currently_enrolled(inputs.students)
    classified = [s for s in enrolled if s.nationality_country is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not enrolled:
        if not inputs.students:
            missing.append("students")
        else:
            warnings.append("no students with status in {ACTIVE, REPEATING}")
    if enrolled and not classified:
        missing.append("students.nationality_country")
    if classified and len(classified) < len(enrolled):
        warnings.append(
            f"{len(enrolled) - len(classified)}/{len(enrolled)} enrolled students "
            "missing nationality_country"
        )

    if not classified:
        return _result(
            kpi_id="INT-02",
            name="International Student Ratio",
            formula="100 * count(students.nationality_country != home) / count(enrolled with nationality)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"enrolled_with_nationality": 0},
        )

    foreign = sum(1 for s in classified if s.nationality_country != inputs.home_country)
    value = 100.0 * foreign / len(classified)
    return _result(
        kpi_id="INT-02",
        name="International Student Ratio",
        formula="100 * count(students.nationality_country != home) / count(enrolled with nationality)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "currently_enrolled": len(enrolled),
            "with_nationality": len(classified),
            "foreign": foreign,
            "home_country": inputs.home_country,
        },
    )


# ---------------------------------------------------------------------------
# INT-03 Outgoing Student Mobility
# ---------------------------------------------------------------------------


def _mobility_rate(
    inputs: InstitutionInternationalInputs,
    *,
    kpi_id: str,
    name: str,
    formula: str,
    flag_attr: str,
) -> KpiResult:
    enrolled = currently_enrolled(inputs.students)
    classified = [s for s in enrolled if getattr(s, flag_attr) is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not enrolled:
        if not inputs.students:
            missing.append("students")
        else:
            warnings.append("no students with status in {ACTIVE, REPEATING}")
    if enrolled and not classified:
        missing.append(f"students.{flag_attr}")
    if classified and len(classified) < len(enrolled):
        warnings.append(
            f"{len(enrolled) - len(classified)}/{len(enrolled)} enrolled students "
            f"missing {flag_attr}"
        )

    if not classified:
        return _result(
            kpi_id=kpi_id,
            name=name,
            formula=formula,
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"enrolled_with_flag": 0},
        )

    on_mobility = sum(1 for s in classified if getattr(s, flag_attr))
    value = 100.0 * on_mobility / len(classified)
    return _result(
        kpi_id=kpi_id,
        name=name,
        formula=formula,
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "currently_enrolled": len(enrolled),
            "with_flag": len(classified),
            "on_mobility": on_mobility,
        },
    )


def int_03_outgoing_student_mobility(inputs: InstitutionInternationalInputs) -> KpiResult:
    return _mobility_rate(
        inputs,
        kpi_id="INT-03",
        name="Outgoing Student Mobility",
        formula="100 * count(students.is_outgoing_exchange=True) / count(enrolled with flag)",
        flag_attr="is_outgoing_exchange",
    )


# ---------------------------------------------------------------------------
# INT-04 Incoming Student Mobility
# ---------------------------------------------------------------------------


def int_04_incoming_student_mobility(inputs: InstitutionInternationalInputs) -> KpiResult:
    return _mobility_rate(
        inputs,
        kpi_id="INT-04",
        name="Incoming Student Mobility",
        formula="100 * count(students.is_incoming_exchange=True) / count(enrolled with flag)",
        flag_attr="is_incoming_exchange",
    )


# ---------------------------------------------------------------------------
# INT-05 International Partnership Agreements - QS IRN proxy
# ---------------------------------------------------------------------------


def int_05_international_partnerships(inputs: InstitutionInternationalInputs) -> KpiResult:
    partnerships = inputs.academic_partnerships
    missing: list[str] = []
    warnings: list[str] = []

    if not partnerships:
        missing.append("academic_partnerships")
        return _result(
            kpi_id="INT-05",
            name="International Partnership Agreements",
            formula="count(academic_partnerships where is_active AND partner_country != home)",
            unit="agreements",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"partnerships_known": 0},
        )

    active = [p for p in partnerships if p.is_active]
    classified = [p for p in active if p.partner_country is not None]
    if active and len(classified) < len(active):
        warnings.append(
            f"{len(active) - len(classified)}/{len(active)} active partnerships "
            "missing partner_country"
        )

    international = sum(
        1 for p in classified if p.partner_country != inputs.home_country
    )
    return _result(
        kpi_id="INT-05",
        name="International Partnership Agreements",
        formula="count(academic_partnerships where is_active AND partner_country != home)",
        unit="agreements",
        inputs=inputs,
        value=float(international),
        missing=[],
        warnings=warnings,
        used={
            "partnerships_known": len(partnerships),
            "active": len(active),
            "with_country": len(classified),
            "international": international,
            "home_country": inputs.home_country,
        },
    )


# ---------------------------------------------------------------------------
# INT-06 Foreign Language Program Rate
# ---------------------------------------------------------------------------


def int_06_foreign_language_program_rate(inputs: InstitutionInternationalInputs) -> KpiResult:
    active = [p for p in inputs.programs if p.is_active]
    classified = [p for p in active if p.teaching_languages is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not active:
        if not inputs.programs:
            missing.append("programs")
        else:
            missing.append("active_programs")
    elif not classified:
        missing.append("programs.teaching_languages")
    elif len(classified) < len(active):
        warnings.append(
            f"{len(active) - len(classified)}/{len(active)} active programs "
            "missing teaching_languages"
        )

    if not classified:
        return _result(
            kpi_id="INT-06",
            name="Foreign Language Program Rate",
            formula=(
                "100 * count(programs with any teaching_language not in official_languages) "
                "/ count(active programs with languages set)"
            ),
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"classified_programs": 0},
        )

    official = {lang.lower() for lang in inputs.official_languages}
    foreign = sum(
        1
        for p in classified
        if p.teaching_languages
        and any(lang.lower() not in official for lang in p.teaching_languages)
    )
    value = 100.0 * foreign / len(classified)
    return _result(
        kpi_id="INT-06",
        name="Foreign Language Program Rate",
        formula=(
            "100 * count(programs with any teaching_language not in official_languages) "
            "/ count(active programs with languages set)"
        ),
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "active_programs": len(active),
            "classified_programs": len(classified),
            "foreign_language_programs": foreign,
            "official_languages": sorted(official),
        },
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

DOMAIN_D_CALCULATORS: list[Callable[[InstitutionInternationalInputs], KpiResult]] = [
    int_01_international_faculty_ratio,
    int_02_international_student_ratio,
    int_03_outgoing_student_mobility,
    int_04_incoming_student_mobility,
    int_05_international_partnerships,
    int_06_foreign_language_program_rate,
]
