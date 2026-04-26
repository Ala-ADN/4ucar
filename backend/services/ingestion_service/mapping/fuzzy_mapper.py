"""Fuzzy string matching fallback for column-to-field mapping.

Used when Claude fails or returns unparseable JSON. Lower quality than the
Claude approach but never leaves the user with nothing to work with.

Uses difflib.get_close_matches against the flat alias dictionary built from
KPI_FIELDS. No external calls — fully local, fully data-sovereign.
"""

import difflib

from backend.services.ingestion_service.kpi_schema import build_alias_map

_FUZZY_CUTOFF = 0.6
_alias_map: dict[str, str] | None = None


def _get_alias_map() -> dict[str, str]:
    global _alias_map
    if _alias_map is None:
        _alias_map = build_alias_map()
    return _alias_map


def fuzzy_map(headers: list[str], domain: str) -> list[dict]:
    """Return a mapping proposal using fuzzy string matching.

    Same output format as claude_mapper.propose_mapping:
    [{"column": str, "field_id": str|None, "confidence": float, "reason": str}]
    """
    from backend.services.ingestion_service.kpi_schema import fields_for_domain

    domain_field_ids = set(fields_for_domain(domain).keys())  # type: ignore[arg-type]
    alias_map = _get_alias_map()
    # Only consider aliases that map to a field in the requested domain
    domain_aliases = {alias: fid for alias, fid in alias_map.items() if fid in domain_field_ids}
    all_aliases = list(domain_aliases.keys())

    result = []
    for header in headers:
        header_lower = header.lower().strip()

        # Exact match first
        if header_lower in domain_aliases:
            field_id = domain_aliases[header_lower]
            result.append({
                "column": header,
                "field_id": field_id,
                "confidence": 1.0,
                "reason": "Correspondance exacte avec un alias connu.",
            })
            continue

        # Fuzzy match
        matches = difflib.get_close_matches(
            header_lower, all_aliases, n=1, cutoff=_FUZZY_CUTOFF
        )
        if matches:
            best_alias = matches[0]
            field_id = domain_aliases[best_alias]
            ratio = difflib.SequenceMatcher(None, header_lower, best_alias).ratio()
            result.append({
                "column": header,
                "field_id": field_id,
                "confidence": round(ratio, 2),
                "reason": f"Correspondance approximative avec l'alias « {best_alias} ».",
            })
        else:
            result.append({
                "column": header,
                "field_id": None,
                "confidence": 0.0,
                "reason": "Aucune correspondance trouvée dans le schéma pour ce domaine.",
            })

    return result
