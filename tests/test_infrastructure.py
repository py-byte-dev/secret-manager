import json
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
import redis.asyncio as redis
from faker import Faker
from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.event_dm import EventDM, EventType
from backend.domain.entities.secret_dm import SecretDM
from backend.infrastructure.mapper.secret_cache import SecretCacheDataMapper
from backend.infrastructure.models import Event, Secret
from backend.infrastructure.repositories.event import EventRepository
from backend.infrastructure.repositories.secret import SecretRepository

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def secret_repo(
    session: AsyncSession, redis_client: redis.Redis, data_mapper: SecretCacheDataMapper
) -> SecretRepository:
    return SecretRepository(session=session, redis_client=redis_client, data_mapper=data_mapper)


@pytest.fixture
async def event_repo(session: AsyncSession) -> EventRepository:
    return EventRepository(session=session)


async def test_save_secret_without_optional_params(
    session: AsyncSession,
    redis_client: redis.Redis,
    secret_repo: SecretRepository,
    faker: Faker,
) -> None:
    secret_dm = SecretDM(
        uuid=str(uuid4()),
        secret=faker.pystr(min_chars=10).encode(),
        passphrase=None,
        created_at=datetime.now(),
        expired_at=None,
        is_deleted=False,
    )

    await secret_repo.save(secret=secret_dm)

    result = await session.execute(select(Secret).where(Secret.uuid == secret_dm.uuid))
    rows = result.fetchall()
    assert len(rows) == 1
    secret = rows[0][0]
    assert secret.secret == secret_dm.secret
    assert secret.passphrase == secret_dm.passphrase
    assert secret.created_at == secret_dm.created_at
    assert secret.expired_at == secret_dm.expired_at
    assert secret.is_deleted == secret_dm.is_deleted

    cache_result = await redis_client.get(str(secret_dm.uuid))
    assert cache_result is not None

    cache_json = json.loads(cache_result)
    cache_secret = cache_json['secret'].encode() if cache_json['secret'] else None
    cache_passphrase = cache_json['passphrase'].encode() if cache_json['passphrase'] else None
    cache_created_at = (
        datetime.fromisoformat(cache_json['created_at']) if isinstance(cache_json['created_at'], str) else None
    )
    cache_expired_at = (
        datetime.fromisoformat(cache_json['expired_at']) if isinstance(cache_json['expired_at'], str) else None
    )

    assert cache_secret == secret_dm.secret
    assert cache_passphrase == secret_dm.passphrase
    assert cache_created_at == secret_dm.created_at
    assert cache_expired_at == secret_dm.expired_at
    assert cache_json['is_deleted'] == secret_dm.is_deleted

    ttl = await redis_client.ttl(str(secret_dm.uuid))
    assert 250 <= ttl <= 300


async def test_save_secret_with_optional_params(
    session: AsyncSession,
    redis_client: redis.Redis,
    secret_repo: SecretRepository,
    faker: Faker,
) -> None:
    secret_dm = SecretDM(
        uuid=str(uuid4()),
        secret=faker.pystr(min_chars=10).encode(),
        passphrase=faker.pystr(min_chars=10).encode(),
        created_at=datetime.now(),
        expired_at=datetime.now() + timedelta(seconds=300),
        is_deleted=False,
    )

    await secret_repo.save(secret=secret_dm)

    result = await session.execute(select(Secret).where(Secret.uuid == secret_dm.uuid))
    rows = result.fetchall()
    assert len(rows) == 1
    secret = rows[0][0]
    assert secret.secret == secret_dm.secret
    assert secret.passphrase == secret_dm.passphrase
    assert secret.created_at == secret_dm.created_at
    assert secret.expired_at == secret_dm.expired_at
    assert secret.is_deleted == secret_dm.is_deleted

    cache_result = await redis_client.get(str(secret_dm.uuid))
    assert cache_result is not None

    cache_json = json.loads(cache_result)
    cache_secret = cache_json['secret'].encode() if cache_json['secret'] else None
    cache_passphrase = cache_json['passphrase'].encode() if cache_json['passphrase'] else None
    cache_created_at = (
        datetime.fromisoformat(cache_json['created_at']) if isinstance(cache_json['created_at'], str) else None
    )
    cache_expired_at = (
        datetime.fromisoformat(cache_json['expired_at']) if isinstance(cache_json['expired_at'], str) else None
    )

    assert cache_secret == secret_dm.secret
    assert cache_passphrase == secret_dm.passphrase
    assert cache_created_at == secret_dm.created_at
    assert cache_expired_at == secret_dm.expired_at
    assert cache_json['is_deleted'] == secret_dm.is_deleted

    ttl = await redis_client.ttl(str(secret_dm.uuid))
    assert 250 <= ttl <= 300


async def test_delete_secret(
    session: AsyncSession,
    redis_client: redis.Redis,
    secret_repo: SecretRepository,
    faker: Faker,
):
    secret_dm = SecretDM(
        uuid=str(uuid4()),
        secret=faker.pystr(min_chars=10).encode(),
        passphrase=faker.pystr(min_chars=10).encode(),
        created_at=datetime.now(),
        expired_at=datetime.now() + timedelta(seconds=300),
        is_deleted=False,
    )

    await session.execute(
        insert(Secret).values(
            uuid=secret_dm.uuid,
            secret=secret_dm.secret,
            passphrase=secret_dm.passphrase,
            created_at=secret_dm.created_at,
            expired_at=secret_dm.expired_at,
            is_deleted=secret_dm.is_deleted,
        )
    )

    secret_dm.is_deleted = True
    await secret_repo.delete(secret=secret_dm)
    result = await session.execute(select(Secret).where(Secret.uuid == secret_dm.uuid))
    secret = result.fetchone()[0]

    assert secret.is_deleted is True
    cache_result = await redis_client.get(str(secret_dm.uuid))
    assert cache_result is None


async def test_save_event(
    session: AsyncSession,
    event_repo: EventRepository,
    faker: Faker,
) -> None:
    event_dm = EventDM(
        uuid=str(uuid4()),
        client_ip=faker.ipv4(),
        client_user_agent=faker.user_agent(),
        type=EventType.CREATE,
        created_at=datetime.now(),
        secret_id=str(uuid4()),
    )

    await event_repo.save(event=event_dm)
    result = await session.execute(select(Event).where(Event.uuid == event_dm.uuid))
    rows = result.fetchall()
    assert len(rows) == 1
    event = rows[0][0]

    assert event.client_ip == event_dm.client_ip
    assert event.client_user_agent == event_dm.client_user_agent
    assert event.type == event_dm.type
    assert event.created_at == event_dm.created_at
    assert str(event.secret_id) == event_dm.secret_id
