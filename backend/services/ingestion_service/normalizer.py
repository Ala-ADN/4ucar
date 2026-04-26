"""Value normalization — Stage 5 of the ingestion pipeline.

Transforms raw string cell values into typed Python values ready for validation.
All transformations are logged for the audit trail.

Handles:
- French number formatting: space/nbsp as thousands separator, comma as decimal
- Arabic-Indic numerals → Western (٠١٢٣٤٥٦٧٨٩ → 0123456789)
- Percentage sign stripping
- Currency symbol stripping (TND, DT, د.ت, دينار)
- Null-like strings → None (empty, N/A, —, nd, nr, -, n/d, non renseigné)
- Whitespace normalization
"""

from __future__ import annotations

import re
from typing import Any

from backend.services.ingestion_service.kpi_schema import KPI_FIELDS

_NULL_LIKE = frozenset({
    "", "n/a", "na", "—", "–", "-", "nd", "nr", "n/d",
    "non renseigné", "non renseignée", "néant", "none", "null", "nan",
    ".", "..", "---",
})

_ARABIC_INDIC_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_EXTENDED_ARABIC_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

_CURRENCY_PATTERN = re.compile(r"(?:TND|DT|د\.ت|دينار)", re.IGNORECASE)
_PERCENT_PATTERN = re.compile(r"\s*%\s*$")
_THOUSANDS_PATTERN = re.compile(r"[\s  ]")  # space, nbsp, narrow nbsp


def normalize_row(
    raw_row: dict[str, str],
    mapping: dict[str, str | None],
) -> tuple[dict[str, Any], list[dict]]:
    """Normalize one row using the confirmed column→field mapping.

    Returns:
        normalized: dict mapping field_id → typed value (or None)
        log: list of transformation records for the audit trail
    """
    normalized: dict[str, Any] = {}
    log: list[dict] = []

    for col_header, raw_value in raw_row.items():
        field_id = mapping.get(col_header)
        if field_id is None:
            continue  # column explicitly marked as ignored

        kpi = KPI_FIELDS.get(field_id)
        if kpi is None:
            continue

        typed_value, transforms = _normalize_value(raw_value, field_id, kpi.data_type)
        normalized[field_id] = typed_value

        if transforms:
            log.append({
                "column": col_header,
                "field_id": field_id,
                "raw": raw_value,
                "normalized": str(typed_value),
                "transforms": transforms,
            })

    return normalized, log


def _normalize_value(
    raw: str,
    field_id: str,
    data_type: str,
) -> tuple[Any, list[str]]:
    """Apply all transformations to a single raw string value.

    Returns (typed_value, list_of_transform_names_applied).
    """
    transforms: list[str] = []
    value = str(raw).strip()

    # Null detection
    if value.lower() in _NULL_LIKE:
        return None, ["null_coerced"]

    # Arabic-Indic numeral conversion
    converted = value.translate(_ARABIC_INDIC_MAP).translate(_EXTENDED_ARABIC_MAP)
    if converted != value:
        transforms.append("arabic_indic_to_western")
        value = converted

    # Currency stripping
    stripped_currency = _CURRENCY_PATTERN.sub("", value).strip()
    if stripped_currency != value:
        transforms.append("currency_stripped")
        value = stripped_currency

    # Percentage stripping
    if data_type == "percentage":
        stripped_pct = _PERCENT_PATTERN.sub("", value).strip()
        if stripped_pct != value:
            transforms.append("percent_sign_stripped")
            value = stripped_pct

    # French number formatting: thousands separator (space/nbsp) + comma decimal
    # Apply before parsing
    no_thousands = _THOUSANDS_PATTERN.sub("", value)
    if no_thousands != value:
        transforms.append("thousands_separator_removed")
        value = no_thousands

    if "," in value and "." not in value:
        value = value.replace(",", ".")
        transforms.append("comma_decimal_to_dot")

    # Type coercion
    if data_type in ("float", "percentage"):
        try:
            result = float(value)
            return result, transforms
        except ValueError:
            return None, transforms + ["parse_failed"]

    if data_type == "integer":
        try:
            # Accept float-looking strings like "42.0"
            result = int(float(value))
            return result, transforms
        except ValueError:
            return None, transforms + ["parse_failed"]

    # Fallback: return as string
    return value, transforms
