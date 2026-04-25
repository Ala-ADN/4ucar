"""Auto-classification endpoint (LLM-driven document_class detection)."""

from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["documents"])
