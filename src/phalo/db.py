"""Async engine over the shared Postgres.

Phalo uses SQLAlchemy Core with explicit SQL — it reads nuwa's domain tables
(never modelled here; nuwa's Prisma schema is their source of truth) and
writes only to the `phalo` schema (owned by Alembic migrations in this repo).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

from phalo.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_settings().async_database_url,
            pool_size=5,
            max_overflow=5,
            pool_pre_ping=True,
        )
    return _engine


@asynccontextmanager
async def connection() -> AsyncIterator[AsyncConnection]:
    """A connection with an open transaction (commits on clean exit)."""
    async with get_engine().begin() as conn:
        yield conn


async def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
