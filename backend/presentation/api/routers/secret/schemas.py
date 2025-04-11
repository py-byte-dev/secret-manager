from uuid import UUID

from pydantic import BaseModel

from backend.application.dto.secret import CreateSecretDTO


class CreateSecretSchema(BaseModel):
    secret: str
    passphrase: str | None = None
    ttl_seconds: int | None = None

    def to_dto(self) -> CreateSecretDTO:
        return CreateSecretDTO(
            secret=self.secret,
            passphrase=self.passphrase,
            ttl_seconds=self.ttl_seconds,
        )


class CreateSecretResponseSchema(BaseModel):
    secret_key: UUID


class SecretResponseSchema(BaseModel):
    secret: str
