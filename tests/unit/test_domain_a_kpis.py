"""Unit tests for Domain A (Research & Citations) KPI calculators.

Synthetic fixtures keep these tests fast and deterministic; the live Google
Scholar smoke test lives in `scripts/demo_domain_a_insat.py` instead.
"""

from __future__ import annotations

from datetime import date

import pytest

from backend.services.kpi_service.domain import (
    ConsultancyContract,
    DoctoralStudent,
    FacultyMember,
    FundedProject,
    InstitutionResearchInputs,
    Publication,
    compute_research_domain,
)
from backend.services.kpi_service.domain.research import (
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
)

PERIOD_START = date(2022, 1, 1)
PERIOD_END = date(2026, 12, 31)
# Five-year window for period_end=2026 is 2022..2026 inclusive.


def _inputs(**overrides) -> InstitutionResearchInputs:
    base = dict(
        institution_id="inst-1",
        institution_code="INSAT",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
        faculty=[],
        funded_projects=[],
        doctoral_students=[],
        consultancy_contracts=[],
    )
    base.update(overrides)
    return InstitutionResearchInputs(**base)


def _pub(year: int, citations: int | None = 0, **kw) -> Publication:
    return Publication(title=f"P{year}", year=year, citation_count=citations, **kw)


# ---------------------------------------------------------------------------
# RES-01
# ---------------------------------------------------------------------------


class TestRes01CitationsPerFaculty:
    def test_basic(self):
        f = FacultyMember(
            id="f1",
            full_name="A",
            publications=[_pub(2024, 50), _pub(2023, 30), _pub(2010, 999)],  # 2010 outside window
        )
        result = res_01_citations_per_faculty(_inputs(faculty=[f]))
        assert result.value == pytest.approx(80.0)
        assert result.is_complete
        assert result.inputs_used["window"] == [2022, 2026]

    def test_missing_fte(self):
        result = res_01_citations_per_faculty(_inputs(faculty=[]))
        assert result.value is None
        assert "active_faculty_fte" in result.missing_fields

    def test_partial_citation_data_warns(self):
        f = FacultyMember(
            id="f1",
            full_name="A",
            publications=[_pub(2024, 50), _pub(2025, None)],
        )
        result = res_01_citations_per_faculty(_inputs(faculty=[f]))
        assert result.value == pytest.approx(50.0)
        assert any("missing citation_count" in w for w in result.warnings)
        assert not result.is_complete

    def test_inactive_faculty_excluded(self):
        active = FacultyMember(id="a", full_name="A", publications=[_pub(2025, 10)])
        inactive = FacultyMember(
            id="b", full_name="B", is_active=False, publications=[_pub(2025, 1000)]
        )
        result = res_01_citations_per_faculty(_inputs(faculty=[active, inactive]))
        assert result.value == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# RES-02
# ---------------------------------------------------------------------------


class TestRes02HIndexMedian:
    def test_median_of_three(self):
        faculty = [
            FacultyMember(id=str(i), full_name=str(i), h_index=h)
            for i, h in enumerate([5, 12, 30])
        ]
        result = res_02_h_index_median(_inputs(faculty=faculty))
        assert result.value == 12.0
        assert result.is_complete

    def test_single_faculty(self):
        f = FacultyMember(id="f1", full_name="Only", h_index=18)
        result = res_02_h_index_median(_inputs(faculty=[f]))
        assert result.value == 18.0

    def test_all_missing(self):
        f = FacultyMember(id="f1", full_name="A", h_index=None)
        result = res_02_h_index_median(_inputs(faculty=[f]))
        assert result.value is None
        assert "faculty.h_index" in result.missing_fields

    def test_partial_missing_warns(self):
        faculty = [
            FacultyMember(id="a", full_name="A", h_index=10),
            FacultyMember(id="b", full_name="B", h_index=None),
        ]
        result = res_02_h_index_median(_inputs(faculty=faculty))
        assert result.value == 10.0
        assert any("missing h_index" in w for w in result.warnings)
        assert not result.is_complete


# ---------------------------------------------------------------------------
# RES-03
# ---------------------------------------------------------------------------


class TestRes03PubsPerFaculty:
    def test_counts_in_window(self):
        f = FacultyMember(
            id="f", full_name="F",
            publications=[_pub(2024), _pub(2023), _pub(2020)],  # 2020 outside window
        )
        result = res_03_publications_per_faculty(_inputs(faculty=[f]))
        assert result.value == 2.0

    def test_excludes_non_peer_reviewed(self):
        f = FacultyMember(
            id="f", full_name="F",
            publications=[_pub(2024), _pub(2024, is_peer_reviewed=False)],
        )
        result = res_03_publications_per_faculty(_inputs(faculty=[f]))
        assert result.value == 1.0


# ---------------------------------------------------------------------------
# RES-04
# ---------------------------------------------------------------------------


class TestRes04InternationalNetwork:
    def test_pct_calculated(self):
        f = FacultyMember(
            id="f", full_name="F",
            publications=[
                _pub(2024, coauthor_countries=["TN", "FR"]),
                _pub(2024, coauthor_countries=["TN"]),
                _pub(2024, coauthor_countries=["TN", "DE"]),
            ],
        )
        result = res_04_international_research_network(_inputs(faculty=[f]))
        assert result.value == pytest.approx(2 / 3 * 100)

    def test_no_country_data_is_uncomputable(self):
        f = FacultyMember(
            id="f", full_name="F",
            publications=[_pub(2024), _pub(2025)],  # coauthor_countries=None
        )
        result = res_04_international_research_network(_inputs(faculty=[f]))
        assert result.value is None
        assert "publications.coauthor_countries" in result.missing_fields

    def test_partial_country_data_warns(self):
        f = FacultyMember(
            id="f", full_name="F",
            publications=[
                _pub(2024, coauthor_countries=["TN", "US"]),
                _pub(2024),  # missing
            ],
        )
        result = res_04_international_research_network(_inputs(faculty=[f]))
        assert result.value == 100.0  # only 1 classified, and it's international
        assert any("missing coauthor_countries" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# RES-05 / 06
# ---------------------------------------------------------------------------


class TestRes05Res06Funding:
    def test_res_05_counts_active_external(self):
        projects = [
            FundedProject(id="p1", title="A", amount_tnd=10000, is_external=True, is_active=True),
            FundedProject(id="p2", title="B", amount_tnd=5000, is_external=True, is_active=False),
            FundedProject(id="p3", title="C", amount_tnd=20000, is_external=False, is_active=True),
        ]
        result = res_05_funded_rd_projects(_inputs(funded_projects=projects))
        assert result.value == 1.0

    def test_res_06_income_per_fte(self):
        f = FacultyMember(id="f", full_name="F", fte_fraction=0.5)
        projects = [
            FundedProject(id="p1", title="A", amount_tnd=10000, is_external=True, is_active=True),
            FundedProject(id="p2", title="B", amount_tnd=20000, is_external=True, is_active=False),
        ]
        result = res_06_research_income_per_faculty(_inputs(faculty=[f], funded_projects=projects))
        assert result.value == pytest.approx(60000.0)  # (10000+20000) / 0.5

    def test_res_06_warns_on_missing_amount(self):
        f = FacultyMember(id="f", full_name="F")
        projects = [
            FundedProject(id="p1", title="A", amount_tnd=None, is_external=True, is_active=True),
        ]
        result = res_06_research_income_per_faculty(_inputs(faculty=[f], funded_projects=projects))
        assert any("missing amount_tnd" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# RES-07 / 08
# ---------------------------------------------------------------------------


class TestRes07Res08Doctoral:
    def test_res_07_active_phd_per_fte(self):
        f = FacultyMember(id="f", full_name="F")
        students = [
            DoctoralStudent(id="s1", is_active=True),
            DoctoralStudent(id="s2", is_active=True),
            DoctoralStudent(id="s3", is_active=False),
        ]
        result = res_07_phd_students_per_faculty(_inputs(faculty=[f], doctoral_students=students))
        assert result.value == 2.0

    def test_res_08_awarded_in_period(self):
        f = FacultyMember(id="f", full_name="F")
        students = [
            DoctoralStudent(id="s1", is_active=False, awarded_date=date(2026, 6, 1)),
            DoctoralStudent(id="s2", is_active=False, awarded_date=date(2025, 6, 1)),  # outside
            DoctoralStudent(id="s3", is_active=True),
        ]
        result = res_08_doctorates_awarded_ratio(_inputs(faculty=[f], doctoral_students=students))
        assert result.value == 1.0


# ---------------------------------------------------------------------------
# RES-09
# ---------------------------------------------------------------------------


class TestRes09HighCitationPapers:
    def test_no_benchmark_data_is_uncomputable(self):
        f = FacultyMember(id="f", full_name="F", publications=[_pub(2024, 100)])
        result = res_09_high_citation_papers(_inputs(faculty=[f]))
        assert result.value is None
        assert any("field_top_1pct" in m for m in result.missing_fields)

    def test_with_flag(self):
        f = FacultyMember(
            id="f", full_name="F",
            publications=[
                _pub(2024, 100, field_top_1pct=True),
                _pub(2024, 5, field_top_1pct=False),
                _pub(2024, 20, field_top_1pct=True),
            ],
        )
        result = res_09_high_citation_papers(_inputs(faculty=[f]))
        assert result.value == 2.0


# ---------------------------------------------------------------------------
# RES-10
# ---------------------------------------------------------------------------


class TestRes10ConsultancyRevenue:
    def test_sums_in_period(self):
        contracts = [
            ConsultancyContract(id="c1", revenue_tnd=15000, contract_date=date(2026, 3, 1)),
            ConsultancyContract(id="c2", revenue_tnd=5000, contract_date=date(2025, 12, 1)),
        ]
        result = res_10_consultancy_revenue(_inputs(consultancy_contracts=contracts))
        assert result.value == 15000.0

    def test_missing_data(self):
        result = res_10_consultancy_revenue(_inputs())
        assert "consultancy_contracts" in result.missing_fields


# ---------------------------------------------------------------------------
# RES-11
# ---------------------------------------------------------------------------


class TestRes11OpenAccess:
    def test_pct(self):
        f = FacultyMember(
            id="f", full_name="F",
            publications=[
                _pub(2024, is_open_access=True),
                _pub(2024, is_open_access=False),
                _pub(2025, is_open_access=True),
                _pub(2025, is_open_access=True),
            ],
        )
        result = res_11_open_access_rate(_inputs(faculty=[f]))
        assert result.value == 75.0

    def test_no_oa_flag_is_uncomputable(self):
        f = FacultyMember(id="f", full_name="F", publications=[_pub(2024)])
        result = res_11_open_access_rate(_inputs(faculty=[f]))
        assert result.value is None
        assert "publications.is_open_access" in result.missing_fields


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def test_dispatcher_runs_all_eleven():
    results = compute_research_domain(_inputs())
    assert len(results) == 11
    assert {r.kpi_id for r in results} == {
        "RES-01", "RES-02", "RES-03", "RES-04", "RES-05",
        "RES-06", "RES-07", "RES-08", "RES-09", "RES-10", "RES-11",
    }
    # With empty inputs, every KPI is either missing or trivially zero.
    for r in results:
        if r.value is None:
            assert r.missing_fields, f"{r.kpi_id} returned None without missing_fields"


def test_sofiane_ouni_style_fixture():
    """Plausible single-professor INSAT fixture mirroring a Google Scholar payload.

    Replace `h_index` / pubs with the cached real values when running the demo;
    here we just verify the result envelope shapes.
    """
    professor = FacultyMember(
        id="insat-sofiane-ouni",
        full_name="Sofiane Ouni",
        h_index=12,
        fte_fraction=1.0,
        home_country="TN",
        publications=[
            _pub(2024, 35),
            _pub(2023, 28),
            _pub(2022, 41),
            _pub(2021, 19),  # outside 2022..2026 window? 2021 < 2022 → yes outside
            _pub(2025, 8),
        ],
    )
    inputs = _inputs(faculty=[professor])
    results = {r.kpi_id: r for r in compute_research_domain(inputs)}

    # RES-01: only pubs in [2022, 2026] count → 35 + 28 + 41 + 8 = 112
    assert results["RES-01"].value == pytest.approx(112.0)
    # RES-02: median of single value is that value
    assert results["RES-02"].value == 12.0
    # RES-03: 4 pubs in window, FTE=1
    assert results["RES-03"].value == 4.0
    # KPIs with no source data should be flagged, not crash
    for kpi_id in ("RES-04", "RES-05", "RES-06", "RES-07", "RES-08", "RES-09", "RES-10", "RES-11"):
        assert results[kpi_id].value is None or results[kpi_id].is_estimated, kpi_id
        assert results[kpi_id].missing_fields, kpi_id
