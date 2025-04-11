from dataclasses import dataclass


@dataclass(slots=True)
class CreateSecretDTO:
    secret: str
    passphrase: str | None
    ttl_seconds: int | None
