from abc import abstractmethod
from typing import Protocol


class BcryptHasher(Protocol):
    @abstractmethod
    def hash(self, raw_data: str) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def verify(self, raw_data: bytes, hashed_data: bytes) -> bool:
        raise NotImplementedError
