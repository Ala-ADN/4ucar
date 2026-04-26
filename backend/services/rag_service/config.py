"""rag-service configuration.

Reads from environment variables prefixed with `RAG_`. All defaults are
placeholders — the service is scaffold-only and not wired up yet.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class RagSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RAG_", env_file=".env", extra="ignore")

    # Embedding model — matches the one used in ingestion_service for column mapping
    embedding_model: str = "intfloat/multilingual-e5-large"
    embedding_dim: int = 1024

    # Vector store — placeholder. Production likely pgvector on the existing Postgres.
    vector_backend: str = "pgvector"  # pgvector | faiss | inmemory
    vector_table: str = "rag_chunks"

    # Chunking
    chunk_size_tokens: int = 512
    chunk_overlap_tokens: int = 64

    # Retrieval
    top_k: int = 6
    min_score: float = 0.25

    # Generation — uses the existing `anthropic` SDK already in pyproject.toml
    generation_model: str = "claude-opus-4-7"
    max_output_tokens: int = 1024

    # Sources to index (logical names — actual ingestion is unimplemented)
    enabled_sources: tuple[str, ...] = (
        "data_records",
        "accreditation_frameworks",
        "uploaded_documents",
        "prompt_templates",
    )


@lru_cache
def get_settings() -> RagSettings:
    return RagSettings()
