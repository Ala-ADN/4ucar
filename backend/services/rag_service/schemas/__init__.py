"""Pydantic request/response schemas for the RAG service."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    embedding_model: str
    vector_backend: str
    indexed_chunks: int


class SourceInfo(BaseModel):
    name: str
    chunk_count: int
    last_indexed_at: datetime | None = None


class SourceListResponse(BaseModel):
    sources: list[SourceInfo]


class IndexRequest(BaseModel):
    sources: list[str] = Field(
        default_factory=list,
        description="Source names to (re)index. Empty list = all enabled sources.",
    )
    full_rebuild: bool = False


class IndexResponse(BaseModel):
    job_id: UUID
    queued_sources: list[str]


class Citation(BaseModel):
    source: str
    chunk_id: str
    score: float
    snippet: str
    metadata: dict | None = None


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    institution_id: UUID | None = Field(
        default=None,
        description="Scope retrieval to a single institution (RBAC).",
    )
    top_k: int | None = Field(default=None, ge=1, le=20)
    sources: list[str] | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    tokens_used: int | None = None
