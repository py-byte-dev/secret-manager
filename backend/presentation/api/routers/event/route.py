from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from backend.application.use_cases.events import GetEventsInteractor
from backend.presentation.api.routers.event.schemas import EventResponseSchema, EventsReponseSchema

router = APIRouter(
    prefix='/event',
    route_class=DishkaRoute,
    tags=['event'],
)


@router.get('', response_model=EventsReponseSchema)
async def get_events(
    interactor: FromDishka[GetEventsInteractor],
    page: int,
    page_size: int,
):
    paginated_data = await interactor(page=page, page_size=page_size)

    return EventsReponseSchema(
        total=paginated_data.total,
        size=paginated_data.size,
        events=[
            EventResponseSchema(
                id=event.uuid,
                client_ip=event.client_ip,
                client_user_agent=event.client_user_agent,
                type=event.type,
                created_at=event.created_at,
                secret_id=event.secret_id,
            )
            for event in paginated_data.items
        ],
    )
