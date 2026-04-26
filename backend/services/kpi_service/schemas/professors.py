"""Pydantic schemas for the professors HTTP surface."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProfessorListItem(BaseModel):
    """One row in the directory list view."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    email: str
    department_code: str | None = None
    department_name: str | None = None
    rank: str | None = None
    primary_specialty: str | None = None
    gender: str | None = None
    h_index: int | None = None
    h_index_updated_at: datetime | None = None
    publications_count: int = 0
    total_citations: int = 0


class ProfessorListResponse(BaseModel):
    total: int
    items: list[ProfessorListItem]


class ProfessorPublicationOut(BaseModel):
    title: str
    journal: str | None = None
    year: int | None = None
    citation_count: int = 0
    doi: str | None = None
    source: str | None = None


class ProfessorSpecializationOut(BaseModel):
    domain: str
    subdomain: str | None = None
    level: str | None = None
    verified: bool = False


class ProfessorDetail(ProfessorListItem):
    """Full record — adds collections."""

    specializations: list[ProfessorSpecializationOut] = Field(default_factory=list)
    top_publications: list[ProfessorPublicationOut] = Field(default_factory=list)


class MatchRequest(BaseModel):
    """Body for POST /professors/match.

    `specialty` is matched against each professor's `primary_specialty`
    plus their `professor_specializations` rows. Token-overlap (Jaccard)
    is used as a stand-in for the embedding similarity from spec §6.3 —
    embeddings can swap in later without changing the response shape.
    """

    specialty: str = Field(..., min_length=1, max_length=200)
    department_code: str | None = None
    max_results: int = Field(default=10, ge=1, le=50)


class MatchScoreBreakdown(BaseModel):
    specialization_similarity: float
    h_index_normalized: float
    available_capacity: float
    student_feedback: float
    same_institution_priority: float


class MatchCandidate(BaseModel):
    professor: ProfessorListItem
    score: float
    score_breakdown: MatchScoreBreakdown
    matched_terms: list[str]


class MatchResponse(BaseModel):
    query: str
    department_code: str | None = None
    total_candidates: int
    candidates: list[MatchCandidate]
