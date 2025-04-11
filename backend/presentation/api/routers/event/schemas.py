from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from backend.domain.entities.event_dm import EventType


class EventResponseSchema(BaseModel):
    id: UUID
    client_ip: str
    client_user_agent: str
    type: EventType
    created_at: datetime
    secret_id: UUID


class EventsReponseSchema(BaseModel):
    total: int
    size: int
    events: list[EventResponseSchema]
