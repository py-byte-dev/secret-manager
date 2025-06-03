import os
from collections.abc import AsyncGenerator, AsyncIterable
from typing import Any
from unittest.mock import AsyncMock

import pytest
import redis.asyncio as redis
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.config import Config
from backend.infrastructure.mapper.secret_cache import SecretCacheDataMapper
from backend.infrastructure.models import Base

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope='session')
def faker() -> Faker:
    return Faker()


@pytest.fixture(scope='session')
def config() -> Config:
    config = Config()
    config.pg.db = os.getenv('TEST_DB')
    config.redis.db = os.getenv('TEST_REDIS_DB')
    return config


@pytest.fixture(scope='session')
def data_mapper() -> SecretCacheDataMapper:
    return SecretCacheDataMapper()


@pytest.fixture(scope='session')
async def session_maker(config: Config) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(config.pg.create_connection_string())

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    return async_sessionmaker(bind=engine, class_=AsyncSession, autoflush=False, expire_on_commit=False)


@pytest.fixture
async def session(session_maker: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, Any]:
    async with session_maker() as session:
        session.commit = AsyncMock()
        yield session
        await session.rollback()


@pytest.fixture
async def redis_pool(config: Config) -> AsyncIterable[redis.ConnectionPool]:
    pool = redis.ConnectionPool.from_url(url=config.redis.create_connection_string())
    yield pool
    await pool.aclose()


@pytest.fixture
async def redis_client(redis_pool: redis.ConnectionPool) -> AsyncIterable[redis.Redis]:
    client = redis.Redis(connection_pool=redis_pool)
    yield client
    await client.flushdb()
    await client.aclose()
