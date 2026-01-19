from typing import AsyncGenerator
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import os
from dotenv import load_dotenv

# Load environment variables explicitly for tests
load_dotenv(".env.local")

from app.core.config import settings
from app.core.db import get_session
from app.main import app
from sqlmodel import SQLModel

# Use an in-memory SQLite database for testing, or a separate test DB
# For this setup I will use a separate async engine on the existing DB config
# but ideally we should use a test DB.
# Given the environment, I'll stick to a transaction-rollback pattern on the main DB or similar,
# but simplest here is to override the dependency.

# Actually, let's use the actual settings but maybe force a test mode if we had one.
# For now, we will create a new engine for the test session.


@pytest.fixture(scope="session")
def event_loop():
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def db_engine(event_loop):
    from app.core.config import settings
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(str(settings.DATABASE_URI), poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def session(db_engine):
    async with AsyncSession(db_engine) as session:
        yield session


@pytest.fixture(scope="function", autouse=True)
async def override_get_session(session):
    app.dependency_overrides[get_session] = lambda: session
    yield
    app.dependency_overrides = {}


@pytest.fixture(scope="module")
async def client() -> AsyncGenerator[AsyncClient, None]:
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as c:
        yield c


@pytest.fixture(scope="module")
async def db() -> AsyncGenerator[AsyncSession, None]:
    # In a real app we might use a separate database
    from app.core.db import engine

    async with AsyncSession(engine) as session:
        yield session
