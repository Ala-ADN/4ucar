"""SQLAlchemy ORM models — one module per aggregate.

Every model module is imported here so that `Base.metadata` is populated
before Alembic autogeneration / migrations run.
"""

from backend.models.professors import (  # noqa: F401
    Professor,
    ProfessorDegree,
    ProfessorHours,
    ProfessorPosition,
    ProfessorPublication,
    ProfessorSpecialization,
)
from backend.models.tenants import Department, Tenant  # noqa: F401
