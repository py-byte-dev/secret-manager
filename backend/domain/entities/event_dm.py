from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class EventType(StrEnum):
    READ = 'READ'
    CREATE = 'CREATE'
    DELETE = 'DELETE'


@dataclass(slots=True)
class EventDM:
    uuid: UUID
    client_ip: str
    client_user_agent: str
    type: EventType
    created_at: datetime
    secret_id: UUID
