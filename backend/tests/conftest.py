import os

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_trustwipe.db"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.core.config import get_settings
from app.db.session import Base, engine


@pytest_asyncio.fixture(autouse=True)
async def _reset_db():
    """Fresh schema for every test — keeps tests independent so ledger
    chain assertions aren't affected by ordering or leftover data."""
    get_settings.cache_clear()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
