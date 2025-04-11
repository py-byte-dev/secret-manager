from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(slots=True)
class SecretDM:
    uuid: UUID
    secret: bytes
    passphrase: bytes | None
    created_at: datetime
    expired_at: datetime | None
    is_deleted: bool

    @property
    def is_secret_expired(self) -> bool:
        if self.expired_at is None:
            return False
        return datetime.now() >= self.expired_at
