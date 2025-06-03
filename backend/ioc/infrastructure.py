import hashlib
from collections.abc import AsyncIterable, Iterable
from concurrent.futures import ThreadPoolExecutor

import redis.asyncio as redis
from dishka import AnyOf, Provider, Scope, provide, from_context
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.application import interfaces
from backend.application.use_cases.secret import SecretDeleteManager
from backend.config import Config
from backend.infrastructure.mapper.secret_cache import SecretCacheDataMapper
from backend.infrastructure.repositories.event import EventRepository
from backend.infrastructure.repositories.secret import SecretRepository
from backend.infrastructure.services.bcrypt_hasher import BcryptHasher
from backend.infrastructure.services.encryption import EncryptionService


class InfrastructureProvider(Provider):
    config = from_context(provides=Config, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def get_thread_pool(self) -> Iterable[ThreadPoolExecutor]:
        thread_pool = ThreadPoolExecutor(max_workers=8)
        yield thread_pool
        thread_pool.shutdown()

    @provide(scope=Scope.APP)
    def get_session_maker(self, config: Config) -> async_sessionmaker[AsyncSession]:
        engine = create_async_engine(
            config.pg.create_connection_string(),
            pool_size=15,
            max_overflow=15,
            connect_args={
                'connect_timeout': 5,
            },
        )
        return async_sessionmaker(engine, class_=AsyncSession, autoflush=False, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def get_session(
            self,
            session_maker: async_sessionmaker[AsyncSession],
    ) -> AsyncIterable[
        AnyOf[
            AsyncSession,
            interfaces.DBSession,
        ]
    ]:
        async with session_maker() as session:
            yield session

    @provide(scope=Scope.APP)
    async def get_redis_connection_pool(self, config: Config) -> AsyncIterable[redis.ConnectionPool]:
        pool = redis.ConnectionPool.from_url(url=config.redis.create_connection_string())
        yield pool
        await pool.aclose()

    @provide(scope=Scope.REQUEST)
    async def get_redis_client(self, pool: redis.ConnectionPool) -> AsyncIterable[redis.Redis]:
        client = redis.Redis(connection_pool=pool)
        yield client
        await client.aclose()

    @provide(scope=Scope.REQUEST, provides=interfaces.EncryptionService)
    def get_encription_service(self, config: Config) -> EncryptionService:
        return EncryptionService(secret_key=hashlib.sha256(config.encryption.secret_key.encode()).digest())

    bcrypt_hasher = provide(
        BcryptHasher,
        scope=Scope.REQUEST,
        provides=interfaces.BcryptHasher,
    )

    secret_cache_data_mapper = provide(SecretCacheDataMapper, scope=Scope.REQUEST)
    secret_repo = provide(
        SecretRepository,
        scope=Scope.REQUEST,
        provides=AnyOf[interfaces.SecretReader, interfaces.SecretSaver, SecretDeleteManager],
    )

    event_repo = provide(
        EventRepository,
        scope=Scope.REQUEST,
        provides=AnyOf[interfaces.EventReader, interfaces.EventSaver],
    )
