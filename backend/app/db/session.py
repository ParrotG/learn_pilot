from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None
_current_database_url: str | None = None


def configure_database(database_url: str) -> None:
    """Configure the shared async engine for the current process."""

    global _engine, _session_factory, _current_database_url

    if _engine is not None and _current_database_url == database_url:
        return

    _engine = create_async_engine(database_url, future=True, echo=False)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False, autoflush=False)
    _current_database_url = database_url


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Database engine has not been configured.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Database session factory has not been configured.")
    return _session_factory


async def get_db_session() -> AsyncIterator[AsyncSession]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session


async def dispose_database() -> None:
    global _engine, _session_factory, _current_database_url

    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
    _current_database_url = None

