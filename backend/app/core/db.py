from collections.abc import AsyncGenerator
from contextlib import contextmanager
from typing import Generator

from sqlmodel import SQLModel, Session
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Async engine for FastAPI
engine = create_async_engine(
    (settings.DATABASE_URI if settings.DATABASE_URI else ""),
    echo=False,
    future=True,
)

# Sync engine for Celery workers (uses psycopg2 instead of asyncpg)
sync_database_uri = (
    settings.DATABASE_URI.replace("postgresql+asyncpg", "postgresql+psycopg2")
    if settings.DATABASE_URI
    else ""
)

sync_engine = create_engine(
    sync_database_uri,
    echo=False,
    pool_pre_ping=True,
)


async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session


@contextmanager
def get_sync_session() -> Generator[Session, None, None]:
    """
    Synchronous session for Celery workers.
    Use with 'with' statement: with get_sync_session() as session:
    """
    session = Session(sync_engine)
    try:
        yield session
    finally:
        session.close()
