from collections.abc import AsyncIterator
from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from dishka import AnyOf, AsyncContainer, Provider, Scope, make_async_container, provide
from dishka.integrations import fastapi as fastapi_integration
from faker import Faker
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend import ioc
from backend.application import interfaces
from backend.config import Config
from backend.domain.entities.event_dm import EventType
from backend.infrastructure.models import Event, Secret
from backend.presentation.api.exceptions_mapping import EXCEPTIONS_MAPPING
from backend.presentation.api.routers import router

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_provider(session: AsyncSession) -> Provider:
    class MockProvider(ioc.ApplicationProvider, ioc.InfrastructureProvider):
        @provide(scope=Scope.REQUEST)
        async def get_session(self) -> AnyOf[AsyncSession, interfaces.DBSession]:
            return session

        @provide(scope=Scope.REQUEST, provides=interfaces.EncryptionService)
        def get_encryption_service(self) -> interfaces.EncryptionService:
            encryption_service = MagicMock()

            encryption_service.encrypt = lambda plaintext, **kwargs: (plaintext + '_encrypt_data').encode()
            encryption_service.decrypt = (
                lambda ciphertext, **kwargs: ciphertext.decode().replace('_encrypt_data', '').encode()
            )

            return encryption_service

    return MockProvider()


@pytest.fixture
def container(mock_provider: Provider, config: Config) -> AsyncContainer:
    return make_async_container(mock_provider, context={Config: config})


@pytest.fixture
async def client(container: AsyncContainer) -> AsyncIterator[AsyncClient]:
    app = FastAPI(exception_handlers=EXCEPTIONS_MAPPING)
    app.include_router(router)
    fastapi_integration.setup_dishka(container, app)
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        yield client


async def test_create_secret(session: AsyncSession, client: AsyncClient, faker: Faker):
    secret = faker.pystr(min_chars=10)
    response = await client.post(url='/api/secret', json={'secret': secret})
    assert response.status_code == 200
    assert 'secret_key' in response.json()


async def test_success_get_secret(session: AsyncSession, client: AsyncClient, faker: Faker):
    uuid = str(uuid4())
    secret = faker.pystr(min_chars=10)

    session.add(
        Secret(
            uuid=uuid,
            secret=secret.encode(),
            passphrase=None,
            created_at=datetime.now(),
            expired_at=None,
            is_deleted=False,
        )
    )
    await session.flush()

    response = await client.get(url=f'/api/secret/{uuid}')
    assert response.status_code == 200
    assert response.json()['secret'] == secret


async def test_failure_get_secret(session: AsyncSession, client: AsyncClient, faker: Faker):
    uuid = str(uuid4())
    secret = faker.pystr(min_chars=10)

    session.add(
        Secret(
            uuid=uuid,
            secret=secret.encode(),
            passphrase=None,
            created_at=datetime.now(),
            expired_at=None,
            is_deleted=True,
        )
    )
    await session.flush()

    response = await client.get(url=f'/api/secret/{uuid}')
    assert response.status_code == 404


async def test_delete_secret(session: AsyncSession, client: AsyncClient, faker: Faker):
    uuid = str(uuid4())
    secret = faker.pystr(min_chars=10)

    session.add(
        Secret(
            uuid=uuid,
            secret=secret.encode(),
            passphrase=None,
            created_at=datetime.now(),
            expired_at=None,
            is_deleted=False,
        )
    )
    await session.flush()

    response = await client.delete(url=f'/api/secret/{uuid}')
    assert response.status_code == 200


async def test_get_events(session: AsyncSession, client: AsyncClient, faker: Faker):
    uuid = str(uuid4())
    client_id = faker.ipv4()
    client_user_agent = faker.user_agent()
    event_type = EventType.CREATE
    created_at = datetime.now()
    secret_id = str(uuid4())

    session.add(
        Event(
            uuid=uuid,
            client_ip=client_id,
            client_user_agent=client_user_agent,
            type=event_type,
            created_at=created_at,
            secret_id=secret_id,
        ),
    )
    await session.flush()

    response = await client.get(url='/api/event', params={'page': 1, 'page_size': 1})
    assert response.status_code == 200

    response_json = response.json()
    assert response_json['events'][0]['client_ip'] == client_id
    assert response_json['events'][0]['client_user_agent'] == client_user_agent
    assert response_json['events'][0]['type'] == event_type
    assert datetime.fromisoformat(response_json['events'][0]['created_at']) == created_at
    assert response_json['events'][0]['secret_id'] == secret_id
