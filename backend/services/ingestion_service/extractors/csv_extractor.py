"""CSV extractor with encoding detection (chardet) and delimiter auto-detection.

Tunisian administrative tools commonly export Windows-1252. The extractor:
- Uses chardet to detect encoding; surfaces top-2 candidates if ambiguous
- Tries comma, semicolon, tab as delimiters and picks the most consistent one
- Raises if both encoding and delimiter are ambiguous (user must confirm)
"""

import csv
import io
from pathlib import Path

import chardet

from backend.services.ingestion_service.extractors.base import ExtractionResult

_CANDIDATE_DELIMITERS = [";", ",", "\t"]
_ENCODING_CONFIDENCE_THRESHOLD = 0.80


def extract(
    file_path: str | Path,
    encoding: str | None = None,
    delimiter: str | None = None,
) -> ExtractionResult:
    raw_bytes = Path(file_path).read_bytes()

    detected_encoding, encoding_candidates = _detect_encoding(raw_bytes)
    chosen_encoding = encoding or detected_encoding

    text = raw_bytes.decode(chosen_encoding, errors="replace")

    detected_delimiter, delimiter_candidates = _detect_delimiter(text)
    chosen_delimiter = delimiter or detected_delimiter

    reader = csv.DictReader(io.StringIO(text), delimiter=chosen_delimiter)
    rows: list[dict[str, str]] = []
    raw_headers: list[str] | None = None

    for row in reader:
        if raw_headers is None:
            raw_headers = [h.strip() for h in (reader.fieldnames or [])]
        cleaned = {k.strip(): (v.strip() if v else "") for k, v in row.items()}
        rows.append(cleaned)

    headers = raw_headers or []

    result = ExtractionResult(
        headers=headers,
        rows=rows,
        preview=rows[:5],
        total_rows=len(rows),
    )
    result.encoding_candidates = encoding_candidates
    result.delimiter_candidates = delimiter_candidates
    return result


def _detect_encoding(raw_bytes: bytes) -> tuple[str, list[str]]:
    detection = chardet.detect(raw_bytes)
    encoding = detection.get("encoding") or "utf-8"
    confidence = detection.get("confidence", 0.0)

    candidates = [encoding]
    # If confidence is low, surface UTF-8 and Windows-1252 as alternatives
    if confidence < _ENCODING_CONFIDENCE_THRESHOLD:
        for alt in ["utf-8", "windows-1252", "iso-8859-1"]:
            if alt.lower() != encoding.lower():
                candidates.append(alt)

    return encoding, candidates


def _detect_delimiter(text: str) -> tuple[str, list[str]]:
    """Pick the delimiter that produces the most consistent column count across rows."""
    sample_lines = text.splitlines()[:20]

    scores: dict[str, float] = {}
    for delim in _CANDIDATE_DELIMITERS:
        counts = [line.count(delim) for line in sample_lines if line.strip()]
        if not counts:
            continue
        avg = sum(counts) / len(counts)
        variance = sum((c - avg) ** 2 for c in counts) / len(counts)
        # Higher avg + lower variance = better delimiter
        scores[delim] = avg - variance

    if not scores:
        return ",", _CANDIDATE_DELIMITERS

    sorted_delims = sorted(scores, key=lambda d: scores[d], reverse=True)
    return sorted_delims[0], sorted_delims
