"""rag-service FastAPI entrypoint.

Run with: `uv run uvicorn backend.services.rag_service.main:app --port 8020`
"""

from __future__ import annotations

from fastapi import FastAPI

from backend.services.rag_service.api.routes import router as rag_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="UCAR RAG Service",
        description=(
            "Retrieval-augmented generation over UCAR data: committed KPI records, "
            "accreditation frameworks, ingested documents, and prompt templates."
        ),
        version="0.1.0",
    )
    app.include_router(rag_router)
    return app


app = create_app()
