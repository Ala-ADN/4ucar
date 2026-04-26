"""Seed the database with INSAT faculty (DGIM and DGPI departments).

Idempotent: re-running upserts on (tenant.code), (tenant_id, dept.code), and
professor.email. Run *after* `alembic upgrade head` has created the schema.

Usage:
    python -m scripts.seed_insat_dgim_dgpi
"""

from __future__ import annotations

import asyncio
import sys

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.professors import Professor, ProfessorPosition, ProfessorSpecialization
from backend.models.tenants import Department, Tenant
from backend.shared.db.session import get_engine, get_sessionmaker
from data.seeds.insat_faculty import (
    DEPARTMENTS,
    FACULTY,
    TENANT_CODE,
    TENANT_NAME,
    FacultyRecord,
)


async def _upsert_tenant(session: AsyncSession) -> Tenant:
    existing = await session.scalar(select(Tenant).where(Tenant.code == TENANT_CODE))
    if existing is not None:
        existing.name = TENANT_NAME
        return existing
    tenant = Tenant(code=TENANT_CODE, name=TENANT_NAME, country_code="TN")
    session.add(tenant)
    await session.flush()
    return tenant


async def _upsert_departments(session: AsyncSession, tenant: Tenant) -> dict[str, Department]:
    out: dict[str, Department] = {}
    for spec in DEPARTMENTS:
        existing = await session.scalar(
            select(Department).where(
                Department.tenant_id == tenant.id, Department.code == spec["code"]
            )
        )
        if existing is None:
            existing = Department(tenant_id=tenant.id, code=spec["code"], name=spec["name"])
            session.add(existing)
        existing.name = spec["name"]
        existing.director_email = spec.get("director_email")
        out[spec["code"]] = existing
    await session.flush()
    return out


async def _upsert_professor(
    session: AsyncSession,
    tenant: Tenant,
    departments: dict[str, Department],
    rec: FacultyRecord,
) -> tuple[Professor, bool]:
    """Insert or update a professor by email. Returns (professor, created)."""
    department = departments[rec["department_code"]]

    existing = await session.scalar(select(Professor).where(Professor.email == rec["email"]))
    created = existing is None
    prof = existing or Professor(email=rec["email"], tenant_id=tenant.id, first_name="", last_name="")

    prof.tenant_id = tenant.id
    prof.department_id = department.id
    prof.first_name = rec["first_name"]
    prof.last_name = rec["last_name"]
    prof.gender = rec.get("gender")
    prof.rank = rec.get("rank")
    prof.primary_specialty = rec.get("specialty")
    prof.contract_type = "permanent"
    prof.position_status = "active"

    if created:
        session.add(prof)
        await session.flush()
    else:
        await session.execute(
            delete(ProfessorSpecialization)
            .where(ProfessorSpecialization.professor_id == prof.id)
            .where(ProfessorSpecialization.level == "primary")
        )
        await session.execute(
            delete(ProfessorPosition)
            .where(ProfessorPosition.professor_id == prof.id)
            .where(ProfessorPosition.is_current.is_(True))
        )
        await session.flush()

    if rec.get("specialty"):
        session.add(
            ProfessorSpecialization(
                professor_id=prof.id,
                domain=rec["specialty"],
                level="primary",
                verified=False,
            )
        )

    session.add(
        ProfessorPosition(
            professor_id=prof.id,
            title=rec.get("rank"),
            department=department.name,
            is_current=True,
        )
    )

    return prof, created


async def seed() -> dict[str, int]:
    sessionmaker = get_sessionmaker()
    created_count = 0
    updated_count = 0
    async with sessionmaker() as session:
        async with session.begin():
            tenant = await _upsert_tenant(session)
            departments = await _upsert_departments(session, tenant)
            for rec in FACULTY:
                _, created = await _upsert_professor(session, tenant, departments, rec)
                if created:
                    created_count += 1
                else:
                    updated_count += 1
    return {
        "tenant": TENANT_CODE,
        "departments": len(DEPARTMENTS),
        "faculty_total": len(FACULTY),
        "created": created_count,
        "updated": updated_count,
    }


async def _main() -> int:
    summary = await seed()
    print("Seed complete:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    await get_engine().dispose()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
