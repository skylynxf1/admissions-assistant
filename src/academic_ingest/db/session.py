from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool


class DatabaseSettings(BaseModel):
    model_config = ConfigDict(frozen=True)

    url: str
    echo: bool = False


def create_engine_and_session(
    settings: DatabaseSettings | str,
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    database_settings = (
        settings if isinstance(settings, DatabaseSettings) else DatabaseSettings(url=settings)
    )
    database_url = database_settings.url
    engine_options: dict[str, object] = {
        "echo": database_settings.echo,
        "pool_pre_ping": True,
    }
    if database_url.startswith("sqlite+aiosqlite:///:memory:"):
        engine_options.update(
            {
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False},
            }
        )
    engine = create_async_engine(database_url, **engine_options)
    return engine, async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
