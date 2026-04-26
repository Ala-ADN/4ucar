"""Ingestion service FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.services.ingestion_service.config import get_settings
from backend.services.ingestion_service.routers import (
    audit,
    health,
    imports,
    quarantine,
    requests,
    upload,
)
from backend.shared.exceptions import UcarError, ucar_error_handler
from backend.shared.logging import configure_logging


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.app_log_level)

    app = FastAPI(
        title="UCAR Data Ingestion Service",
        description="Entry point for all data into the UCAR KPI database.",
        version="1.0.0",
        docs_url="/docs" if settings.app_env == "local" else None,
        redoc_url=None,
    )

    # CORS — allow all in local, restrict in production
    origins = ["*"] if settings.app_env == "local" else ["https://erp.ucar.tn"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(UcarError, ucar_error_handler)  # type: ignore[arg-type]

    app.include_router(health.router, tags=["health"])
    app.include_router(upload.router, tags=["upload"])
    app.include_router(imports.router, tags=["imports"])
    app.include_router(quarantine.router, tags=["quarantine"])
    app.include_router(audit.router, tags=["audit"])
    app.include_router(requests.router, tags=["data-requests"])

    return app


app = create_app()
