"""Shared pytest fixtures — in-memory DB, HTTP client, token helpers."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.services.ingestion_service.main import create_app
from backend.services.ingestion_service.dependencies import get_db
from backend.shared.auth.jwt import issue_token
from backend.shared.auth.rbac import Role
from backend.shared.db.base import Base

# SQLite in-memory for tests (asyncio via aiosqlite)
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    app = create_app()

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def make_token(
    user_id: uuid.UUID | None = None,
    institution_id: uuid.UUID | None = None,
    role: Role = Role.INSTITUTION_ADMIN,
    secret: str = "change-me",
) -> str:
    uid = user_id or uuid.uuid4()
    iid = institution_id or uuid.uuid4()
    claims = {
        "sub": str(uid),
        "institution_id": str(iid),
        "role": role.value,
    }
    return issue_token(claims, secret)


@pytest.fixture
def institution_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def admin_token(institution_id) -> str:
    return make_token(institution_id=institution_id, role=Role.INSTITUTION_ADMIN)


@pytest.fixture
def analyst_token() -> str:
    return make_token(role=Role.UCAR_ANALYST)


@pytest.fixture
def super_admin_token() -> str:
    return make_token(role=Role.SUPER_ADMIN)
