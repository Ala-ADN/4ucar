"""Demo: compute Domain A KPIs for INSAT using one researcher's public profile.

Default provider is OpenAlex (free, reliable, no auth). Google Scholar is kept
as a fallback because it can be useful for cached/offline replay, but Google
aggressively blocks scrapers and the live path will frequently fail.

Usage:
    python scripts/demo_domain_a_insat.py
    python scripts/demo_domain_a_insat.py --refresh
    python scripts/demo_domain_a_insat.py --provider scholar
    python scripts/demo_domain_a_insat.py --email you@your.institution.tn
    python scripts/demo_domain_a_insat.py --period 2025
    python scripts/demo_domain_a_insat.py --name "Sofiane Ouni" --affiliation INSAT
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import date
from pathlib import Path

from backend.services.kpi_service.domain import (
    InstitutionResearchInputs,
    compute_research_domain,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = REPO_ROOT / "data" / "cache"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--provider",
        choices=("openalex", "scholar"),
        default="openalex",
        help="Data source for researcher profile (default: openalex)",
    )
    p.add_argument("--refresh", action="store_true", help="Force a fresh fetch")
    p.add_argument(
        "--period",
        type=int,
        default=date.today().year,
        help="Period-end year (default: current year)",
    )
    p.add_argument("--name", default="Sofiane Ouni")
    p.add_argument("--affiliation", default="INSAT")
    p.add_argument("--country", default="TN", help="ISO-2 country code for disambiguation")
    p.add_argument(
        "--email",
        default=None,
        help="Email for the OpenAlex polite pool (optional but recommended)",
    )
    p.add_argument(
        "--max-works",
        type=int,
        default=500,
        help="Cap on publications to pull (OpenAlex only)",
    )
    return p.parse_args()


def fetch_professor(args: argparse.Namespace):
    if args.provider == "openalex":
        from backend.integrations.openalex import fetch_faculty_from_openalex

        cache_path = CACHE_DIR / f"openalex_{_slug(args.name)}.json"
        return fetch_faculty_from_openalex(
            full_name=args.name,
            institution_hint=args.affiliation,
            country_code=args.country,
            faculty_id=f"{args.affiliation.lower()}-{_slug(args.name)}",
            home_country=args.country,
            max_works=args.max_works,
            cache_path=cache_path,
            refresh=args.refresh,
            email=args.email,
        )
    else:
        from backend.integrations.google_scholar import fetch_faculty_from_scholar

        cache_path = CACHE_DIR / f"scholar_{_slug(args.name)}.json"
        return fetch_faculty_from_scholar(
            full_name=args.name,
            faculty_id=f"{args.affiliation.lower()}-{_slug(args.name)}",
            affiliation_hint=args.affiliation,
            cache_path=cache_path,
            refresh=args.refresh,
            home_country=args.country,
        )


def _slug(name: str) -> str:
    return name.lower().strip().replace(" ", "_")


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    professor = fetch_professor(args)

    period_start = date(args.period, 1, 1)
    period_end = date(args.period, 12, 31)
    inputs = InstitutionResearchInputs(
        institution_id="00000000-0000-0000-0000-000000000001",
        institution_code=args.affiliation,
        period_start=period_start,
        period_end=period_end,
        faculty=[professor],
        home_country=args.country,
    )

    print()
    print("=" * 78)
    print(f"  Domain A KPIs - {inputs.institution_code}  |  period {args.period}")
    print(f"  Source ({args.provider}): {professor.full_name}")
    print(
        f"  Publications: {len(professor.publications)}   h-index: {professor.h_index}"
    )
    print("=" * 78)

    results = compute_research_domain(inputs)
    for r in results:
        status = "OK" if r.is_complete else ("EST" if r.value is not None else "MISSING")
        value_str = f"{r.value:.3f}" if r.value is not None else "n/a"
        print(f"\n[{status:>7}] {r.kpi_id}  {r.name}")
        print(f"          formula : {r.formula}")
        print(f"          value   : {value_str} {r.unit}")
        if r.missing_fields:
            print(f"          missing : {', '.join(r.missing_fields)}")
        if r.warnings:
            for w in r.warnings:
                print(f"          warn    : {w}")
        if r.inputs_used:
            print(f"          used    : {json.dumps(r.inputs_used, default=str)}")

    print()
    print("-" * 78)
    summary = {
        "complete": sum(1 for r in results if r.is_complete),
        "estimated": sum(1 for r in results if r.is_estimated),
        "missing": sum(1 for r in results if r.value is None),
    }
    print(
        f"  Summary: {summary['complete']} complete | {summary['estimated']} estimated "
        f"| {summary['missing']} uncomputable"
    )
    print("-" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
