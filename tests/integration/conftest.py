from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from academic_ingest.db.base import Base
from academic_ingest.db.session import create_engine_and_session


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine, session_factory = create_engine_and_session("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with session_factory() as session:
        yield session
    await engine.dispose()
