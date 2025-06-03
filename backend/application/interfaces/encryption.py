from abc import abstractmethod
from typing import Protocol


class EncryptionService(Protocol):
    @abstractmethod
    def encrypt(self, plaintext: str) -> bytes: ...

    @abstractmethod
    def decrypt(self, ciphertext: bytes) -> bytes: ...
