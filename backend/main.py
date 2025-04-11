import argparse
import logging
from collections.abc import Callable, Coroutine
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from dishka import AsyncContainer, make_async_container
from dishka.integrations import fastapi as fastapi_integration
from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from psycopg.errors import UndefinedTable
from sqlalchemy.exc import ProgrammingError

from backend import ioc
from backend.application.use_cases.secret import CheckSecretExpirationInteractor
from backend.config import Config
from backend.infrastructure.services.periodic_task import periodic_task
from backend.presentation.api.exceptions_mapping import EXCEPTIONS_MAPPING
from backend.presentation.api.middlewares.no_cache import NoCacheMiddleware
from backend.presentation.api.routers import router

config = Config()


@periodic_task(delay=60)
async def check_secret_expirations_task(container: AsyncContainer):
    async with container() as container:
        try:
            interactor = await container.get(CheckSecretExpirationInteractor)
            await interactor()
        except ProgrammingError as e:
            if isinstance(e.orig, UndefinedTable):
                logging.warning("Missing table in database — please ensure migrations have been applied.")


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
    )
    logger = logging.getLogger(__name__)
    logger.info('Starting bot')


@asynccontextmanager
async def lifespan(app: FastAPI):
    await check_secret_expirations_task(app.state.dishka_container)
    yield
    await app.state.dishka_container.close()


def create_app(
        router: APIRouter,
        container: AsyncContainer,
        exc_mapping: dict[
            int | type[Exception],
            Callable[[Request, Any], Coroutine[Any, Any, Response]],
        ],
):
    app = FastAPI(
        lifespan=lifespan,
        exception_handlers=exc_mapping,
        openapi_url='/api/openapi.json',
        docs_url='/api/docs',
    )
    app.include_router(router)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    app.add_middleware(NoCacheMiddleware)

    fastapi_integration.setup_dishka(container, app)
    return app


def parse_argument() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Launch API server with custom host and port.',
    )

    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help="The host address to bind the server to. Default is '0.0.0.0'.",
    )

    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='The port number to bind the server to. Default is 8000.',
    )

    return parser.parse_args()


if __name__ == '__main__':
    launch_args = parse_argument()
    setup_logging()

    container = make_async_container(
        ioc.ApplicationProvider(),
        ioc.InfrastructureProvider(),
        context={Config: config},
    )

    uvicorn.run(
        create_app(
            container=container,
            router=router,
            exc_mapping=EXCEPTIONS_MAPPING,
        ),
        host=launch_args.host,
        port=launch_args.port,
        lifespan='on',
    )
