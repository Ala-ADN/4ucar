"""Human review queue API — list / approve / reject extraction results."""

from fastapi import APIRouter

router = APIRouter(prefix="/documents/review", tags=["documents"])
