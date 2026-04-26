"""RAG service HTTP routes.

All handlers are scaffold-only and raise NotImplementedError.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from backend.services.rag_service.schemas import (
    HealthResponse,
    IndexRequest,
    IndexResponse,
    QueryRequest,
    QueryResponse,
    SourceListResponse,
)

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe. Returns service status without touching the vector store."""
    raise NotImplementedError


@router.get("/sources", response_model=SourceListResponse)
async def list_sources() -> SourceListResponse:
    """List indexable source types and their current chunk counts."""
    raise NotImplementedError


@router.post("/index", response_model=IndexResponse, status_code=status.HTTP_202_ACCEPTED)
async def index(payload: IndexRequest) -> IndexResponse:
    """Trigger (re)indexing for one or more source types.

    Returns a job id; actual work would run in a Celery worker on the
    existing `extraction` or a new `rag` queue.
    """
    raise NotImplementedError


@router.post("/query", response_model=QueryResponse)
async def query(payload: QueryRequest) -> QueryResponse:
    """Run a retrieval-augmented query.

    Pipeline: embed query → vector search top_k → rerank → build prompt
    → call generation model → return answer with citations.
    """
    raise NotImplementedError
