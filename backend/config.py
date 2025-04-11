from dataclasses import dataclass, field
from os import environ as env


@dataclass(slots=True)
class PgConfig:
    db: str = field(default_factory=lambda: env.get('POSTGRES_DB').strip())
    host: str = field(default_factory=lambda: env.get('POSTGRES_HOST').strip())
    port: int = field(default_factory=lambda: int(env.get('POSTGRES_PORT').strip()))
    user: str = field(default_factory=lambda: env.get('POSTGRES_USER').strip())
    password: str = field(default_factory=lambda: env.get('POSTGRES_PASSWORD').strip())

    def create_connection_string(self) -> str:
        return f'postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}'


@dataclass(slots=True)
class RedisConfig:
    host: str = field(default_factory=lambda: env.get('REDIS_HOST').strip())
    port: int = field(default_factory=lambda: int(env.get('REDIS_PORT').strip()))
    db: str = field(default_factory=lambda: env.get('REDIS_DB').strip())

    def create_connection_string(self) -> str:
        return f'redis://{self.host}:{self.port}/{self.db}'


@dataclass(slots=True)
class EncryptionConfig:
    secret_key: str = field(default_factory=lambda: env.get('SECRET_KEY').strip())


@dataclass(slots=True)
class Config:
    pg: PgConfig = field(default_factory=PgConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    encryption: EncryptionConfig = field(default_factory=EncryptionConfig)
