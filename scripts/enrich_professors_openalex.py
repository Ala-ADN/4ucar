"""Enrich seeded professors with OpenAlex h-index + publications.

Runs after `seed_insat_dgim_dgpi`. For every professor (or a filtered subset),
calls OpenAlex once, persists `h_index` on `professors`, and bulk-inserts
`professor_publications` rows. Cached per-name under `data/cache/openalex_*.json`
so reruns are cheap.

Usage:
    python -m scripts.enrich_professors_openalex
    python -m scripts.enrich_professors_openalex --limit 5
    python -m scripts.enrich_professors_openalex --refresh           # force-refetch
    python -m scripts.enrich_professors_openalex --department DGIM   # one dept
    python -m scripts.enrich_professors_openalex --email you@x.tn    # polite pool
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.integrations.openalex import (
    OpenAlexClient,
    fetch_faculty_from_openalex,
)
from backend.models.professors import Professor, ProfessorPublication
from backend.models.tenants import Department
from backend.shared.db.session import get_engine, get_sessionmaker

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "data" / "cache"

log = logging.getLogger("enrich_openalex")


def _slug(name: str) -> str:
    return name.lower().strip().replace(" ", "_")


async def _list_targets(
    session: AsyncSession, *, department_code: str | None, limit: int | None
) -> list[Professor]:
    stmt = select(Professor)
    if department_code:
        stmt = stmt.join(Department, Department.id == Professor.department_id).where(
            Department.code == department_code
        )
    stmt = stmt.order_by(Professor.last_name, Professor.first_name)
    if limit:
        stmt = stmt.limit(limit)
    return list((await session.scalars(stmt)).all())


def _name_variants(first: str, last: str) -> list[str]:
    """Generate fallback name spellings for OpenAlex disambiguation.

    Handles two common Tunisian-naming gotchas:
      - 'Med X' is a directory abbreviation for 'Mohamed X' that OpenAlex
        author records spell out in full.
      - Compound first names ('Med Mehdi', 'Slim Sabri') often get indexed
        under just one of the two tokens.
    """
    primary = f"{first} {last}".strip()
    variants: list[str] = [primary]

    if first.startswith("Med "):
        variants.append(f"Mohamed {first[4:]} {last}".strip())
        variants.append(f"{first[4:]} {last}".strip())
    elif first == "Med":
        variants.append(f"Mohamed {last}".strip())

    parts = first.split()
    if len(parts) > 1:
        for token in parts:
            if token != "Med":
                variants.append(f"{token} {last}".strip())

    # De-dupe while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


async def _enrich_one(
    session: AsyncSession,
    prof: Professor,
    *,
    client: OpenAlexClient,
    refresh: bool,
    affiliation: str,
    country: str,
    email: str | None,
    max_works: int,
) -> tuple[bool, int]:
    """Returns (success, publications_inserted)."""
    variants = _name_variants(prof.first_name, prof.last_name)
    faculty = None
    last_error: Exception | None = None

    for variant in variants:
        cache_path = CACHE_DIR / f"openalex_{_slug(variant)}.json"
        try:
            faculty = await asyncio.to_thread(
                fetch_faculty_from_openalex,
                full_name=variant,
                institution_hint=affiliation,
                country_code=country,
                faculty_id=str(prof.id),
                home_country=country,
                max_works=max_works,
                cache_path=cache_path,
                refresh=refresh,
                email=email,
                client=client,
            )
            if variant != variants[0]:
                log.info("matched %s under variant %r", variants[0], variant)
            break
        except LookupError as e:
            last_error = e
            continue
        except Exception as e:  # network/parse — log and skip
            log.error("openalex error for %s: %s", variant, e)
            return False, 0

    if faculty is None:
        log.warning("no openalex match: %s (tried %s)", variants[0], variants)
        del last_error
        return False, 0

    prof.h_index = faculty.h_index
    prof.h_index_updated_at = datetime.now(timezone.utc)

    # Replace any existing OpenAlex-sourced publications for this professor.
    await session.execute(
        delete(ProfessorPublication)
        .where(ProfessorPublication.professor_id == prof.id)
        .where(ProfessorPublication.source == "openalex")
    )
    inserted = 0
    for pub in faculty.publications:
        session.add(
            ProfessorPublication(
                professor_id=prof.id,
                title=pub.title[:8000] if pub.title else "<untitled>",
                year=pub.year,
                doi=pub.doi,
                citation_count=pub.citation_count or 0,
                source="openalex",
            )
        )
        inserted += 1
    return True, inserted


async def enrich(args: argparse.Namespace) -> dict[str, int]:
    sessionmaker = get_sessionmaker()
    matched = 0
    missed = 0
    publications_total = 0

    client = OpenAlexClient(email=args.email)
    try:
        async with sessionmaker() as session:
            targets = await _list_targets(
                session, department_code=args.department, limit=args.limit
            )
            log.info("enriching %d professors", len(targets))
            for i, prof in enumerate(targets, 1):
                ok, n_pubs = await _enrich_one(
                    session,
                    prof,
                    client=client,
                    refresh=args.refresh,
                    affiliation=args.affiliation,
                    country=args.country,
                    email=args.email,
                    max_works=args.max_works,
                )
                if ok:
                    matched += 1
                    publications_total += n_pubs
                    log.info(
                        "[%d/%d] %s %s — h=%s pubs=%d",
                        i,
                        len(targets),
                        prof.first_name,
                        prof.last_name,
                        prof.h_index,
                        n_pubs,
                    )
                else:
                    missed += 1

                # Commit per-row so a network failure later doesn't lose progress.
                await session.commit()
    finally:
        client.close()

    return {
        "matched": matched,
        "missed": missed,
        "publications_inserted": publications_total,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--limit", type=int, default=None, help="Stop after N professors")
    p.add_argument(
        "--department", default=None, help="Restrict to one department code (e.g. DGIM)"
    )
    p.add_argument("--refresh", action="store_true", help="Ignore on-disk cache")
    p.add_argument("--affiliation", default="INSAT", help="Institution hint for OpenAlex")
    p.add_argument("--country", default="TN", help="ISO-2 country code")
    p.add_argument("--email", default=None, help="Email for the OpenAlex polite pool")
    p.add_argument("--max-works", type=int, default=500)
    p.add_argument(
        "--log-level", default="INFO", choices=("DEBUG", "INFO", "WARNING", "ERROR")
    )
    return p.parse_args()


async def _main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    summary = await enrich(args)
    print("\nEnrichment complete:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    await get_engine().dispose()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
