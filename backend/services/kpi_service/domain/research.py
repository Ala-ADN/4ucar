"""Domain A — Research & Citations KPI calculators (RES-01..RES-11).

Each function:
    - takes an `InstitutionResearchInputs`
    - returns a `KpiResult` with `value`, `is_complete`, `missing_fields`,
      `warnings`, and `inputs_used`
    - never raises on missing data; produces an explicit "uncomputable" result

5-year-window KPIs (RES-01, RES-03, RES-04, RES-09, RES-11) use the rolling
window ending at `period_end.year` (inclusive). Single-period KPIs (RES-05,
RES-08, RES-10) use `[period_start, period_end]`.
"""

from __future__ import annotations

from collections.abc import Callable
from statistics import median

from .inputs import (
    InstitutionResearchInputs,
    Publication,
    five_year_window,
    total_active_fte,
)
from .result import KpiResult, build_kpi_result

DOMAIN = "RESEARCH"


def _pubs_in_window(inputs: InstitutionResearchInputs) -> list[Publication]:
    first, last = five_year_window(inputs.period_end)
    return [
        p
        for f in inputs.faculty
        if f.is_active
        for p in f.publications
        if p.year is not None and first <= p.year <= last
    ]


def _result(*, inputs: InstitutionResearchInputs, **kw) -> KpiResult:
    return build_kpi_result(inputs, DOMAIN, **kw)


# ---------------------------------------------------------------------------
# RES-01 Citations per Faculty (5y window) — QS 20% / THE 30%
# ---------------------------------------------------------------------------


def res_01_citations_per_faculty(inputs: InstitutionResearchInputs) -> KpiResult:
    fte = total_active_fte(inputs.faculty)
    pubs = _pubs_in_window(inputs)
    missing: list[str] = []
    warnings: list[str] = []

    if fte == 0:
        missing.append("active_faculty_fte")

    pubs_with_cites = [p for p in pubs if p.citation_count is not None]
    if pubs and len(pubs_with_cites) < len(pubs):
        warnings.append(
            f"{len(pubs) - len(pubs_with_cites)}/{len(pubs)} publications missing citation_count"
        )
    citations = sum(p.citation_count or 0 for p in pubs_with_cites)
    value = citations / fte if fte > 0 else None

    first, last = five_year_window(inputs.period_end)
    return _result(
        kpi_id="RES-01",
        name="Citations per Faculty",
        formula="sum(citations to publications in [Y-4, Y]) / active FTE faculty",
        unit="citations/FTE",
        inputs=inputs,
        value=value,
        missing=missing,
        warnings=warnings,
        used={
            "window": [first, last],
            "publications_in_window": len(pubs),
            "publications_with_citation_count": len(pubs_with_cites),
            "total_citations": citations,
            "active_fte": fte,
        },
    )


# ---------------------------------------------------------------------------
# RES-02 H-index (faculty median)
# ---------------------------------------------------------------------------


def res_02_h_index_median(inputs: InstitutionResearchInputs) -> KpiResult:
    active = [f for f in inputs.faculty if f.is_active]
    h_indices = [f.h_index for f in active if f.h_index is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not active:
        missing.append("active_faculty")
    if active and not h_indices:
        missing.append("faculty.h_index")

    if active and len(h_indices) < len(active):
        warnings.append(
            f"{len(active) - len(h_indices)}/{len(active)} active faculty missing h_index"
        )

    value = float(median(h_indices)) if h_indices else None

    return _result(
        kpi_id="RES-02",
        name="H-index (faculty median)",
        formula="median(h_index) over active faculty",
        unit="index",
        inputs=inputs,
        value=value,
        missing=missing,
        warnings=warnings,
        used={
            "active_faculty": len(active),
            "faculty_with_h_index": len(h_indices),
            "min": min(h_indices) if h_indices else None,
            "max": max(h_indices) if h_indices else None,
        },
    )


# ---------------------------------------------------------------------------
# RES-03 Publications per Faculty (5y window) — THE 6%
# ---------------------------------------------------------------------------


def res_03_publications_per_faculty(inputs: InstitutionResearchInputs) -> KpiResult:
    fte = total_active_fte(inputs.faculty)
    pubs = [p for p in _pubs_in_window(inputs) if p.is_peer_reviewed]
    missing: list[str] = []
    if fte == 0:
        missing.append("active_faculty_fte")

    value = len(pubs) / fte if fte > 0 else None
    first, last = five_year_window(inputs.period_end)
    return _result(
        kpi_id="RES-03",
        name="Publications per Faculty",
        formula="count(peer-reviewed publications in [Y-4, Y]) / active FTE faculty",
        unit="publications/FTE",
        inputs=inputs,
        value=value,
        missing=missing,
        warnings=[],
        used={
            "window": [first, last],
            "peer_reviewed_publications": len(pubs),
            "active_fte": fte,
        },
    )


# ---------------------------------------------------------------------------
# RES-04 International Research Network Score (5y window) — QS 5%
# ---------------------------------------------------------------------------


def res_04_international_research_network(inputs: InstitutionResearchInputs) -> KpiResult:
    pubs = _pubs_in_window(inputs)
    missing: list[str] = []
    warnings: list[str] = []

    if not pubs:
        missing.append("publications_in_window")
        return _result(
            kpi_id="RES-04",
            name="International Research Network Score",
            formula="100 * count(pubs with >=1 international coauthor) / total pubs",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"publications_in_window": 0},
        )

    pubs_with_country_data = [p for p in pubs if p.coauthor_countries is not None]
    pubs_without = len(pubs) - len(pubs_with_country_data)
    if pubs_without:
        warnings.append(
            f"{pubs_without}/{len(pubs)} publications missing coauthor_countries"
        )

    if not pubs_with_country_data:
        missing.append("publications.coauthor_countries")
        return _result(
            kpi_id="RES-04",
            name="International Research Network Score",
            formula="100 * count(pubs with >=1 international coauthor) / total pubs",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"publications_in_window": len(pubs), "with_country_data": 0},
        )

    home = inputs.home_country
    international = sum(
        1
        for p in pubs_with_country_data
        if any(c and c != home for c in (p.coauthor_countries or []))
    )
    value = 100.0 * international / len(pubs_with_country_data)

    return _result(
        kpi_id="RES-04",
        name="International Research Network Score",
        formula="100 * count(pubs with >=1 international coauthor) / total pubs",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "publications_in_window": len(pubs),
            "with_country_data": len(pubs_with_country_data),
            "with_international_coauthor": international,
            "home_country": home,
        },
    )


# ---------------------------------------------------------------------------
# RES-05 Funded R&D Projects (count of active external) — THE Research income
# ---------------------------------------------------------------------------


def res_05_funded_rd_projects(inputs: InstitutionResearchInputs) -> KpiResult:
    active_external = [p for p in inputs.funded_projects if p.is_active and p.is_external]
    return _result(
        kpi_id="RES-05",
        name="Funded R&D Projects",
        formula="count(funded_projects where is_active AND is_external)",
        unit="projects",
        inputs=inputs,
        value=float(len(active_external)),
        missing=[] if inputs.funded_projects else ["funded_projects"],
        warnings=[],
        used={
            "total_projects_known": len(inputs.funded_projects),
            "active_external": len(active_external),
        },
    )


# ---------------------------------------------------------------------------
# RES-06 Research Income per Faculty (TND/FTE) — THE 6%
# ---------------------------------------------------------------------------


def res_06_research_income_per_faculty(inputs: InstitutionResearchInputs) -> KpiResult:
    fte = total_active_fte(inputs.faculty)
    missing: list[str] = []
    warnings: list[str] = []

    if fte == 0:
        missing.append("active_faculty_fte")

    external_with_amount = [
        p for p in inputs.funded_projects if p.is_external and p.amount_tnd is not None
    ]
    external_total = [p for p in inputs.funded_projects if p.is_external]
    if external_total and len(external_with_amount) < len(external_total):
        warnings.append(
            f"{len(external_total) - len(external_with_amount)}/{len(external_total)} "
            "external projects missing amount_tnd"
        )
    if not inputs.funded_projects:
        missing.append("funded_projects")

    income = sum(p.amount_tnd or 0.0 for p in external_with_amount)
    value = income / fte if fte > 0 else None

    return _result(
        kpi_id="RES-06",
        name="Research Income per Faculty",
        formula="sum(external_funding_tnd) / active FTE faculty",
        unit="TND/FTE",
        inputs=inputs,
        value=value,
        missing=missing,
        warnings=warnings,
        used={
            "external_projects": len(external_total),
            "external_total_tnd": income,
            "active_fte": fte,
        },
    )


# ---------------------------------------------------------------------------
# RES-07 PhD Students per Faculty — THE Doctoral Ratio proxy
# ---------------------------------------------------------------------------


def res_07_phd_students_per_faculty(inputs: InstitutionResearchInputs) -> KpiResult:
    fte = total_active_fte(inputs.faculty)
    missing: list[str] = []
    if fte == 0:
        missing.append("active_faculty_fte")
    if not inputs.doctoral_students:
        missing.append("doctoral_students")

    active = [s for s in inputs.doctoral_students if s.is_active]
    value = len(active) / fte if fte > 0 else None

    return _result(
        kpi_id="RES-07",
        name="PhD Students per Faculty",
        formula="count(active doctoral students) / active FTE faculty",
        unit="students/FTE",
        inputs=inputs,
        value=value,
        missing=missing,
        warnings=[],
        used={
            "active_phd_students": len(active),
            "total_phd_students_known": len(inputs.doctoral_students),
            "active_fte": fte,
        },
    )


# ---------------------------------------------------------------------------
# RES-08 Doctorates Awarded Ratio — THE Teaching 6%
# ---------------------------------------------------------------------------


def res_08_doctorates_awarded_ratio(inputs: InstitutionResearchInputs) -> KpiResult:
    fte = total_active_fte(inputs.faculty)
    missing: list[str] = []
    if fte == 0:
        missing.append("active_faculty_fte")
    if not inputs.doctoral_students:
        missing.append("doctoral_students")

    awarded = [
        s
        for s in inputs.doctoral_students
        if s.awarded_date is not None
        and inputs.period_start <= s.awarded_date <= inputs.period_end
    ]
    value = len(awarded) / fte if fte > 0 else None
    return _result(
        kpi_id="RES-08",
        name="Doctorates Awarded Ratio",
        formula="count(doctorates awarded in period) / active FTE faculty",
        unit="awards/FTE",
        inputs=inputs,
        value=value,
        missing=missing,
        warnings=[],
        used={
            "awarded_in_period": len(awarded),
            "active_fte": fte,
        },
    )


# ---------------------------------------------------------------------------
# RES-09 High-Citation Papers (top 1% by field) — THE Citations 30%
# ---------------------------------------------------------------------------


def res_09_high_citation_papers(inputs: InstitutionResearchInputs) -> KpiResult:
    pubs = _pubs_in_window(inputs)
    flagged = [p for p in pubs if p.field_top_1pct is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not pubs:
        missing.append("publications_in_window")
    if pubs and not flagged:
        # No publication carries the field-percentile flag — typically requires
        # SciVal/Scopus benchmark data which we don't have locally.
        missing.append("publications.field_top_1pct (Scopus/SciVal benchmark)")
    if flagged and len(flagged) < len(pubs):
        warnings.append(
            f"{len(pubs) - len(flagged)}/{len(pubs)} publications missing field_top_1pct flag"
        )

    if not flagged:
        return _result(
            kpi_id="RES-09",
            name="High-Citation Papers (top 1%)",
            formula="count(publications flagged in top 1% citations for their field)",
            unit="papers",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"publications_in_window": len(pubs)},
        )

    count = sum(1 for p in flagged if p.field_top_1pct)
    return _result(
        kpi_id="RES-09",
        name="High-Citation Papers (top 1%)",
        formula="count(publications flagged in top 1% citations for their field)",
        unit="papers",
        inputs=inputs,
        value=float(count),
        missing=[],
        warnings=warnings,
        used={
            "publications_in_window": len(pubs),
            "flagged_pubs": len(flagged),
            "top_1pct_count": count,
        },
    )


# ---------------------------------------------------------------------------
# RES-10 Consultancy Revenue (TND) — THE Research income
# ---------------------------------------------------------------------------


def res_10_consultancy_revenue(inputs: InstitutionResearchInputs) -> KpiResult:
    in_period = [
        c
        for c in inputs.consultancy_contracts
        if c.contract_date is not None
        and inputs.period_start <= c.contract_date <= inputs.period_end
    ]
    with_amount = [c for c in in_period if c.revenue_tnd is not None]
    warnings: list[str] = []
    missing: list[str] = []
    if not inputs.consultancy_contracts:
        missing.append("consultancy_contracts")
    if in_period and len(with_amount) < len(in_period):
        warnings.append(
            f"{len(in_period) - len(with_amount)}/{len(in_period)} contracts missing revenue_tnd"
        )

    revenue = sum(c.revenue_tnd or 0.0 for c in with_amount)
    return _result(
        kpi_id="RES-10",
        name="Consultancy Revenue",
        formula="sum(revenue_tnd of consultancy contracts in period)",
        unit="TND",
        inputs=inputs,
        value=revenue if (with_amount or not missing) else None,
        missing=missing,
        warnings=warnings,
        used={
            "contracts_in_period": len(in_period),
            "with_revenue": len(with_amount),
            "total_tnd": revenue,
        },
    )


# ---------------------------------------------------------------------------
# RES-11 Open Access Publication Rate (%) — Sustainability proxy
# ---------------------------------------------------------------------------


def res_11_open_access_rate(inputs: InstitutionResearchInputs) -> KpiResult:
    pubs = _pubs_in_window(inputs)
    classified = [p for p in pubs if p.is_open_access is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not pubs:
        missing.append("publications_in_window")
        return _result(
            kpi_id="RES-11",
            name="Open Access Publication Rate",
            formula="100 * count(pubs is_open_access=True) / total pubs in window",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"publications_in_window": 0},
        )

    if not classified:
        missing.append("publications.is_open_access")
        return _result(
            kpi_id="RES-11",
            name="Open Access Publication Rate",
            formula="100 * count(pubs is_open_access=True) / total pubs in window",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={
                "publications_in_window": len(pubs),
                "publications_with_oa_flag": 0,
            },
        )

    if len(classified) < len(pubs):
        warnings.append(
            f"{len(pubs) - len(classified)}/{len(pubs)} publications missing is_open_access flag"
        )

    oa = sum(1 for p in classified if p.is_open_access)
    value = 100.0 * oa / len(classified)
    return _result(
        kpi_id="RES-11",
        name="Open Access Publication Rate",
        formula="100 * count(pubs is_open_access=True) / total pubs in window",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "publications_in_window": len(pubs),
            "publications_with_oa_flag": len(classified),
            "open_access_count": oa,
        },
    )


# ---------------------------------------------------------------------------
# Registry — drives the dispatcher
# ---------------------------------------------------------------------------

DOMAIN_A_CALCULATORS: list[Callable[[InstitutionResearchInputs], KpiResult]] = [
    res_01_citations_per_faculty,
    res_02_h_index_median,
    res_03_publications_per_faculty,
    res_04_international_research_network,
    res_05_funded_rd_projects,
    res_06_research_income_per_faculty,
    res_07_phd_students_per_faculty,
    res_08_doctorates_awarded_ratio,
    res_09_high_citation_papers,
    res_10_consultancy_revenue,
    res_11_open_access_rate,
]
