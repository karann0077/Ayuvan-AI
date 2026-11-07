import logging

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Stage 1 WhatsApp conversation and longitudinal health-record backend.",
    )
    app.include_router(router, prefix=settings.api_prefix)
    return app


app = create_app()
