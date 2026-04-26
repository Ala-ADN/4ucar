"""Document chunking.

Splits source text into overlapping windows sized for the embedding model.
Different source types use different strategies:
  - data_records → one chunk per (institution, period, domain) bundle
  - accreditation_frameworks → one chunk per control / criterion
  - uploaded_documents → token-windowed with overlap
  - prompt_templates → one chunk per template file
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Chunk:
    chunk_id: str
    source: str
    text: str
    metadata: dict


def chunk_text(text: str, *, source: str, metadata: dict) -> list[Chunk]:
    """Token-window chunker with overlap. Unimplemented."""
    raise NotImplementedError


def chunk_data_records(records: list[dict]) -> list[Chunk]:
    """Group committed KPI records into per-(institution, period) chunks."""
    raise NotImplementedError


def chunk_framework(framework: dict) -> list[Chunk]:
    """One chunk per accreditation control."""
    raise NotImplementedError
