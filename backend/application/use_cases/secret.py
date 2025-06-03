import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from functools import partial
from typing import Protocol
from uuid import UUID

from backend.application import exceptions as app_exceptions, interfaces
from backend.application.dto.secret import CreateSecretDTO
from backend.domain.entities.event_dm import EventDM, EventType
from backend.domain.entities.secret_dm import SecretDM


class CreateSecretInteractor:
    def __init__(
        self,
        thread_pool: ThreadPoolExecutor,
        secret_saver: interfaces.SecretSaver,
        event_saver: interfaces.EventSaver,
        db_session: interfaces.DBSession,
        encription_service: interfaces.EncryptionService,
        hasher: interfaces.BcryptHasher,
        current_dt: interfaces.GenerateCurrentDT,
        uuid_generator: interfaces.UUIDGenerator,
    ):
        self._thread_pool = thread_pool
        self._secret_saver = secret_saver
        self._event_saver = event_saver
        self._db_session = db_session
        self._encription_service = encription_service
        self._hasher = hasher
        self._current_dt = current_dt
        self._uuid_generator = uuid_generator

    async def __call__(self, data: CreateSecretDTO, client_ip: str, client_user_agent: str) -> UUID:
        loop = asyncio.get_running_loop()
        hashed_passphrase = (
            await loop.run_in_executor(self._thread_pool, partial(self._hasher.hash, raw_data=data.passphrase))
            if data.passphrase
            else None
        )

        encrypted_secret = await loop.run_in_executor(
            self._thread_pool,
            partial(self._encription_service.encrypt, plaintext=data.secret),
        )

        current_dt = self._current_dt()
        expired_at = current_dt + timedelta(seconds=data.ttl_seconds) if data.ttl_seconds else None

        secret_dm = SecretDM(
            uuid=self._uuid_generator(),
            secret=encrypted_secret,
            passphrase=hashed_passphrase,
            created_at=current_dt,
            expired_at=expired_at,
            is_deleted=False,
        )

        event_dm = EventDM(
            uuid=self._uuid_generator(),
            client_ip=client_ip,
            client_user_agent=client_user_agent,
            type=EventType.CREATE,
            created_at=current_dt,
            secret_id=secret_dm.uuid,
        )

        await self._secret_saver.save(secret=secret_dm)
        await self._event_saver.save(event=event_dm)
        await self._db_session.commit()

        return secret_dm.uuid


class SecretDeleteManager(interfaces.SecretReader, interfaces.SecretDeleter, Protocol): ...


class GetSecretInteractor:
    def __init__(
        self,
        thread_pool: ThreadPoolExecutor,
        secret_delete_manager: SecretDeleteManager,
        event_saver: interfaces.EventSaver,
        db_session: interfaces.DBSession,
        encription_service: interfaces.EncryptionService,
        current_dt: interfaces.GenerateCurrentDT,
        uuid_generator: interfaces.UUIDGenerator,
    ):
        self._thread_pool = thread_pool
        self._secret_delete_manager = secret_delete_manager
        self._event_saver = event_saver
        self._db_session = db_session
        self._encription_service = encription_service
        self._current_dt = current_dt
        self._uuid_generator = uuid_generator

    async def __call__(self, secret_id: UUID, client_ip: str, client_user_agent: str) -> str:
        secret_dm = await self._secret_delete_manager.get_by_id(secret_id=secret_id)

        loop = asyncio.get_running_loop()
        decrypted_secret = await loop.run_in_executor(
            self._thread_pool,
            partial(self._encription_service.decrypt, ciphertext=secret_dm.secret),
        )

        secret_dm.is_deleted = True
        event_dm = EventDM(
            uuid=self._uuid_generator(),
            client_ip=client_ip,
            client_user_agent=client_user_agent,
            type=EventType.READ,
            created_at=self._current_dt(),
            secret_id=secret_dm.uuid,
        )

        await self._secret_delete_manager.delete(secret=secret_dm)
        await self._event_saver.save(event=event_dm)
        await self._db_session.commit()

        return decrypted_secret.decode()


class DeleteSecretInteractor:
    def __init__(
        self,
        thread_pool: ThreadPoolExecutor,
        secret_delete_manager: SecretDeleteManager,
        event_saver: interfaces.EventSaver,
        db_session: interfaces.DBSession,
        hasher: interfaces.BcryptHasher,
        current_dt: interfaces.GenerateCurrentDT,
        uuid_generator: interfaces.UUIDGenerator,
    ):
        self._thread_pool = thread_pool
        self._secret_delete_manager = secret_delete_manager
        self._event_saver = event_saver
        self._db_session = db_session
        self._hasher = hasher
        self._current_dt = current_dt
        self._uuid_generator = uuid_generator

    async def __call__(self, secret_id: UUID, passphrase: str | None, client_ip: str, client_user_agent: str) -> None:
        secret_dm = await self._secret_delete_manager.get_by_id(secret_id=secret_id)

        if secret_dm.passphrase:
            loop = asyncio.get_running_loop()
            is_correct_passphrase = await loop.run_in_executor(
                self._thread_pool,
                partial(self._hasher.verify, raw_data=passphrase.encode(), hashed_data=secret_dm.passphrase),
            )
            if not is_correct_passphrase:
                raise app_exceptions.IncorrectPassphraseError

        secret_dm.is_deleted = True
        event_dm = EventDM(
            uuid=self._uuid_generator(),
            client_ip=client_ip,
            client_user_agent=client_user_agent,
            type=EventType.DELETE,
            created_at=self._current_dt(),
            secret_id=secret_dm.uuid,
        )

        await self._secret_delete_manager.delete(secret=secret_dm)
        await self._event_saver.save(event=event_dm)
        await self._db_session.commit()


class CheckSecretExpirationInteractor:
    def __init__(
        self,
        secret_delete_manager: SecretDeleteManager,
        session: interfaces.DBSession,
    ):
        self._secret_delete_manager = secret_delete_manager
        self._session = session

    async def __call__(self) -> None:
        secrets = await self._secret_delete_manager.get_all_expirable()

        for secret in secrets:
            if secret.is_secret_expired:
                secret.is_deleted = True
                await self._secret_delete_manager.delete(secret=secret)

        await self._session.commit()
