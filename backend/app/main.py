from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import app.models  # noqa: F401
from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.session import configure_database
from app.services.export_service import ExportService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_database(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        settings.resolved_upload_dir.mkdir(parents=True, exist_ok=True)
        settings.resolved_export_dir.mkdir(parents=True, exist_ok=True)
        export_service = ExportService(session_note_service=None)
        if not export_service.is_pandoc_available(settings):
            logger.warning(
                "Pandoc is not available. Export requests will fail until `%s` is installed or PANDOC_BINARY is updated.",
                settings.pandoc_binary,
            )
        yield

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.include_router(api_router)

    @app.get("/health")
    async def health() -> dict[str, str | bool]:
        export_service = ExportService(session_note_service=None)
        return {
            "status": "ok",
            "app_name": settings.app_name,
            "pandoc_available": export_service.is_pandoc_available(settings),
        }

    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.code, "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "validation_error",
                "message": "Request validation failed.",
                "details": exc.errors(),
            },
        )

    return app


app = create_app()
