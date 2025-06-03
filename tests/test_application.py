from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from unittest.mock import MagicMock, create_autospec
from uuid import UUID

import pytest
from faker import Faker

from backend.application import interfaces
from backend.application.dto.secret import CreateSecretDTO
from backend.application.use_cases.secret import (
    CreateSecretInteractor,
    DeleteSecretInteractor,
    GetSecretInteractor,
    SecretDeleteManager,
)
from backend.domain.entities.secret_dm import SecretDM

pytestmark = pytest.mark.asyncio


@pytest.fixture
def create_secret_interactor(faker: Faker) -> CreateSecretInteractor:
    thread_pool = create_autospec(ThreadPoolExecutor)
    secret_repo = create_autospec(interfaces.SecretSaver)
    event_repo = create_autospec(interfaces.EventSaver)
    db_session = create_autospec(interfaces.DBSession)
    encription_service = create_autospec(interfaces.EncryptionService)
    hasher = create_autospec(interfaces.BcryptHasher)
    current_dt = MagicMock(return_value=datetime(2025, 4, 10, 10, 7, 42, 123456))
    uuid_generator = MagicMock(return_value=UUID('12345678-1234-5678-1234-567812345678'))

    def submit_mock(func, *args, **kwargs):
        future = Future()
        try:
            result = func(*args, **kwargs)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        return future

    thread_pool.submit.side_effect = submit_mock

    return CreateSecretInteractor(
        thread_pool=thread_pool,
        secret_saver=secret_repo,
        event_saver=event_repo,
        db_session=db_session,
        encription_service=encription_service,
        hasher=hasher,
        current_dt=current_dt,
        uuid_generator=uuid_generator,
    )


@pytest.fixture
def get_secret_interactor(faker: Faker) -> GetSecretInteractor:
    thread_pool = create_autospec(ThreadPoolExecutor)
    secret_repo = create_autospec(SecretDeleteManager)
    event_repo = create_autospec(interfaces.EventSaver)
    db_session = create_autospec(interfaces.DBSession)
    encription_service = create_autospec(interfaces.EncryptionService)
    current_dt = MagicMock(return_value=datetime(2025, 4, 10, 10, 7, 42, 123456))
    uuid_generator = MagicMock(return_value=UUID('12345678-1234-5678-1234-567812345678'))

    def submit_mock(func, *args, **kwargs):
        future = Future()
        try:
            result = func(*args, **kwargs)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        return future

    thread_pool.submit.side_effect = submit_mock

    secret_dm = SecretDM(
        uuid=UUID('12345678-1234-5678-1234-567812345678'),
        secret=b'secret',
        passphrase=None,
        created_at=datetime(2025, 4, 10, 10, 7, 42, 123456),
        expired_at=None,
        is_deleted=False,
    )

    secret_repo.get_by_id.return_value = secret_dm

    def mock_decrypt(ciphertext):
        return ciphertext

    encription_service.decrypt.side_effect = mock_decrypt

    return GetSecretInteractor(
        thread_pool=thread_pool,
        secret_delete_manager=secret_repo,
        event_saver=event_repo,
        db_session=db_session,
        encription_service=encription_service,
        current_dt=current_dt,
        uuid_generator=uuid_generator,
    )


@pytest.fixture
def delete_secret_interactor(faker: Faker) -> DeleteSecretInteractor:
    thread_pool = create_autospec(ThreadPoolExecutor)
    secret_repo = create_autospec(SecretDeleteManager)
    event_repo = create_autospec(interfaces.EventSaver)
    db_session = create_autospec(interfaces.DBSession)
    hasher = create_autospec(interfaces.BcryptHasher)

    current_dt = MagicMock(return_value=datetime(2025, 4, 10, 10, 7, 42, 123456))
    uuid_generator = MagicMock(return_value=UUID('12345678-1234-5678-1234-567812345678'))

    def submit_mock(func, *args, **kwargs):
        future = Future()
        try:
            result = func(*args, **kwargs)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        return future

    thread_pool.submit.side_effect = submit_mock

    secret_dm = SecretDM(
        uuid=UUID('12345678-1234-5678-1234-567812345678'),
        secret=b'secret',
        passphrase=None,
        created_at=datetime(2025, 4, 10, 10, 7, 42, 123456),
        expired_at=None,
        is_deleted=False,
    )

    secret_repo.get_by_id.return_value = secret_dm

    return DeleteSecretInteractor(
        thread_pool=thread_pool,
        secret_delete_manager=secret_repo,
        event_saver=event_repo,
        db_session=db_session,
        hasher=hasher,
        current_dt=current_dt,
        uuid_generator=uuid_generator,
    )


async def test_create_secret(create_secret_interactor: CreateSecretInteractor, faker: Faker) -> None:
    uuid = create_secret_interactor._uuid_generator()
    secret = faker.pystr(min_chars=10)
    passphrase = faker.pystr(min_chars=10)
    client_ip = faker.ipv4()
    client_user_agent = faker.user_agent()

    data = CreateSecretDTO(
        secret=secret,
        passphrase=passphrase,
        ttl_seconds=None,
    )

    result = await create_secret_interactor(data=data, client_ip=client_ip, client_user_agent=client_user_agent)
    create_secret_interactor._hasher.hash.assert_called_once_with(raw_data=data.passphrase)
    create_secret_interactor._encription_service.encrypt.assert_called_once_with(plaintext=data.secret)

    create_secret_interactor._secret_saver.save.assert_awaited_once()
    create_secret_interactor._event_saver.save.assert_awaited_once()
    create_secret_interactor._db_session.commit.assert_awaited_once()

    assert result == uuid


async def test_get_secret(get_secret_interactor: GetSecretInteractor, faker: Faker) -> None:
    uuid = get_secret_interactor._uuid_generator()
    client_ip = faker.ipv4()
    client_user_agent = faker.user_agent()

    result = await get_secret_interactor(secret_id=uuid, client_ip=client_ip, client_user_agent=client_user_agent)

    get_secret_interactor._secret_delete_manager.get_by_id.assert_awaited_once_with(secret_id=uuid)
    get_secret_interactor._encription_service.decrypt.assert_called_once_with(ciphertext=b'secret')

    get_secret_interactor._secret_delete_manager.delete.assert_awaited_once()
    get_secret_interactor._event_saver.save.assert_awaited_once()
    get_secret_interactor._db_session.commit.assert_awaited_once()

    assert result == 'secret'


async def test_delete_secret(delete_secret_interactor: DeleteSecretInteractor, faker: Faker) -> None:
    uuid = delete_secret_interactor._uuid_generator()

    client_ip = faker.ipv4()
    client_user_agent = faker.user_agent()

    await delete_secret_interactor(
        secret_id=uuid, passphrase=None, client_ip=client_ip, client_user_agent=client_user_agent
    )

    delete_secret_interactor._secret_delete_manager.get_by_id.assert_awaited_once_with(secret_id=uuid)
    delete_secret_interactor._secret_delete_manager.delete.assert_awaited_once()
    delete_secret_interactor._event_saver.save.assert_awaited_once()
    delete_secret_interactor._db_session.commit.assert_awaited_once()
