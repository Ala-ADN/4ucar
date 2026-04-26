"""Answer generation.

Builds a system+user prompt from the retrieved chunks, calls the
Anthropic SDK (already declared in pyproject.toml), and returns the
answer with inline citations.
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.services.rag_service.domain.retriever import RetrievedChunk


@dataclass
class Generation:
    answer: str
    tokens_used: int | None
    citations: list[RetrievedChunk]


def build_prompt(question: str, chunks: list[RetrievedChunk]) -> tuple[str, str]:
    """Return (system_prompt, user_prompt). Unimplemented."""
    raise NotImplementedError


async def generate(question: str, chunks: list[RetrievedChunk]) -> Generation:
    """Call the LLM with the assembled prompt. Unimplemented."""
    raise NotImplementedError
