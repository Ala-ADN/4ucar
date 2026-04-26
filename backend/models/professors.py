"""HR schema: professor records, specializations, degrees, positions, hours.

Mirrors §6.1 of the master spec, with `department` modelled as an FK to a
`departments` lookup table rather than a free-text column.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.db.base import Base
from backend.shared.db.types import TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from backend.models.tenants import Department, Tenant


GENDER_VALUES = ("M", "F", "other", "undisclosed")
CONTRACT_TYPES = ("permanent", "contractual")
POSITION_STATUSES = ("active", "on_leave", "suspended", "retired")
DEGREE_LEVELS = ("primary", "secondary", "emerging")
PUBLICATION_SOURCES = ("manual", "scopus_api", "openalex", "doc_extract")


def _sql_in(values: tuple[str, ...]) -> str:
    return "(" + ", ".join(f"'{v}'" for v in values) + ")"


class Professor(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "professors"
    __table_args__ = (
        CheckConstraint(
            f"gender IS NULL OR gender IN {_sql_in(GENDER_VALUES)}",
            name="ck_professor_gender",
        ),
        CheckConstraint(
            f"contract_type IN {_sql_in(CONTRACT_TYPES)}",
            name="ck_professor_contract_type",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    department_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL")
    )

    national_id: Mapped[str | None] = mapped_column(String(20), unique=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    first_name_ar: Mapped[str | None] = mapped_column(String(100))
    last_name_ar: Mapped[str | None] = mapped_column(String(100))

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))

    gender: Mapped[str | None] = mapped_column(String(15))
    contract_type: Mapped[str] = mapped_column(String(20), nullable=False, default="permanent")
    rank: Mapped[str | None] = mapped_column(String(50))
    position_status: Mapped[str | None] = mapped_column(String(20), default="active")
    primary_specialty: Mapped[str | None] = mapped_column(String(150))

    hire_date: Mapped[date | None] = mapped_column(Date)
    min_hours: Mapped[int | None] = mapped_column(Integer)
    max_hours: Mapped[int | None] = mapped_column(Integer)
    base_salary: Mapped[Decimal | None] = mapped_column(Numeric(12, 3))
    photo_url: Mapped[str | None] = mapped_column(Text)

    h_index: Mapped[int | None] = mapped_column(Integer)
    h_index_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    tenant: Mapped["Tenant"] = relationship(back_populates="professors")
    department: Mapped["Department | None"] = relationship(back_populates="professors")
    specializations: Mapped[list["ProfessorSpecialization"]] = relationship(
        back_populates="professor", cascade="all, delete-orphan"
    )
    degrees: Mapped[list["ProfessorDegree"]] = relationship(
        back_populates="professor", cascade="all, delete-orphan"
    )
    positions: Mapped[list["ProfessorPosition"]] = relationship(
        back_populates="professor", cascade="all, delete-orphan"
    )
    publications: Mapped[list["ProfessorPublication"]] = relationship(
        back_populates="professor", cascade="all, delete-orphan"
    )
    hours: Mapped[list["ProfessorHours"]] = relationship(
        back_populates="professor", cascade="all, delete-orphan"
    )


class ProfessorSpecialization(UUIDPKMixin, Base):
    __tablename__ = "professor_specializations"

    professor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("professors.id", ondelete="CASCADE"), nullable=False
    )
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    subdomain: Mapped[str | None] = mapped_column(String(100))
    level: Mapped[str | None] = mapped_column(String(20))
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    professor: Mapped[Professor] = relationship(back_populates="specializations")


class ProfessorDegree(UUIDPKMixin, Base):
    __tablename__ = "professor_degrees"

    professor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("professors.id", ondelete="CASCADE"), nullable=False
    )
    degree_type: Mapped[str | None] = mapped_column(String(50))
    field: Mapped[str | None] = mapped_column(String(200))
    institution: Mapped[str | None] = mapped_column(String(200))
    country: Mapped[str | None] = mapped_column(String(100))
    year: Mapped[int | None] = mapped_column(Integer)
    document_url: Mapped[str | None] = mapped_column(Text)

    professor: Mapped[Professor] = relationship(back_populates="degrees")


class ProfessorPosition(UUIDPKMixin, Base):
    __tablename__ = "professor_positions"

    professor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("professors.id", ondelete="CASCADE"), nullable=False
    )
    institution_id: Mapped[UUID | None] = mapped_column(PG_UUID(as_uuid=True))
    title: Mapped[str | None] = mapped_column(String(200))
    department: Mapped[str | None] = mapped_column(String(200))
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    professor: Mapped[Professor] = relationship(back_populates="positions")


class ProfessorPublication(UUIDPKMixin, Base):
    __tablename__ = "professor_publications"

    professor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("professors.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    journal: Mapped[str | None] = mapped_column(String(300))
    year: Mapped[int | None] = mapped_column(Integer)
    doi: Mapped[str | None] = mapped_column(String(200))
    scopus_id: Mapped[str | None] = mapped_column(String(100))
    citation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source: Mapped[str | None] = mapped_column(String(30))

    professor: Mapped[Professor] = relationship(back_populates="publications")


class ProfessorHours(UUIDPKMixin, Base):
    __tablename__ = "professor_hours"
    __table_args__ = (
        UniqueConstraint(
            "professor_id", "semester", "course_code", name="uq_prof_hours_semester_course"
        ),
    )

    professor_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("professors.id", ondelete="CASCADE"), nullable=False
    )
    semester: Mapped[str | None] = mapped_column(String(10))
    course_code: Mapped[str | None] = mapped_column(String(50))
    course_name: Mapped[str | None] = mapped_column(String(300))
    hours_scheduled: Mapped[int | None] = mapped_column(Integer)
    hours_delivered: Mapped[int | None] = mapped_column(Integer)
    hours_extra: Mapped[int | None] = mapped_column(
        Integer,
        Computed("GREATEST(COALESCE(hours_delivered,0) - COALESCE(hours_scheduled,0), 0)"),
    )

    professor: Mapped[Professor] = relationship(back_populates="hours")
