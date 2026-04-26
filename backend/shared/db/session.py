"""Async SQLAlchemy engine and session factory."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.shared.config import Settings

_engine = None
_sessionmaker = None


def get_engine(settings: Settings):
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.postgres_dsn,
            pool_size=10,
            max_overflow=20,
            echo=settings.app_env == "local",
        )
    return _engine


def get_sessionmaker(settings: Settings) -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        engine = get_engine(settings)
        _sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    return _sessionmaker


async def get_session(settings: Settings) -> AsyncGenerator[AsyncSession, None]:
    factory = get_sessionmaker(settings)
    async with factory() as session:
        yield session
