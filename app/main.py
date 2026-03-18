"""Punkt wejścia aplikacji FastAPI."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.config import settings
from app.database import configure_database, get_session_factory, init_db
from app.download_images import download_sample_images
from app.seed import seed_database


def _configure_logging() -> None:
    level = getattr(logging, settings.log_level, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        force=True,
    )


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.reload()
    _configure_logging()
    download_sample_images()
    configure_database(force=True)
    init_db()

    session = get_session_factory()()
    try:
        seed_database(session)
    finally:
        session.close()

    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Vehicle AI Agent",
        description="Klasyfikacja obrazów pojazdów + agent NL→SQL",
        version="2.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "name": "Vehicle AI Agent",
            "docs": "/docs",
            "health": "/api/health",
        }

    app.include_router(api_router)
    return app


app = create_app()
