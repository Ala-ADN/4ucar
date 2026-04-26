"""Create ingestion service tables.

Revision ID: 001_ingestion_tables
Revises: 20260426_0000
Create Date: 2026-04-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001_ingestion_tables"
down_revision = "20260426_0000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_filename", sa.String(500), nullable=False),
        sa.Column("storage_path", sa.String(1000), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False),
        sa.Column("detected_mime_type", sa.String(100)),
        sa.Column("domain", sa.String(50)),
        sa.Column("period", sa.String(20)),
        sa.Column("is_historical", sa.Boolean, default=False),
        sa.Column("status", sa.String(30), nullable=False, default="pending"),
        sa.Column("extraction_task_id", sa.String(200)),
        sa.Column("mapping_task_id", sa.String(200)),
        sa.Column("validation_task_id", sa.String(200)),
        sa.Column("extracted_headers", postgresql.JSON),
        sa.Column("extracted_preview", postgresql.JSON),
        sa.Column("sheet_name", sa.String(200)),
        sa.Column("total_rows", sa.Integer),
        sa.Column("mapping_proposal", postgresql.JSON),
        sa.Column("confirmed_mapping", postgresql.JSON),
        sa.Column("validation_summary", postgresql.JSON),
        sa.Column("normalization_log", postgresql.JSON),
        sa.Column("overwrite_mode", sa.String(20)),
        sa.Column("records_valid", sa.Integer),
        sa.Column("records_warned", sa.Integer),
        sa.Column("records_quarantined", sa.Integer),
        sa.Column("records_committed", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("committed_at", sa.DateTime(timezone=True)),
        sa.Column("cancelled_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_import_records_institution_id", "import_records", ["institution_id"])
    op.create_index("ix_import_records_status", "import_records", ["status"])

    op.create_table(
        "data_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("import_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_records.id"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("domain", sa.String(50), nullable=False),
        sa.Column("field_id", sa.String(100), nullable=False),
        sa.Column("raw_value", sa.Text),
        sa.Column("normalized_value", postgresql.JSON),
        sa.Column("is_warned", sa.Boolean, default=False),
        sa.Column("warning_message", sa.Text),
        sa.Column("ocr_confidence", sa.Float),
        sa.Column("bounding_box", postgresql.JSON),
        sa.Column("is_archived", sa.Boolean, default=False),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("archived_by_import_id", postgresql.UUID(as_uuid=True)),
        sa.Column("committed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_data_records_import_id", "data_records", ["import_id"])
    op.create_index("ix_data_records_institution_id", "data_records", ["institution_id"])
    op.create_index("ix_data_records_field_id", "data_records", ["field_id"])
    op.create_index("ix_data_records_is_archived", "data_records", ["is_archived"])

    op.create_table(
        "quarantine_rows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("import_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_records.id"), nullable=False),
        sa.Column("row_index", sa.Integer, nullable=False),
        sa.Column("raw_data", postgresql.JSON, nullable=False),
        sa.Column("failed_field", sa.String(100), nullable=False),
        sa.Column("failure_reason_fr", sa.Text, nullable=False),
        sa.Column("resolution", sa.String(20)),
        sa.Column("corrected_value", postgresql.JSON),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True)),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("override_justification", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_quarantine_rows_import_id", "quarantine_rows", ["import_id"])

    op.create_table(
        "data_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("domain", sa.String(50), nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text),
        sa.Column("target_institutions", postgresql.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "data_request_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("data_requests.id"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, default="not_started"),
        sa.Column("import_id", postgresql.UUID(as_uuid=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_data_request_responses_request_id", "data_request_responses", ["request_id"])
    op.create_index("ix_data_request_responses_institution_id", "data_request_responses", ["institution_id"])

    op.create_table(
        "locked_periods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period", sa.String(20), nullable=False),
        sa.Column("domain", sa.String(50)),
        sa.Column("locked_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reason", sa.Text),
    )
    op.create_index("ix_locked_periods_institution_id", "locked_periods", ["institution_id"])

    op.create_table(
        "audit_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("import_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("import_records.id")),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("description_fr", sa.Text, nullable=False),
        sa.Column("payload", postgresql.JSONB),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_entries_import_id", "audit_entries", ["import_id"])
    op.create_index("ix_audit_entries_institution_id", "audit_entries", ["institution_id"])
    op.create_index("ix_audit_entries_action", "audit_entries", ["action"])
    op.create_index("ix_audit_entries_created_at", "audit_entries", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_entries")
    op.drop_table("locked_periods")
    op.drop_table("data_request_responses")
    op.drop_table("data_requests")
    op.drop_table("quarantine_rows")
    op.drop_table("data_records")
    op.drop_table("import_records")
