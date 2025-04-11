from backend.application import interfaces
from backend.application.services.pagination import PaginationService
from backend.domain.entities.event_dm import EventDM
from backend.domain.entities.pagination import Pagination


class GetEventsInteractor:
    def __init__(
        self,
        event_reader: interfaces.EventReader,
        pagination_service: PaginationService,
    ):
        self._event_reader = event_reader
        self._pagination_service = pagination_service

    async def __call__(self, page: int, page_size: int) -> Pagination[EventDM]:
        events = await self._event_reader.get_all()
        return self._pagination_service.create_page(page=page, page_size=page_size, items=events)
