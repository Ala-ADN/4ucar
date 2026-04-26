"""Retrieval — vector search + optional reranking.

Plugs into the configured vector backend (pgvector by default, since the
project already runs Postgres). Applies institution-level filtering for
RBAC before the similarity search.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass
class RetrievedChunk:
    chunk_id: str
    source: str
    text: str
    score: float
    metadata: dict


async def retrieve(
    query: str,
    *,
    top_k: int,
    institution_id: UUID | None = None,
    sources: list[str] | None = None,
) -> list[RetrievedChunk]:
    """Embed query, run vector search, return top_k chunks. Unimplemented."""
    raise NotImplementedError


async def rerank(
    query: str, chunks: list[RetrievedChunk], *, top_k: int
) -> list[RetrievedChunk]:
    """Optional cross-encoder rerank pass. Unimplemented."""
    raise NotImplementedError
