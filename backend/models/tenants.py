"""Tenants (institutions) and their administrative subdivisions (departments)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.shared.db.base import Base
from backend.shared.db.types import TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from backend.models.professors import Professor


class Tenant(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    country_code: Mapped[str] = mapped_column(String(3), nullable=False, default="TN")

    departments: Mapped[list["Department"]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    professors: Mapped[list["Professor"]] = relationship(back_populates="tenant")


class Department(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_department_tenant_code"),)

    tenant_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    director_email: Mapped[str | None] = mapped_column(String(255))

    tenant: Mapped[Tenant] = relationship(back_populates="departments")
    professors: Mapped[list["Professor"]] = relationship(back_populates="department")


class User:
    """Placeholder for the user/identity model (Keycloak-mirrored)."""
