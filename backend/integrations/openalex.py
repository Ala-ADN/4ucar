"""OpenAlex adapter — primary provider for academic-research data.

OpenAlex (https://openalex.org) is a free, open scholarly database derived from
Crossref, ORCID, ROR and the now-retired MAG. No API key is required; providing
an email in the `User-Agent` opts you into the "polite pool" with a much higher
rate limit (10 req/s sustained).

Compared to Google Scholar this is dramatically more reliable for our KPIs:

    - works.open_access.is_oa             → fills RES-11
    - authorships[*].countries            → fills RES-04
    - works.cited_by_percentile_year      → proxy for RES-09 (top 1%)
    - author.summary_stats.h_index        → fills RES-02
    - author.cited_by_count, works_count  → feed RES-01, RES-03

Reference: https://docs.openalex.org/
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from dataclasses import asdict
from pathlib import Path
from typing import Any

import httpx

from backend.services.kpi_service.domain.inputs import FacultyMember, Publication

log = logging.getLogger(__name__)

OPENALEX_BASE = "https://api.openalex.org"
DEFAULT_PER_PAGE = 200  # OpenAlex hard max
DEFAULT_TIMEOUT = 30.0


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


class OpenAlexClient:
    """Thin httpx wrapper that handles polite-pool headers and cursor paging."""

    def __init__(
        self,
        *,
        email: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        client: httpx.Client | None = None,
    ):
        ua = (
            f"4ucar-kpi/0.1 (mailto:{email})"
            if email
            else "4ucar-kpi/0.1 (https://github.com/Ala-ADN/4ucar)"
        )
        self._owns_client = client is None
        self.client = client or httpx.Client(
            base_url=OPENALEX_BASE,
            headers={"User-Agent": ua, "Accept": "application/json"},
            timeout=timeout,
        )
        self.email = email

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> OpenAlexClient:
        return self

    def __exit__(self, *_exc) -> None:
        self.close()

    # -- low-level GET ------------------------------------------------------

    def _get(self, path: str, params: dict | None = None) -> dict:
        params = dict(params or {})
        if self.email and "mailto" not in params:
            params["mailto"] = self.email
        log.debug("GET %s params=%s", path, params)
        r = self.client.get(path, params=params)
        r.raise_for_status()
        return r.json()

    # -- institutions -------------------------------------------------------

    def search_institution(
        self, name: str, country_code: str | None = None
    ) -> dict | None:
        """Return the top-ranked institution matching `name` (optionally in country)."""
        params: dict[str, Any] = {"search": name, "per-page": 5}
        if country_code:
            params["filter"] = f"country_code:{country_code.lower()}"
        data = self._get("/institutions", params)
        results = data.get("results") or []
        return results[0] if results else None

    # -- authors ------------------------------------------------------------

    def search_authors(
        self,
        name: str,
        *,
        institution_id: str | None = None,
        country_code: str | None = None,
        per_page: int = 25,
    ) -> list[dict]:
        params: dict[str, Any] = {"search": name, "per-page": per_page}
        filters: list[str] = []
        if institution_id:
            filters.append(f"last_known_institutions.id:{_short_id(institution_id)}")
        if country_code:
            filters.append(f"last_known_institutions.country_code:{country_code.lower()}")
        if filters:
            params["filter"] = ",".join(filters)
        data = self._get("/authors", params)
        return data.get("results") or []

    def get_author(self, author_id: str) -> dict:
        return self._get(f"/authors/{_short_id(author_id)}")

    # -- works --------------------------------------------------------------

    def iter_author_works(
        self,
        author_id: str,
        *,
        max_works: int | None = None,
        per_page: int = DEFAULT_PER_PAGE,
    ) -> Iterator[dict]:
        cursor = "*"
        yielded = 0
        while cursor:
            data = self._get(
                "/works",
                {
                    "filter": f"authorships.author.id:{_short_id(author_id)}",
                    "per-page": per_page,
                    "cursor": cursor,
                },
            )
            for w in data.get("results") or []:
                yield w
                yielded += 1
                if max_works and yielded >= max_works:
                    return
            cursor = (data.get("meta") or {}).get("next_cursor") or ""


def _short_id(any_id: str) -> str:
    """OpenAlex IDs come as URLs; the API also accepts the bare suffix."""
    return any_id.rsplit("/", 1)[-1] if any_id.startswith("http") else any_id


# ---------------------------------------------------------------------------
# Mapping → domain inputs
# ---------------------------------------------------------------------------


def _publication_from_work(work: dict, *, target_author_id: str | None = None) -> Publication:
    """Map one OpenAlex work to our `Publication` dataclass."""
    bib_title = work.get("title") or work.get("display_name") or "<untitled>"
    year = work.get("publication_year")
    cites = work.get("cited_by_count")

    oa = (work.get("open_access") or {}).get("is_oa")

    countries: set[str] = set()
    target_norm = _short_id(target_author_id) if target_author_id else None
    for a in work.get("authorships") or []:
        author_id_norm = _short_id((a.get("author") or {}).get("id") or "")
        is_target = target_norm and author_id_norm == target_norm
        # Pull country codes from both top-level countries and each institution.
        for c in a.get("countries") or []:
            if c:
                countries.add(c.upper())
        for inst in a.get("institutions") or []:
            cc = inst.get("country_code")
            if cc:
                countries.add(cc.upper())
        # Even the target author's own country goes in — it documents the
        # local affiliation, and the calculator only flags *other* countries
        # as international.
        del is_target  # currently unused; kept for future provenance

    # Top 1% proxy: OpenAlex publishes a per-work percentile within the work's
    # publication year. THE's actual measure is field-normalised; this is a
    # year-normalised approximation, intentionally conservative.
    pct = (work.get("cited_by_percentile_year") or {}).get("min")
    field_top_1pct: bool | None = None
    if isinstance(pct, (int, float)):
        field_top_1pct = pct >= 99

    work_type = work.get("type") or ""
    is_peer_reviewed = work_type in {
        "article",
        "review",
        "book-chapter",
        "book",
        "proceedings-article",
        "journal-article",
    }

    return Publication(
        title=bib_title,
        year=int(year) if isinstance(year, int) else None,
        citation_count=int(cites) if isinstance(cites, int) else None,
        is_peer_reviewed=is_peer_reviewed,
        is_open_access=bool(oa) if isinstance(oa, bool) else None,
        coauthor_countries=sorted(countries) if countries else None,
        field_top_1pct=field_top_1pct,
        doi=(work.get("doi") or "").replace("https://doi.org/", "") or None,
        source="openalex",
    )


def _faculty_from_openalex(
    *,
    author: dict,
    works: list[dict],
    faculty_id: str,
    fte_fraction: float,
    home_country: str,
) -> FacultyMember:
    summary = author.get("summary_stats") or {}
    return FacultyMember(
        id=faculty_id,
        full_name=author.get("display_name", "<unknown>"),
        is_active=True,
        fte_fraction=fte_fraction,
        h_index=summary.get("h_index"),
        home_country=home_country,
        publications=[
            _publication_from_work(w, target_author_id=author.get("id")) for w in works
        ],
    )


# ---------------------------------------------------------------------------
# Cache + public entrypoint
# ---------------------------------------------------------------------------


def _load_cache(path: Path | None) -> dict | None:
    if path and path.exists():
        log.info("Loading OpenAlex payload from cache: %s", path)
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _save_cache(path: Path | None, payload: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    log.info("Saved OpenAlex payload to cache: %s", path)


def fetch_faculty_from_openalex(
    *,
    full_name: str,
    institution_hint: str | None = None,
    country_code: str | None = "TN",
    faculty_id: str | None = None,
    fte_fraction: float = 1.0,
    home_country: str = "TN",
    max_works: int = 500,
    cache_path: Path | None = None,
    refresh: bool = False,
    email: str | None = None,
    client: OpenAlexClient | None = None,
) -> FacultyMember:
    """Look up `full_name` on OpenAlex and return a populated `FacultyMember`.

    Disambiguation: if both `institution_hint` and `country_code` are given,
    we search the institution first (filtered by country), then narrow the
    author search to that institution's ID.

    Caching: if `cache_path` exists and `refresh=False` we replay it without
    touching the network. Otherwise we hit the API and persist the response.
    """
    cached = None if refresh else _load_cache(cache_path)
    if cached:
        return _faculty_from_openalex(
            author=cached["author"],
            works=cached["works"],
            faculty_id=faculty_id or _id_from_name(full_name),
            fte_fraction=fte_fraction,
            home_country=home_country,
        )

    owns_client = client is None
    cli = client or OpenAlexClient(email=email)
    try:
        institution_id: str | None = None
        if institution_hint:
            inst = cli.search_institution(institution_hint, country_code=country_code)
            if inst:
                institution_id = inst["id"]
                log.info(
                    "Resolved institution %r -> %s (%s)",
                    institution_hint,
                    inst.get("display_name"),
                    institution_id,
                )
            else:
                log.warning("No OpenAlex institution found for %r", institution_hint)

        candidates = cli.search_authors(
            full_name,
            institution_id=institution_id,
            country_code=country_code if not institution_id else None,
        )
        if not candidates:
            # Fall back to a name-only search; many authors don't have an
            # affiliation tagged on OpenAlex.
            log.info("No author match with institution filter; retrying name-only")
            candidates = cli.search_authors(full_name)

        if not candidates:
            raise LookupError(f"No OpenAlex author matched: {full_name!r}")

        # Best candidate = highest works_count among those whose name matches
        # our query word-for-word; fall back to the top-ranked overall.
        target_words = {w.lower() for w in full_name.split()}
        scored: list[tuple[int, dict]] = []
        for c in candidates:
            name_words = {w.lower() for w in (c.get("display_name") or "").split()}
            name_overlap = len(target_words & name_words)
            scored.append((name_overlap * 1000 + (c.get("works_count") or 0), c))
        scored.sort(reverse=True, key=lambda t: t[0])
        author = scored[0][1]
        log.info(
            "Selected author %s (%s) - works_count=%s, h_index=%s",
            author.get("display_name"),
            author.get("id"),
            author.get("works_count"),
            (author.get("summary_stats") or {}).get("h_index"),
        )

        # Re-fetch the author to get full summary_stats (search response is leaner).
        author = cli.get_author(author["id"])
        works = list(cli.iter_author_works(author["id"], max_works=max_works))
        log.info("Pulled %d works for %s", len(works), author.get("display_name"))

        _save_cache(cache_path, {"author": author, "works": works})

        return _faculty_from_openalex(
            author=author,
            works=works,
            faculty_id=faculty_id or _id_from_name(full_name),
            fte_fraction=fte_fraction,
            home_country=home_country,
        )
    finally:
        if owns_client:
            cli.close()


def _id_from_name(name: str) -> str:
    return name.lower().strip().replace(" ", "_")


def faculty_to_dict(fm: FacultyMember) -> dict:
    return asdict(fm)
