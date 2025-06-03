from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import TIMESTAMP
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import Mapped, mapped_column

from backend.infrastructure.models.base import Base


class Secret(Base):
    __tablename__ = 'secrets'
    uuid: Mapped[str] = mapped_column(
        'uuid',
        sa.Uuid,
        primary_key=True,
    )
    secret: Mapped[bytes]
    passphrase: Mapped[bytes] = mapped_column(BYTEA, nullable=True)
    created_at: Mapped[datetime]
    expired_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    is_deleted: Mapped[bool]
