"""Google Scholar adapter — turns a public author profile into a `FacultyMember`.

Google Scholar has no official API; we use the `scholarly` library which scrapes
the public website. Calls are slow and rate-limited, so the adapter caches its
output to JSON on disk.

Usage:
    fm = fetch_faculty_from_scholar(
        full_name="Sofiane Ouni",
        affiliation_hint="INSAT",
        cache_path=Path("data/cache/sofiane_ouni.json"),
    )
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import Any

from backend.services.kpi_service.domain.inputs import FacultyMember, Publication

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Cache layer
# ---------------------------------------------------------------------------


def _load_cache(cache_path: Path | None) -> dict | None:
    if cache_path and cache_path.exists():
        log.info("Loading Google Scholar profile from cache: %s", cache_path)
        return json.loads(cache_path.read_text(encoding="utf-8"))
    return None


def _save_cache(cache_path: Path | None, payload: dict) -> None:
    if cache_path is None:
        return
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    log.info("Saved Google Scholar profile to cache: %s", cache_path)


# ---------------------------------------------------------------------------
# Scholarly fetch
# ---------------------------------------------------------------------------


def _fetch_raw(full_name: str, affiliation_hint: str | None) -> dict:
    """Hit Google Scholar (via `scholarly`) and return the filled author dict."""
    try:
        from scholarly import scholarly  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "The `scholarly` package is required for live Google Scholar fetches. "
            "Install dependencies first: `uv pip install -e .`"
        ) from exc

    query = full_name if not affiliation_hint else f"{full_name} {affiliation_hint}"
    log.info("Searching Google Scholar for: %s", query)
    search = scholarly.search_author(query)
    try:
        author = next(search)
    except StopIteration as exc:
        raise LookupError(f"No Google Scholar author matched: {query!r}") from exc

    author = scholarly.fill(
        author,
        sections=["basics", "indices", "counts", "publications"],
    )
    return author


# ---------------------------------------------------------------------------
# Mapping
# ---------------------------------------------------------------------------


def _publication_from_scholarly(raw: dict) -> Publication:
    bib = raw.get("bib", {}) or {}
    year_raw = bib.get("pub_year") or bib.get("year")
    try:
        year: int | None = int(year_raw) if year_raw else None
    except (TypeError, ValueError):
        year = None
    citations = raw.get("num_citations")
    return Publication(
        title=bib.get("title", "<untitled>"),
        year=year,
        citation_count=int(citations) if isinstance(citations, int) else citations,
        is_peer_reviewed=True,
        is_open_access=None,
        coauthor_countries=None,
        field_top_1pct=None,
        source="google_scholar",
    )


def _faculty_from_scholarly(
    *,
    raw: dict,
    faculty_id: str,
    fte_fraction: float,
    home_country: str,
) -> FacultyMember:
    return FacultyMember(
        id=faculty_id,
        full_name=raw.get("name", "<unknown>"),
        is_active=True,
        fte_fraction=fte_fraction,
        h_index=raw.get("hindex"),
        home_country=home_country,
        publications=[_publication_from_scholarly(p) for p in raw.get("publications", [])],
    )


# ---------------------------------------------------------------------------
# Public entrypoint
# ---------------------------------------------------------------------------


def fetch_faculty_from_scholar(
    *,
    full_name: str,
    faculty_id: str | None = None,
    affiliation_hint: str | None = None,
    cache_path: Path | None = None,
    refresh: bool = False,
    fte_fraction: float = 1.0,
    home_country: str = "TN",
) -> FacultyMember:
    """Return a `FacultyMember` populated from Google Scholar.

    If `cache_path` exists and `refresh` is False, the cached payload is used.
    Otherwise, hits Google Scholar, caches the result, then maps it.
    """
    cached: dict[str, Any] | None = None if refresh else _load_cache(cache_path)
    raw = cached or _fetch_raw(full_name, affiliation_hint)
    if not cached:
        _save_cache(cache_path, raw)

    fm = _faculty_from_scholarly(
        raw=raw,
        faculty_id=faculty_id or full_name.lower().replace(" ", "_"),
        fte_fraction=fte_fraction,
        home_country=home_country,
    )
    log.info(
        "Mapped Google Scholar profile %r → %d publications, h-index=%s",
        fm.full_name,
        len(fm.publications),
        fm.h_index,
    )
    return fm


def faculty_to_dict(fm: FacultyMember) -> dict:
    """Convenience: dataclass -> JSON-friendly dict (for cache inspection)."""
    return asdict(fm)
