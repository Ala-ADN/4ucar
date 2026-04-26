"""Create kpi_records table.

Revision ID: 003_kpi_records
Revises: 002_document_templates
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_kpi_records"
down_revision = "002_document_templates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "kpi_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kpi_id", sa.String(10), nullable=False),
        sa.Column("domain", sa.String(20), nullable=False),
        sa.Column("period_start", sa.Date, nullable=False),
        sa.Column("period_end", sa.Date, nullable=False),
        sa.Column("value", sa.Numeric(15, 4), nullable=True),
        sa.Column(
            "missing_fields",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "warnings",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "inputs_used",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "kpi_id",
            "period_start",
            "period_end",
            name="uq_kpi_records_tenant_kpi_period",
        ),
    )
    op.create_index(
        "ix_kpi_records_tenant_period_end",
        "kpi_records",
        ["tenant_id", "period_end"],
    )
    op.create_index(
        "ix_kpi_records_tenant_domain_period",
        "kpi_records",
        ["tenant_id", "domain", "period_end"],
    )


def downgrade() -> None:
    op.drop_index("ix_kpi_records_tenant_domain_period", table_name="kpi_records")
    op.drop_index("ix_kpi_records_tenant_period_end", table_name="kpi_records")
    op.drop_table("kpi_records")
