from collections.abc import Collection

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from backend.application import interfaces
from backend.domain.entities.event_dm import EventDM


class EventRepository(
    interfaces.EventReader,
    interfaces.EventSaver,
):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> Collection[EventDM]:
        query = text('SELECT uuid, client_ip, client_user_agent, type, created_at, secret_id FROM events')
        result = await self._session.execute(statement=query)
        rows = result.fetchall()

        return [
            EventDM(
                uuid=row.uuid,
                client_ip=row.client_ip,
                client_user_agent=row.client_user_agent,
                type=row.type,
                created_at=row.created_at,
                secret_id=row.secret_id,
            )
            for row in rows
        ]

    async def save(self, event: EventDM) -> None:
        stmt = text(
            'INSERT INTO events(uuid, client_ip, client_user_agent, type, created_at, secret_id) '
            'VALUES '
            '(:uuid, :client_ip, :client_user_agent, :type, :created_at, :secret_id)',
        )

        await self._session.execute(
            statement=stmt,
            params={
                'uuid': event.uuid,
                'client_ip': event.client_ip,
                'client_user_agent': event.client_user_agent,
                'type': event.type,
                'created_at': event.created_at,
                'secret_id': event.secret_id,
            },
        )
