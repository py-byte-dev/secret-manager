from datetime import UTC, datetime
from uuid import uuid4

from dishka import Provider, Scope, from_context, provide

from backend.application import interfaces
from backend.application.services.pagination import PaginationService
from backend.application.use_cases.events import GetEventsInteractor
from backend.application.use_cases.secret import (
    CheckSecretExpirationInteractor,
    CreateSecretInteractor,
    DeleteSecretInteractor,
    GetSecretInteractor,
)


class ApplicationProvider(Provider):
    @provide(scope=Scope.APP)
    def get_uuid_generator(self) -> interfaces.UUIDGenerator:
        return uuid4

    @provide(scope=Scope.APP)
    def get_current_dt(self) -> interfaces.GenerateCurrentDT:
        return lambda: datetime.now(UTC)

    create_secret_interactor = provide(CreateSecretInteractor, scope=Scope.REQUEST)
    get_secret_interactor = provide(GetSecretInteractor, scope=Scope.REQUEST)
    delete_secret_interactor = provide(DeleteSecretInteractor, scope=Scope.REQUEST)
    check_secret_expiration_interactor = provide(CheckSecretExpirationInteractor, scope=Scope.REQUEST)

    get_events_interactor = provide(GetEventsInteractor, scope=Scope.REQUEST)

    pagination_service = provide(PaginationService, scope=Scope.REQUEST)
