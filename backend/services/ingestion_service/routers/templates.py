"""Document template CRUD + matcher routes.

A *template* is a saved (institution, source_format, domain, headers,
mapping) tuple promoted from a successful import. The matcher endpoint
scores all of an institution's templates against a new file's headers
so the UI can offer "matched template X — review and commit?" instead
of forcing the mapping step.

Routes:
    GET    /templates                    list this institution's templates
    POST   /templates                    promote an import's mapping into a template
    GET    /templates/{id}               full record
    DELETE /templates/{id}               soft-delete (sets is_active=False)
    POST   /templates/match              score templates against a list of headers
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.services.ingestion_service.dependencies import (
    CurrentUser,
    get_current_user,
    get_db,
    require_own_institution,
)
from backend.services.ingestion_service.kpi_schema import KPI_FIELDS
from backend.services.ingestion_service.models.audit import AuditAction, AuditEntry
from backend.services.ingestion_service.models.document_template import (
    DocumentTemplate,
    DocumentTemplateField,
)
from backend.services.ingestion_service.models.import_record import ImportRecord
from backend.services.ingestion_service.templates_matcher import (
    MIN_AUTO_CONFIRM_SCORE,
    MIN_SUGGESTION_SCORE,
    score_template,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class TemplateFieldOut(BaseModel):
    source_header: str
    target_field_id: str | None
    target_field_label: str | None
    transform_hint: str | None
    is_required: bool


class TemplateSummary(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: str | None
    source_format: str
    domain: str
    sheet_name: str | None
    sample_headers: list[str]
    match_count: int
    last_matched_at: datetime | None
    created_at: datetime
    field_count: int
    mapped_field_count: int


class TemplateDetail(TemplateSummary):
    confirmed_mapping: dict[str, str | None]
    fields: list[TemplateFieldOut]
    sample_preview: list[dict[str, Any]] | None


class CreateFromImportRequest(BaseModel):
    import_id: uuid.UUID
    code: str = Field(..., min_length=1, max_length=60)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)


class MatchRequest(BaseModel):
    institution_id: uuid.UUID
    headers: list[str] = Field(..., min_length=1, max_length=300)
    source_format: str = Field(..., max_length=20)
    domain: str | None = None


class MatchSuggestion(BaseModel):
    template: TemplateSummary
    score: float
    header_coverage: float
    matched_headers: list[str]
    auto_confirm: bool


class MatchResponse(BaseModel):
    suggestions: list[MatchSuggestion]
    best: MatchSuggestion | None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return s or "template"


def _summary(template: DocumentTemplate, *, field_count: int, mapped_count: int) -> TemplateSummary:
    return TemplateSummary(
        id=template.id,
        code=template.code,
        name=template.name,
        description=template.description,
        source_format=template.source_format,
        domain=template.domain,
        sheet_name=template.sheet_name,
        sample_headers=list(template.sample_headers or []),
        match_count=template.match_count,
        last_matched_at=template.last_matched_at,
        created_at=template.created_at,
        field_count=field_count,
        mapped_field_count=mapped_count,
    )


def _kpi_label(field_id: str | None) -> str | None:
    if not field_id:
        return None
    field = KPI_FIELDS.get(field_id)
    return field.label_fr if field else None


def _detail(template: DocumentTemplate, fields: list[DocumentTemplateField]) -> TemplateDetail:
    mapped = sum(1 for f in fields if f.target_field_id)
    return TemplateDetail(
        **_summary(template, field_count=len(fields), mapped_count=mapped).model_dump(),
        confirmed_mapping=dict(template.confirmed_mapping or {}),
        sample_preview=template.sample_preview,
        fields=[
            TemplateFieldOut(
                source_header=f.source_header,
                target_field_id=f.target_field_id,
                target_field_label=_kpi_label(f.target_field_id),
                transform_hint=f.transform_hint,
                is_required=f.is_required,
            )
            for f in fields
        ],
    )


def _format_from_mime(mime: str | None) -> str:
    """Group MIME types into the 5 source-format buckets templates use."""
    if not mime:
        return "csv"
    if "spreadsheet" in mime or "excel" in mime:
        return "ods" if "opendocument" in mime else "xlsx"
    if mime.startswith("text/csv"):
        return "csv"
    if mime == "application/pdf":
        return "pdf"
    if mime.startswith("image/"):
        return "image"
    return "csv"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/templates", response_model=list[TemplateSummary])
async def list_templates(
    institution_id: uuid.UUID = Query(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    domain: str | None = None,
    source_format: str | None = None,
    include_inactive: bool = False,
) -> list[TemplateSummary]:
    require_own_institution(institution_id, current_user)

    stmt = select(DocumentTemplate).where(DocumentTemplate.institution_id == institution_id)
    if not include_inactive:
        stmt = stmt.where(DocumentTemplate.is_active.is_(True))
    if domain:
        stmt = stmt.where(DocumentTemplate.domain == domain)
    if source_format:
        stmt = stmt.where(DocumentTemplate.source_format == source_format)
    stmt = stmt.order_by(desc(DocumentTemplate.match_count), desc(DocumentTemplate.created_at))

    templates = (await db.scalars(stmt)).all()

    # Pull all fields for these templates in one shot.
    if templates:
        ids = [t.id for t in templates]
        fields_stmt = select(DocumentTemplateField).where(
            DocumentTemplateField.template_id.in_(ids)
        )
        fields = (await db.scalars(fields_stmt)).all()
    else:
        fields = []
    fields_by_template: dict[uuid.UUID, list[DocumentTemplateField]] = {}
    for f in fields:
        fields_by_template.setdefault(f.template_id, []).append(f)

    out: list[TemplateSummary] = []
    for t in templates:
        fs = fields_by_template.get(t.id, [])
        mapped = sum(1 for f in fs if f.target_field_id)
        out.append(_summary(t, field_count=len(fs), mapped_count=mapped))
    return out


@router.get("/templates/{template_id}", response_model=TemplateDetail)
async def template_detail(
    template_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TemplateDetail:
    template = await db.get(DocumentTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template introuvable.")
    require_own_institution(template.institution_id, current_user)

    fields = (
        await db.scalars(
            select(DocumentTemplateField).where(
                DocumentTemplateField.template_id == template.id
            )
        )
    ).all()
    return _detail(template, list(fields))


@router.post("/templates", response_model=TemplateDetail, status_code=201)
async def create_template_from_import(
    body: CreateFromImportRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TemplateDetail:
    """Promote a successful import's confirmed mapping into a reusable template."""
    record = await db.get(ImportRecord, body.import_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Import introuvable.")
    require_own_institution(record.institution_id, current_user)

    if not record.confirmed_mapping:
        raise HTTPException(
            status_code=400,
            detail="L'import n'a pas encore de mapping confirmé — impossible d'en faire un modèle.",
        )
    if record.status not in ("mapping_confirmed", "validated", "committed"):
        raise HTTPException(
            status_code=400,
            detail="Le mapping doit être confirmé avant la promotion en modèle.",
        )

    code = _slugify(body.code)
    existing = await db.scalar(
        select(DocumentTemplate).where(
            DocumentTemplate.institution_id == record.institution_id,
            DocumentTemplate.code == code,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Un modèle avec le code « {code} » existe déjà.",
        )

    template = DocumentTemplate(
        institution_id=record.institution_id,
        code=code,
        name=body.name,
        description=body.description,
        source_format=_format_from_mime(record.detected_mime_type),
        domain=record.domain or "operational",
        sheet_name=record.sheet_name,
        sample_headers=list(record.extracted_headers or []),
        sample_preview=record.extracted_preview,
        confirmed_mapping=dict(record.confirmed_mapping),
        source_import_id=record.id,
        created_by=current_user.user_id,
    )
    db.add(template)
    await db.flush()

    field_rows = [
        DocumentTemplateField(
            template_id=template.id,
            source_header=hdr,
            target_field_id=target,
            is_required=bool(target and KPI_FIELDS.get(target) and KPI_FIELDS[target].required),
        )
        for hdr, target in (record.confirmed_mapping or {}).items()
    ]
    for f in field_rows:
        db.add(f)

    db.add(
        AuditEntry(
            import_id=record.id,
            institution_id=record.institution_id,
            user_id=current_user.user_id,
            action="template_created",
            description_fr=(
                f"Modèle de document « {template.name} » créé à partir de l'import "
                f"{record.original_filename}."
            ),
            payload={"template_id": str(template.id), "code": template.code},
        )
    )
    await db.commit()
    await db.refresh(template)

    return _detail(template, field_rows)


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    template = await db.get(DocumentTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template introuvable.")
    require_own_institution(template.institution_id, current_user)

    template.is_active = False
    await db.commit()


class ApplyTemplateResponse(BaseModel):
    import_id: uuid.UUID
    template_id: uuid.UUID
    status: str
    confirmed_mapping: dict[str, str | None]


@router.post(
    "/imports/{import_id}/apply-template/{template_id}",
    response_model=ApplyTemplateResponse,
)
async def apply_template_to_import(
    import_id: uuid.UUID,
    template_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ApplyTemplateResponse:
    """Apply a saved template's mapping to a freshly extracted import.

    Bumps the import to `mapping_confirmed` and queues the
    normalization+validation step — same path as the manual confirm.
    """
    from backend.services.ingestion_service.templates_matcher import (
        apply_template_mapping,
    )

    record = await db.get(ImportRecord, import_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Import introuvable.")
    require_own_institution(record.institution_id, current_user)

    template = await db.get(DocumentTemplate, template_id)
    if template is None or template.institution_id != record.institution_id:
        raise HTTPException(status_code=404, detail="Template introuvable.")
    if not template.is_active:
        raise HTTPException(status_code=400, detail="Template archivé.")

    if record.status not in ("extracted", "mapping_proposed"):
        raise HTTPException(
            status_code=400,
            detail=(
                "Le template ne peut être appliqué qu'à un import en attente de mapping."
            ),
        )

    confirmed = apply_template_mapping(
        template.confirmed_mapping or {}, list(record.extracted_headers or [])
    )

    record.confirmed_mapping = confirmed
    record.status = "mapping_confirmed"
    template.match_count = (template.match_count or 0) + 1
    template.last_matched_at = datetime.now(timezone.utc)

    db.add(
        AuditEntry(
            import_id=record.id,
            institution_id=record.institution_id,
            user_id=current_user.user_id,
            action=AuditAction.MAPPING_CONFIRMED,
            description_fr=(
                f"Mapping auto-confirmé via le modèle « {template.name} »."
            ),
            payload={"template_id": str(template.id), "template_code": template.code},
        )
    )
    await db.commit()

    # Kick off the same downstream Celery step the manual confirm uses.
    from backend.services.ingestion_service.tasks import run_normalization_and_validation

    task = run_normalization_and_validation.apply_async(
        args=[str(record.id)], queue="extraction"
    )
    record.validation_task_id = task.id
    await db.commit()

    return ApplyTemplateResponse(
        import_id=record.id,
        template_id=template.id,
        status=record.status,
        confirmed_mapping=confirmed,
    )


@router.post("/templates/match", response_model=MatchResponse)
async def match_templates(
    body: MatchRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MatchResponse:
    """Score every active template for the institution against the given headers."""
    require_own_institution(body.institution_id, current_user)

    stmt = select(DocumentTemplate).where(
        DocumentTemplate.institution_id == body.institution_id,
        DocumentTemplate.is_active.is_(True),
    )
    templates = (await db.scalars(stmt)).all()
    if not templates:
        return MatchResponse(suggestions=[], best=None)

    ids = [t.id for t in templates]
    fields = (
        await db.scalars(
            select(DocumentTemplateField).where(
                DocumentTemplateField.template_id.in_(ids)
            )
        )
    ).all()
    fields_by_template: dict[uuid.UUID, list[DocumentTemplateField]] = {}
    for f in fields:
        fields_by_template.setdefault(f.template_id, []).append(f)

    suggestions: list[MatchSuggestion] = []
    for t in templates:
        result = score_template(
            template_id=str(t.id),
            template_code=t.code,
            template_name=t.name,
            template_format=t.source_format,
            template_domain=t.domain,
            template_headers=list(t.sample_headers or []),
            incoming_format=body.source_format,
            incoming_domain=body.domain,
            incoming_headers=body.headers,
        )
        if result is None or result.score < MIN_SUGGESTION_SCORE:
            continue
        fs = fields_by_template.get(t.id, [])
        mapped = sum(1 for f in fs if f.target_field_id)
        suggestions.append(
            MatchSuggestion(
                template=_summary(t, field_count=len(fs), mapped_count=mapped),
                score=result.score,
                header_coverage=result.header_coverage,
                matched_headers=result.matched_headers,
                auto_confirm=result.score >= MIN_AUTO_CONFIRM_SCORE,
            )
        )

    suggestions.sort(key=lambda s: s.score, reverse=True)
    return MatchResponse(suggestions=suggestions, best=suggestions[0] if suggestions else None)
