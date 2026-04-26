"""Document templates — reusable mappings promoted from confirmed imports.

A template captures, per (institution, domain, source_format), the result
of a successful header→KPI-field mapping. When a subsequent file of the
same shape is uploaded, the matcher scores it against every saved
template and — above a confidence threshold — auto-confirms the mapping
so the file skips the manual review step.

Schema flexibility (option B): the *target* field set is closed (the 34
KPI ids in `kpi_schema.py`); the *source* side accepts any column header
text. Template fields persist that mapping, plus an optional transform
hint (e.g. "FR_NUMBER", "ARABIC_DIGITS") used by the normalizer.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.db.base import Base

if TYPE_CHECKING:  # pragma: no cover
    pass


class DocumentTemplate(Base):
    """A saved, reusable mapping between source columns and KPI fields."""

    __tablename__ = "document_templates"
    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_doc_template_inst_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000))

    # Pipeline shape. `source_format` is one of: xlsx, csv, pdf, image, ods.
    source_format: Mapped[str] = mapped_column(String(20), nullable=False)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    sheet_name: Mapped[str | None] = mapped_column(String(200))

    # Snapshot of the headers seen at promotion time — drives the matcher.
    sample_headers: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    sample_preview: Mapped[list | None] = mapped_column(JSON)

    # Authoritative mapping from header text → target KPI field id (or None
    # to mean "ignore this column"). Stored as a flat dict for fast access.
    confirmed_mapping: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # Source import the template was promoted from (audit trail).
    source_import_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    match_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_matched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    fields: Mapped[list["DocumentTemplateField"]] = relationship(
        back_populates="template", cascade="all, delete-orphan"
    )


class DocumentTemplateField(Base):
    """One source-column → target-KPI-field row of a template's mapping.

    Mirrors `confirmed_mapping` as relational rows so we can index, filter,
    and report by KPI field id (e.g. "which templates expose ACA-01?").
    """

    __tablename__ = "document_template_fields"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_header: Mapped[str] = mapped_column(String(500), nullable=False)
    target_field_id: Mapped[str | None] = mapped_column(String(100), index=True)
    transform_hint: Mapped[str | None] = mapped_column(String(50))
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500))

    template: Mapped[DocumentTemplate] = relationship(back_populates="fields")
