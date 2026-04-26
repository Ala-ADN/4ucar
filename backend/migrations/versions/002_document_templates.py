"""Add document_templates + document_template_fields.

Revision ID: 002_document_templates
Revises: 001_ingestion_tables
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_document_templates"
down_revision = "001_ingestion_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(1000)),
        sa.Column("source_format", sa.String(20), nullable=False),
        sa.Column("domain", sa.String(50), nullable=False),
        sa.Column("sheet_name", sa.String(200)),
        sa.Column("sample_headers", postgresql.JSON, nullable=False),
        sa.Column("sample_preview", postgresql.JSON),
        sa.Column("confirmed_mapping", postgresql.JSON, nullable=False),
        sa.Column("source_import_id", postgresql.UUID(as_uuid=True)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("match_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_matched_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("institution_id", "code", name="uq_doc_template_inst_code"),
    )
    op.create_index(
        "ix_document_templates_institution_id",
        "document_templates",
        ["institution_id"],
    )

    op.create_table(
        "document_template_fields",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_header", sa.String(500), nullable=False),
        sa.Column("target_field_id", sa.String(100)),
        sa.Column("transform_hint", sa.String(50)),
        sa.Column("is_required", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("notes", sa.String(500)),
    )
    op.create_index(
        "ix_document_template_fields_template_id",
        "document_template_fields",
        ["template_id"],
    )
    op.create_index(
        "ix_document_template_fields_target_field_id",
        "document_template_fields",
        ["target_field_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_document_template_fields_target_field_id",
        table_name="document_template_fields",
    )
    op.drop_index(
        "ix_document_template_fields_template_id",
        table_name="document_template_fields",
    )
    op.drop_table("document_template_fields")
    op.drop_index(
        "ix_document_templates_institution_id",
        table_name="document_templates",
    )
    op.drop_table("document_templates")
