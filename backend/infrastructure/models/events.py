from datetime import datetime
from uuid import UUID

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from backend.domain.entities.event_dm import EventType
from backend.infrastructure.models.base import Base


class Event(Base):
    __tablename__ = 'events'

    uuid: Mapped[str] = mapped_column(
        'uuid',
        sa.Uuid,
        primary_key=True,
    )
    client_ip: Mapped[str]
    client_user_agent: Mapped[str]
    type: Mapped[EventType]
    created_at: Mapped[datetime]
    secret_id: Mapped[UUID]
