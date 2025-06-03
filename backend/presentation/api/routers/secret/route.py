from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Request

from backend.application.use_cases.secret import CreateSecretInteractor, DeleteSecretInteractor, GetSecretInteractor
from backend.presentation.api.routers.secret.schemas import (
    CreateSecretResponseSchema,
    CreateSecretSchema,
    SecretResponseSchema,
)

router = APIRouter(
    prefix='/secret',
    route_class=DishkaRoute,
    tags=['secret'],
)


@router.get('/{secret_key}', response_model=SecretResponseSchema)
async def get_secret(
    request: Request,
    interactor: FromDishka[GetSecretInteractor],
    secret_key: str,
):
    secret = await interactor(
        secret_id=secret_key, client_ip=request.client.host, client_user_agent=request.headers.get('user-agent')
    )
    return SecretResponseSchema(
        secret=secret,
    )


@router.post('', response_model=CreateSecretResponseSchema)
async def create_secret(
    request: Request,
    interactor: FromDishka[CreateSecretInteractor],
    data: CreateSecretSchema,
):
    print(data.passphrase)
    secret_id = await interactor(
        data=data.to_dto(), client_ip=request.client.host, client_user_agent=request.headers.get('user-agent')
    )

    return CreateSecretResponseSchema(secret_key=secret_id)


@router.delete('/{secret_key}')
async def delete_secret(
    request: Request,
    interactor: FromDishka[DeleteSecretInteractor],
    secret_key: str,
    passphrase: str | None = None,
):
    await interactor(
        secret_id=secret_key,
        passphrase=passphrase,
        client_ip=request.client.host,
        client_user_agent=request.headers.get('user-agent'),
    )
