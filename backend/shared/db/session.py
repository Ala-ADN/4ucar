"""Async SQLAlchemy engine and session factory.

Lazily constructed singletons - the engine pool is shared across the
process. `get_session()` is a FastAPI dependency that yields a session
inside an async context manager so commit/rollback semantics are owned
by the request handler.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.shared.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            echo=settings.database_echo,
            future=True,
            pool_pre_ping=True,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields one session per request.

    The handler owns commit/rollback. On exception, SQLAlchemy rolls back
    automatically inside the context manager.
    """
    async with get_sessionmaker()() as session:
        yield session
