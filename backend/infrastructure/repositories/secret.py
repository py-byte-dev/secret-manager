from collections.abc import Collection
from uuid import UUID

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from backend.application import interfaces
from backend.domain import exceptions as domain_exceptions
from backend.domain.entities.secret_dm import SecretDM
from backend.infrastructure.mapper.secret_cache import SecretCacheDataMapper

from sqlalchemy.exc import ProgrammingError
from psycopg.errors import UndefinedTable


class SecretRepository(
    interfaces.SecretReader,
    interfaces.SecretSaver,
    interfaces.SecretDeleter,
):
    def __init__(
            self,
            session: AsyncSession,
            redis_client: redis.Redis,
            data_mapper: SecretCacheDataMapper,
    ) -> None:
        self._session = session
        self._redis_client = redis_client
        self._data_mapper = data_mapper

    async def get_by_id(self, secret_id: UUID) -> SecretDM:
        cache = await self._redis_client.get(str(secret_id))
        if cache:
            return self._data_mapper.json_to_entity(data=cache)

        query = text(
            'SELECT uuid, secret, passphrase, created_at, expired_at, is_deleted FROM secrets WHERE uuid = :uuid AND is_deleted = FALSE',
        )
        result = await self._session.execute(statement=query, params={'uuid': secret_id})
        row = result.fetchone()

        if not row:
            raise domain_exceptions.SecretNotFound

        return SecretDM(
            uuid=row.uuid,
            secret=row.secret,
            passphrase=row.passphrase,
            created_at=row.created_at,
            expired_at=row.expired_at,
            is_deleted=row.is_deleted,
        )

    async def get_all_expirable(self) -> Collection[SecretDM]:
        query = text(
            'SELECT uuid, secret, passphrase, created_at, expired_at, is_deleted FROM secrets WHERE expired_at IS NOT NULL AND is_deleted = FALSE',
        )
        result = await self._session.execute(statement=query)
        rows = result.fetchall()

        return [
            SecretDM(
                uuid=row.uuid,
                secret=row.secret,
                passphrase=row.passphrase,
                created_at=row.created_at,
                expired_at=row.expired_at,
                is_deleted=row.is_deleted,
            )
            for row in rows
        ]

    async def save(self, secret: SecretDM, ttl: int = 300) -> None:
        stmt = text(
            'INSERT INTO secrets(uuid, secret, passphrase, created_at, expired_at, is_deleted) '
            'VALUES '
            '(:uuid, :secret, :passphrase, :created_at, :expired_at, :is_deleted)',
        )

        await self._session.execute(
            statement=stmt,
            params={
                'uuid': secret.uuid,
                'secret': secret.secret,
                'passphrase': secret.passphrase,
                'created_at': secret.created_at,
                'expired_at': secret.expired_at,
                'is_deleted': secret.is_deleted,
            },
        )

        value = self._data_mapper.entity_to_json(secret=secret)
        await self._redis_client.set(name=str(secret.uuid), value=value, ex=ttl)

    async def delete(self, secret: SecretDM) -> None:
        stmt = text('UPDATE secrets SET is_deleted = TRUE WHERE uuid = :uuid')
        await self._session.execute(
            statement=stmt,
            params={'uuid': secret.uuid},
        )

        await self._redis_client.delete(str(secret.uuid))
