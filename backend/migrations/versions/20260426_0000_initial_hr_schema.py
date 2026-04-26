"""initial hr schema (tenants, departments, professors + child tables)

Revision ID: 20260426_0000
Revises:
Create Date: 2026-04-26 00:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "20260426_0000"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(30), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("country_code", sa.String(3), nullable=False, server_default="TN"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "departments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("director_email", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "code", name="uq_department_tenant_code"),
    )

    op.create_table(
        "professors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "department_id",
            UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="SET NULL"),
        ),
        sa.Column("national_id", sa.String(20), unique=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("first_name_ar", sa.String(100)),
        sa.Column("last_name_ar", sa.String(100)),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(30)),
        sa.Column("gender", sa.String(15)),
        sa.Column("contract_type", sa.String(20), nullable=False, server_default="permanent"),
        sa.Column("rank", sa.String(50)),
        sa.Column("position_status", sa.String(20), server_default="active"),
        sa.Column("primary_specialty", sa.String(150)),
        sa.Column("hire_date", sa.Date),
        sa.Column("min_hours", sa.Integer),
        sa.Column("max_hours", sa.Integer),
        sa.Column("base_salary", sa.Numeric(12, 3)),
        sa.Column("photo_url", sa.Text),
        sa.Column("h_index", sa.Integer),
        sa.Column("h_index_updated_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "gender IS NULL OR gender IN ('M', 'F', 'other', 'undisclosed')",
            name="ck_professor_gender",
        ),
        sa.CheckConstraint(
            "contract_type IN ('permanent', 'contractual')",
            name="ck_professor_contract_type",
        ),
    )
    op.create_index("ix_professors_tenant_id", "professors", ["tenant_id"])
    op.create_index("ix_professors_department_id", "professors", ["department_id"])

    op.create_table(
        "professor_specializations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("professors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("domain", sa.String(100), nullable=False),
        sa.Column("subdomain", sa.String(100)),
        sa.Column("level", sa.String(20)),
        sa.Column("verified", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "professor_degrees",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("professors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("degree_type", sa.String(50)),
        sa.Column("field", sa.String(200)),
        sa.Column("institution", sa.String(200)),
        sa.Column("country", sa.String(100)),
        sa.Column("year", sa.Integer),
        sa.Column("document_url", sa.Text),
    )

    op.create_table(
        "professor_positions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("professors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("institution_id", UUID(as_uuid=True)),
        sa.Column("title", sa.String(200)),
        sa.Column("department", sa.String(200)),
        sa.Column("start_date", sa.Date),
        sa.Column("end_date", sa.Date),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "professor_publications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("professors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("journal", sa.String(300)),
        sa.Column("year", sa.Integer),
        sa.Column("doi", sa.String(200)),
        sa.Column("scopus_id", sa.String(100)),
        sa.Column("citation_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("source", sa.String(30)),
    )

    op.create_table(
        "professor_hours",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "professor_id",
            UUID(as_uuid=True),
            sa.ForeignKey("professors.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("semester", sa.String(10)),
        sa.Column("course_code", sa.String(50)),
        sa.Column("course_name", sa.String(300)),
        sa.Column("hours_scheduled", sa.Integer),
        sa.Column("hours_delivered", sa.Integer),
        sa.Column(
            "hours_extra",
            sa.Integer,
            sa.Computed(
                "GREATEST(COALESCE(hours_delivered,0) - COALESCE(hours_scheduled,0), 0)"
            ),
        ),
        sa.UniqueConstraint(
            "professor_id", "semester", "course_code", name="uq_prof_hours_semester_course"
        ),
    )


def downgrade() -> None:
    op.drop_table("professor_hours")
    op.drop_table("professor_publications")
    op.drop_table("professor_positions")
    op.drop_table("professor_degrees")
    op.drop_table("professor_specializations")
    op.drop_index("ix_professors_department_id", table_name="professors")
    op.drop_index("ix_professors_tenant_id", table_name="professors")
    op.drop_table("professors")
    op.drop_table("departments")
    op.drop_table("tenants")
