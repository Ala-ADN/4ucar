"""SQLAlchemy 2.0 models for the ingestion pipeline tables."""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.db.base import Base


class ImportRecord(Base):
    """One row per file upload attempt. Tracks the full pipeline state."""

    __tablename__ = "import_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    detected_mime_type: Mapped[str | None] = mapped_column(String(100))

    domain: Mapped[str | None] = mapped_column(String(50))  # academic|finance|operational|environmental
    period: Mapped[str | None] = mapped_column(String(20))  # e.g. 2025-S1
    is_historical: Mapped[bool] = mapped_column(Boolean, default=False)

    # Pipeline state
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", index=True
    )
    # pending → extracted → mapping_proposed → mapping_confirmed → validated → committed | cancelled

    # Celery task IDs for async polling
    extraction_task_id: Mapped[str | None] = mapped_column(String(200))
    mapping_task_id: Mapped[str | None] = mapped_column(String(200))
    validation_task_id: Mapped[str | None] = mapped_column(String(200))

    # Extraction output
    extracted_headers: Mapped[list[str] | None] = mapped_column(JSON)
    extracted_preview: Mapped[list[dict] | None] = mapped_column(JSON)  # first 5 rows
    sheet_name: Mapped[str | None] = mapped_column(String(200))  # chosen Excel sheet
    total_rows: Mapped[int | None] = mapped_column(Integer)

    # AI mapping output (proposal + user-confirmed)
    mapping_proposal: Mapped[list[dict] | None] = mapped_column(JSON)
    confirmed_mapping: Mapped[dict | None] = mapped_column(JSON)  # {col_header: field_id | null}

    # Validation output
    validation_summary: Mapped[dict | None] = mapped_column(JSON)
    normalization_log: Mapped[list[dict] | None] = mapped_column(JSON)

    # Commit options chosen by user
    overwrite_mode: Mapped[str | None] = mapped_column(String(20))  # overwrite|merge|cancel

    # Commit statistics
    records_valid: Mapped[int | None] = mapped_column(Integer)
    records_warned: Mapped[int | None] = mapped_column(Integer)
    records_quarantined: Mapped[int | None] = mapped_column(Integer)
    records_committed: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    quarantine_rows: Mapped[list["QuarantineRow"]] = relationship(back_populates="import_record")
    data_records: Mapped[list["DataRecord"]] = relationship(back_populates="import_record")
    audit_entries: Mapped[list["AuditEntry"]] = relationship(back_populates="import_record")


class DataRecord(Base):
    """One committed data row — one KPI value for one institution+period."""

    __tablename__ = "data_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_records.id"), nullable=False, index=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)

    field_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    raw_value: Mapped[str | None] = mapped_column(Text)
    normalized_value: Mapped[dict | None] = mapped_column(JSON)

    # Validation status
    is_warned: Mapped[bool] = mapped_column(Boolean, default=False)
    warning_message: Mapped[str | None] = mapped_column(Text)

    # OCR metadata (if sourced from image/PDF)
    ocr_confidence: Mapped[float | None] = mapped_column()
    bounding_box: Mapped[dict | None] = mapped_column(JSON)  # {x, y, w, h, page}

    # Soft-delete for overwrite mode
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_by_import_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    committed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    import_record: Mapped["ImportRecord"] = relationship(back_populates="data_records")


class QuarantineRow(Base):
    """Rows that failed hard validation — held for human review before commit."""

    __tablename__ = "quarantine_rows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_records.id"), nullable=False, index=True
    )

    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    failed_field: Mapped[str] = mapped_column(String(100), nullable=False)
    failure_reason_fr: Mapped[str] = mapped_column(Text, nullable=False)

    # Resolution by user
    resolution: Mapped[str | None] = mapped_column(String(20))  # correct|override|discard
    corrected_value: Mapped[dict | None] = mapped_column(JSON)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    override_justification: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    import_record: Mapped["ImportRecord"] = relationship(back_populates="quarantine_rows")


class DataRequest(Base):
    """UCAR central pushes collection requests to specific institutions."""

    __tablename__ = "data_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    # List of institution UUIDs targeted
    target_institutions: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    responses: Mapped[list["DataRequestResponse"]] = relationship(back_populates="request")


class DataRequestResponse(Base):
    """Per-institution response status for a data collection request."""

    __tablename__ = "data_request_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_requests.id"), nullable=False, index=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    # not_started|in_progress|submitted|late
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_started")
    import_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    request: Mapped["DataRequest"] = relationship(back_populates="responses")


class LockedPeriod(Base):
    """Periods that have been locked by super_admin — no new imports allowed."""

    __tablename__ = "locked_periods"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    institution_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    domain: Mapped[str | None] = mapped_column(String(50))  # None = all domains

    locked_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    reason: Mapped[str | None] = mapped_column(Text)


# Import here to avoid circular import issues; AuditEntry references ImportRecord
from backend.services.ingestion_service.models.audit import AuditEntry  # noqa: E402, F401
