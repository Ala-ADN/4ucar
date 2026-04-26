"""Append-only audit log for the ingestion pipeline.

Every action from upload to commit is recorded here. No UPDATE or DELETE
operations are permitted on this table — it is a legal requirement.
"""

import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from backend.shared.db.base import Base


class AuditEntry(Base):
    """One immutable row per pipeline event."""

    __tablename__ = "audit_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    import_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_records.id"), index=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # Action descriptor — see constants below
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Human-readable detail in French
    description_fr: Mapped[str] = mapped_column(Text, nullable=False)

    # Structured evidence blob (before/after state, mapping proposal, etc.)
    payload: Mapped[dict | None] = mapped_column(JSON)

    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    import_record: Mapped["ImportRecord | None"] = relationship(back_populates="audit_entries")  # noqa: F821


# Audit action constants — use these instead of free-form strings
class AuditAction:
    FILE_UPLOADED = "file_uploaded"
    EXTRACTION_STARTED = "extraction_started"
    EXTRACTION_COMPLETED = "extraction_completed"
    EXTRACTION_FAILED = "extraction_failed"
    MAPPING_PROPOSED = "mapping_proposed"
    MAPPING_CONFIRMED = "mapping_confirmed"
    NORMALIZATION_COMPLETED = "normalization_completed"
    VALIDATION_COMPLETED = "validation_completed"
    QUARANTINE_RESOLVED = "quarantine_resolved"
    COMMIT_STARTED = "commit_started"
    COMMIT_COMPLETED = "commit_completed"
    COMMIT_CONFLICT = "commit_conflict"
    IMPORT_CANCELLED = "import_cancelled"
    IMPORT_ROLLED_BACK = "import_rolled_back"
    PERIOD_LOCKED = "period_locked"
    PERIOD_UNLOCKED = "period_unlocked"
    FILE_PURGED = "file_purged"
