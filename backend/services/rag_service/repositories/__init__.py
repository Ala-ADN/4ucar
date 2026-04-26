"""Vector-store repository layer.

Abstracts the underlying vector backend (pgvector / faiss / inmemory)
behind a small interface so the domain layer stays backend-agnostic.
All methods are scaffold-only.
"""

from __future__ import annotations

from typing import Protocol


class VectorRepository(Protocol):
    async def upsert(
        self, chunk_ids: list[str], vectors: list[list[float]], payloads: list[dict]
    ) -> None: ...

    async def search(
        self, vector: list[float], *, top_k: int, filters: dict | None = None
    ) -> list[tuple[str, float, dict]]: ...

    async def delete(self, chunk_ids: list[str]) -> int: ...

    async def count(self, filters: dict | None = None) -> int: ...
