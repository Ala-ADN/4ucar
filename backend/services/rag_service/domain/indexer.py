"""Indexing pipeline.

For each enabled source: pull rows → chunk → embed → upsert into the
vector store. Designed to be called from a Celery worker so reindexing
does not block the API.
"""

from __future__ import annotations

from uuid import UUID

from backend.services.rag_service.domain.chunker import Chunk


async def index_source(source: str, *, full_rebuild: bool = False) -> int:
    """Index one logical source. Returns chunk count written. Unimplemented."""
    raise NotImplementedError


async def embed_chunks(chunks: list[Chunk]) -> list[list[float]]:
    """Batch-embed chunks with the configured sentence-transformer model."""
    raise NotImplementedError


async def upsert_chunks(chunks: list[Chunk], embeddings: list[list[float]]) -> None:
    """Write chunks + vectors to the configured vector store."""
    raise NotImplementedError


async def delete_by_institution(institution_id: UUID) -> int:
    """RBAC support: drop all chunks belonging to one institution."""
    raise NotImplementedError
