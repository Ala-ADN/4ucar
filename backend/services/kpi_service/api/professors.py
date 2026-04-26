"""Professor directory + matching API.

Endpoints:
    GET  /professors                  - paginated directory with filters
    GET  /professors/filters          - department + rank facets
    GET  /professors/{id}             - full record (specs, top publications)
    POST /professors/match            - rank candidates per spec §6.3

Matching: spec §6.3's formula uses sentence embeddings; until those land
we substitute Jaccard overlap on tokenised specialty text. Same response
shape, embeddings can drop in later.
"""

from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import case, desc, func, or_, select

from backend.models.professors import (
    Professor,
    ProfessorPublication,
    ProfessorSpecialization,
)
from backend.models.tenants import Department
from backend.services.kpi_service.api.dependencies import SessionDep
from backend.services.kpi_service.schemas.professors import (
    MatchCandidate,
    MatchRequest,
    MatchResponse,
    MatchScoreBreakdown,
    ProfessorDetail,
    ProfessorListItem,
    ProfessorListResponse,
    ProfessorPublicationOut,
    ProfessorSpecializationOut,
)

router = APIRouter(prefix="/professors", tags=["professors"])

# Reference scale for normalising h-index to 0..1 — INSAT's top is around 33,
# 50 leaves headroom without flattening everyone above the 90th percentile.
_H_INDEX_REFERENCE = 50.0

# Known stop-words specific to academic specialty fields. Filtered before
# token overlap so noise like "et" / "des" / "informatique" doesn't dominate.
_STOPWORDS = {
    "and", "or", "of", "for", "in", "the", "et", "des", "de", "du", "la", "le",
    "les", "à", "a", "au", "aux", "d", "l", "en",
}


def _tokens(text: str) -> set[str]:
    """Lowercase, strip punctuation, drop stopwords, keep tokens of len>=2."""
    if not text:
        return set()
    cleaned = re.sub(r"[^\w\s]", " ", text.lower(), flags=re.UNICODE)
    return {t for t in cleaned.split() if len(t) >= 2 and t not in _STOPWORDS}


# ---------------------------------------------------------------------------
# Helpers — query construction
# ---------------------------------------------------------------------------


def _summary_query(department_code: str | None = None):
    """Base SELECT that joins department + per-professor publication aggregates."""
    pub_count = func.count(ProfessorPublication.id).label("publications_count")
    citations = func.coalesce(
        func.sum(ProfessorPublication.citation_count), 0
    ).label("total_citations")

    stmt = (
        select(
            Professor,
            Department.code.label("department_code"),
            Department.name.label("department_name"),
            pub_count,
            citations,
        )
        .join(Department, Department.id == Professor.department_id, isouter=True)
        .join(
            ProfessorPublication,
            ProfessorPublication.professor_id == Professor.id,
            isouter=True,
        )
        .group_by(Professor.id, Department.code, Department.name)
    )
    if department_code:
        stmt = stmt.where(Department.code == department_code.upper())
    return stmt


def _row_to_list_item(row) -> ProfessorListItem:
    prof: Professor = row[0]
    return ProfessorListItem(
        id=prof.id,
        first_name=prof.first_name,
        last_name=prof.last_name,
        email=prof.email,
        department_code=row.department_code,
        department_name=row.department_name,
        rank=prof.rank,
        primary_specialty=prof.primary_specialty,
        gender=prof.gender,
        h_index=prof.h_index,
        h_index_updated_at=prof.h_index_updated_at,
        publications_count=row.publications_count or 0,
        total_citations=row.total_citations or 0,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=ProfessorListResponse)
async def list_professors(
    session: SessionDep,
    search: str | None = Query(default=None, max_length=120),
    department: str | None = Query(default=None, max_length=30),
    rank: str | None = Query(default=None, max_length=80),
    has_h_index: bool | None = Query(default=None),
    sort: str = Query(default="h_index_desc"),
    limit: int = Query(default=200, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> ProfessorListResponse:
    stmt = _summary_query(department_code=department)

    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Professor.first_name).like(like),
                func.lower(Professor.last_name).like(like),
                func.lower(Professor.email).like(like),
                func.lower(Professor.primary_specialty).like(like),
            )
        )
    if rank:
        stmt = stmt.where(Professor.rank == rank)
    if has_h_index is True:
        stmt = stmt.where(Professor.h_index.isnot(None))
    elif has_h_index is False:
        stmt = stmt.where(Professor.h_index.is_(None))

    # Total count via a sub-select on the filtered grouping.
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    sort_options = {
        "h_index_desc": (
            # Treat NULL h-index as -1 so it sorts last under DESC.
            desc(func.coalesce(Professor.h_index, -1)),
            Professor.last_name.asc(),
        ),
        "h_index_asc": (
            func.coalesce(Professor.h_index, 9999).asc(),
            Professor.last_name.asc(),
        ),
        "name_asc": (Professor.last_name.asc(), Professor.first_name.asc()),
        "name_desc": (Professor.last_name.desc(), Professor.first_name.desc()),
        "citations_desc": (desc("total_citations"), Professor.last_name.asc()),
    }
    order_by = sort_options.get(sort, sort_options["h_index_desc"])
    stmt = stmt.order_by(*order_by).limit(limit).offset(offset)

    rows = (await session.execute(stmt)).all()
    return ProfessorListResponse(
        total=int(total or 0),
        items=[_row_to_list_item(r) for r in rows],
    )


@router.get("/filters")
async def list_filters(session: SessionDep) -> dict[str, list[dict]]:
    """Facets for the directory toolbar — fed straight to <select> options."""
    dept_stmt = (
        select(
            Department.code,
            Department.name,
            func.count(Professor.id).label("count"),
        )
        .join(Professor, Professor.department_id == Department.id, isouter=True)
        .group_by(Department.code, Department.name)
        .order_by(Department.code)
    )
    rank_stmt = (
        select(Professor.rank, func.count(Professor.id).label("count"))
        .where(Professor.rank.isnot(None))
        .group_by(Professor.rank)
        .order_by(
            # Sort by an academic-grade ordering rather than alphabetic.
            case(
                {"Professeur": 1, "Maître de Conférences": 2, "Maître Assistant": 3, "PES": 4},
                value=Professor.rank,
                else_=99,
            )
        )
    )
    depts = [
        {"code": r.code, "name": r.name, "count": int(r.count or 0)}
        for r in (await session.execute(dept_stmt)).all()
    ]
    ranks = [
        {"value": r.rank, "count": int(r.count or 0)}
        for r in (await session.execute(rank_stmt)).all()
    ]
    return {"departments": depts, "ranks": ranks}


@router.get("/{professor_id}", response_model=ProfessorDetail)
async def professor_detail(
    professor_id: UUID, session: SessionDep
) -> ProfessorDetail:
    summary = await session.execute(
        _summary_query().where(Professor.id == professor_id)
    )
    row = summary.first()
    if row is None:
        raise HTTPException(status_code=404, detail="Professor not found")

    base = _row_to_list_item(row)

    spec_stmt = select(ProfessorSpecialization).where(
        ProfessorSpecialization.professor_id == professor_id
    )
    specs = [
        ProfessorSpecializationOut(
            domain=s.domain,
            subdomain=s.subdomain,
            level=s.level,
            verified=s.verified,
        )
        for s in (await session.scalars(spec_stmt)).all()
    ]

    pubs_stmt = (
        select(ProfessorPublication)
        .where(ProfessorPublication.professor_id == professor_id)
        .order_by(desc(func.coalesce(ProfessorPublication.citation_count, 0)))
        .limit(10)
    )
    pubs = [
        ProfessorPublicationOut(
            title=p.title,
            journal=p.journal,
            year=p.year,
            citation_count=p.citation_count,
            doi=p.doi,
            source=p.source,
        )
        for p in (await session.scalars(pubs_stmt)).all()
    ]
    return ProfessorDetail(
        **base.model_dump(),
        specializations=specs,
        top_publications=pubs,
    )


@router.post("/match", response_model=MatchResponse)
async def match_professors(
    body: MatchRequest, session: SessionDep
) -> MatchResponse:
    query_tokens = _tokens(body.specialty)
    if not query_tokens:
        raise HTTPException(
            status_code=400,
            detail="Could not extract any meaningful tokens from `specialty`.",
        )

    # Pull the candidate pool — filter only by department here. Specialty
    # matching is computed in Python so we can score and rank by overlap.
    base_stmt = _summary_query(department_code=body.department_code)
    rows = (await session.execute(base_stmt)).all()

    # Pre-fetch all specialisations for the candidates in one shot.
    candidate_ids = [r[0].id for r in rows]
    spec_stmt = select(ProfessorSpecialization).where(
        ProfessorSpecialization.professor_id.in_(candidate_ids)
    )
    spec_by_prof: dict[UUID, list[ProfessorSpecialization]] = {}
    for spec in (await session.scalars(spec_stmt)).all():
        spec_by_prof.setdefault(spec.professor_id, []).append(spec)

    candidates: list[MatchCandidate] = []
    for row in rows:
        prof: Professor = row[0]
        # All specialty surfaces this professor exposes:
        text_pool: list[str] = []
        if prof.primary_specialty:
            text_pool.append(prof.primary_specialty)
        for spec in spec_by_prof.get(prof.id, []):
            text_pool.append(spec.domain)
            if spec.subdomain:
                text_pool.append(spec.subdomain)
        prof_tokens = _tokens(" ".join(text_pool))

        if not prof_tokens:
            continue

        # Jaccard similarity on token sets.
        intersection = query_tokens & prof_tokens
        union = query_tokens | prof_tokens
        spec_similarity = len(intersection) / len(union) if union else 0.0
        if spec_similarity == 0.0:
            continue

        h_norm = (
            min(prof.h_index / _H_INDEX_REFERENCE, 1.0) if prof.h_index else 0.0
        )
        # Capacity, feedback, institution-priority signals don't have data
        # yet — defaults match the master spec's intent (full availability,
        # neutral feedback, all results are within the same tenant for now).
        breakdown = MatchScoreBreakdown(
            specialization_similarity=round(spec_similarity, 4),
            h_index_normalized=round(h_norm, 4),
            available_capacity=1.0,
            student_feedback=0.5,
            same_institution_priority=1.0,
        )
        score = (
            0.4 * spec_similarity
            + 0.2 * h_norm
            + 0.2 * breakdown.available_capacity
            + 0.1 * breakdown.student_feedback
            + 0.1 * breakdown.same_institution_priority
        )
        candidates.append(
            MatchCandidate(
                professor=_row_to_list_item(row),
                score=round(score, 4),
                score_breakdown=breakdown,
                matched_terms=sorted(intersection),
            )
        )

    candidates.sort(key=lambda c: c.score, reverse=True)
    return MatchResponse(
        query=body.specialty,
        department_code=body.department_code.upper() if body.department_code else None,
        total_candidates=len(candidates),
        candidates=candidates[: body.max_results],
    )
