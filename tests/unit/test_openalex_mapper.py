"""Unit tests for the OpenAlex → domain mapper.

Pure mapping tests — no network. Fixtures mirror the shape returned by the
real OpenAlex API as documented at https://docs.openalex.org/api-entities/works.
"""

from __future__ import annotations

import pytest

from backend.integrations.openalex import (
    _faculty_from_openalex,
    _publication_from_work,
    _short_id,
)


def test_short_id_strips_url():
    assert _short_id("https://openalex.org/A12345") == "A12345"
    assert _short_id("A12345") == "A12345"


# ---------------------------------------------------------------------------
# _publication_from_work
# ---------------------------------------------------------------------------


def _work(**overrides) -> dict:
    base = {
        "id": "https://openalex.org/W1",
        "title": "Sample paper",
        "publication_year": 2024,
        "cited_by_count": 12,
        "type": "article",
        "open_access": {"is_oa": True, "oa_url": "https://example.org/p.pdf"},
        "authorships": [
            {
                "author": {"id": "https://openalex.org/A1", "display_name": "Sofiane Ouni"},
                "countries": ["TN"],
                "institutions": [{"country_code": "TN"}],
            },
            {
                "author": {"id": "https://openalex.org/A2", "display_name": "Coauthor"},
                "countries": ["FR"],
                "institutions": [{"country_code": "FR"}],
            },
        ],
        "cited_by_percentile_year": {"min": 99.4, "max": 99.7},
        "doi": "https://doi.org/10.1000/xyz",
    }
    base.update(overrides)
    return base


def test_publication_basic_fields():
    p = _publication_from_work(_work(), target_author_id="A1")
    assert p.title == "Sample paper"
    assert p.year == 2024
    assert p.citation_count == 12
    assert p.is_open_access is True
    assert p.is_peer_reviewed is True
    assert p.doi == "10.1000/xyz"
    assert p.source == "openalex"


def test_publication_collects_coauthor_countries():
    p = _publication_from_work(_work(), target_author_id="A1")
    assert p.coauthor_countries == ["FR", "TN"]  # sorted


def test_publication_top_1pct_flag():
    p = _publication_from_work(_work(), target_author_id="A1")
    assert p.field_top_1pct is True

    not_top = _work(cited_by_percentile_year={"min": 75.0, "max": 80.0})
    assert _publication_from_work(not_top, target_author_id="A1").field_top_1pct is False

    no_pct = _work(cited_by_percentile_year=None)
    assert _publication_from_work(no_pct, target_author_id="A1").field_top_1pct is None


def test_publication_missing_oa_flag():
    p = _publication_from_work(_work(open_access=None), target_author_id="A1")
    assert p.is_open_access is None


def test_publication_non_peer_reviewed_type():
    p = _publication_from_work(_work(type="dataset"), target_author_id="A1")
    assert p.is_peer_reviewed is False


def test_publication_handles_missing_year_and_cites():
    bad = _work(publication_year=None, cited_by_count=None)
    p = _publication_from_work(bad, target_author_id="A1")
    assert p.year is None
    assert p.citation_count is None


def test_publication_no_country_data_yields_none():
    no_countries = _work(
        authorships=[
            {"author": {"id": "https://openalex.org/A1"}},
            {"author": {"id": "https://openalex.org/A2"}},
        ],
    )
    p = _publication_from_work(no_countries, target_author_id="A1")
    assert p.coauthor_countries is None


# ---------------------------------------------------------------------------
# _faculty_from_openalex
# ---------------------------------------------------------------------------


def test_faculty_assembled():
    author = {
        "id": "https://openalex.org/A1",
        "display_name": "Sofiane Ouni",
        "summary_stats": {"h_index": 14, "i10_index": 22},
        "works_count": 2,
        "cited_by_count": 50,
    }
    works = [
        _work(id="https://openalex.org/W1", publication_year=2024, cited_by_count=30),
        _work(id="https://openalex.org/W2", publication_year=2023, cited_by_count=20),
    ]
    fm = _faculty_from_openalex(
        author=author,
        works=works,
        faculty_id="insat-sofiane-ouni",
        fte_fraction=1.0,
        home_country="TN",
    )
    assert fm.full_name == "Sofiane Ouni"
    assert fm.h_index == 14
    assert fm.id == "insat-sofiane-ouni"
    assert len(fm.publications) == 2
    assert sum(p.citation_count or 0 for p in fm.publications) == 50
    assert all(p.coauthor_countries == ["FR", "TN"] for p in fm.publications)


def test_faculty_missing_summary_stats():
    fm = _faculty_from_openalex(
        author={"id": "x", "display_name": "Anon"},  # no summary_stats
        works=[],
        faculty_id="anon",
        fte_fraction=1.0,
        home_country="TN",
    )
    assert fm.h_index is None
    assert fm.publications == []
