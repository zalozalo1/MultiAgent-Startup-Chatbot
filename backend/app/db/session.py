"""Async SQLAlchemy engine and session management."""

import logging
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.db.base import Base

logger = logging.getLogger(__name__)

engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> bool:
    """Create tables. Returns False (instead of raising) when the database is
    unreachable, so the app can still boot and report a degraded /health."""
    # Imported for their table definitions before create_all.
    from app.models import conversation, run  # noqa: F401

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return True
    except Exception as exc:
        logger.warning("Database unavailable, persistence disabled: %s", exc)
        return False


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
