"""Match a freshly extracted file's headers against saved DocumentTemplates.

The scorer is intentionally simple: lower-case + de-accent + tokenise,
then take Jaccard overlap on the resulting bags. Domain + format match
multiply the final score (zero out if either disagrees). The threshold
for auto-confirming is exposed as `MIN_AUTO_CONFIRM_SCORE`; below it the
template is shown as a *suggestion* the user can accept, above it the
pipeline jumps straight to validation.

This is not embedding similarity — it doesn't need to be. The KPI field
labels and Tunisian ministerial form headers reuse the same nouns, so
token overlap behaves well in practice. When the production embeddings
land (per kpi_schema.py header), the same `score()` interface returns a
better number; nothing else changes.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Below this we don't even surface the template as a suggestion.
MIN_SUGGESTION_SCORE = 0.35
# At/above this we auto-confirm and skip manual mapping review.
MIN_AUTO_CONFIRM_SCORE = 0.6


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def _tokens(text: str) -> set[str]:
    if not text:
        return set()
    cleaned = _strip_accents(text.lower())
    cleaned = re.sub(r"[^\w\s]", " ", cleaned, flags=re.UNICODE)
    return {t for t in cleaned.split() if len(t) >= 2}


def _normalise_header(header: str) -> frozenset[str]:
    return frozenset(_tokens(header))


def _header_set_signature(headers: list[str]) -> set[frozenset[str]]:
    """One token-set per header; used for header-coverage matching."""
    return {sig for sig in (_normalise_header(h) for h in headers) if sig}


@dataclass
class TemplateMatchResult:
    template_id: str
    template_code: str
    template_name: str
    score: float
    header_coverage: float  # fraction of incoming headers that mapped
    matched_headers: list[str]


def score_template(
    template_id: str,
    template_code: str,
    template_name: str,
    template_format: str,
    template_domain: str,
    template_headers: list[str],
    *,
    incoming_format: str,
    incoming_domain: str | None,
    incoming_headers: list[str],
) -> TemplateMatchResult | None:
    """Return None if format/domain disagree (template is not applicable)."""
    if template_format != incoming_format:
        return None
    if incoming_domain and template_domain != incoming_domain:
        return None

    template_sigs = _header_set_signature(template_headers)
    incoming_sigs = _header_set_signature(incoming_headers)
    if not template_sigs or not incoming_sigs:
        return None

    # Jaccard over header signatures gives a decent overall similarity;
    # header_coverage tells us how many of the incoming columns we know
    # how to map (the user-facing number).
    intersection = template_sigs & incoming_sigs
    union = template_sigs | incoming_sigs
    jaccard = len(intersection) / len(union) if union else 0.0

    coverage = (
        len(intersection) / len(incoming_sigs) if incoming_sigs else 0.0
    )

    matched: list[str] = []
    template_set = {sig: hdr for sig, hdr in zip(template_sigs, template_headers) if sig}
    for hdr in incoming_headers:
        sig = _normalise_header(hdr)
        if sig and sig in template_sigs:
            matched.append(hdr)

    return TemplateMatchResult(
        template_id=template_id,
        template_code=template_code,
        template_name=template_name,
        score=round(jaccard, 4),
        header_coverage=round(coverage, 4),
        matched_headers=matched,
    )


def apply_template_mapping(
    template_mapping: dict[str, str | None],
    incoming_headers: list[str],
) -> dict[str, str | None]:
    """Build a confirmed_mapping for the incoming file from the template.

    The template's mapping is keyed by header text — but headers may
    differ in punctuation/accents/casing, so we re-key by the token-set
    signature for the look-up. Any incoming header without a match in
    the template gets `None` (= ignore column).
    """
    by_sig: dict[frozenset[str], str | None] = {}
    for hdr, target in template_mapping.items():
        sig = _normalise_header(hdr)
        if sig:
            by_sig[sig] = target

    confirmed: dict[str, str | None] = {}
    for hdr in incoming_headers:
        sig = _normalise_header(hdr)
        confirmed[hdr] = by_sig.get(sig) if sig else None
    return confirmed
