from abc import abstractmethod
from collections.abc import Collection
from typing import Protocol
from uuid import UUID

from backend.domain.entities.secret_dm import SecretDM


class SecretReader(Protocol):
    @abstractmethod
    async def get_by_id(self, secret_id: UUID) -> SecretDM: ...

    @abstractmethod
    async def get_all_expirable(self) -> Collection[SecretDM]: ...


class SecretSaver(Protocol):
    @abstractmethod
    async def save(self, secret: SecretDM) -> None: ...


class SecretDeleter(Protocol):
    @abstractmethod
    async def delete(self, secret: SecretDM) -> None: ...
