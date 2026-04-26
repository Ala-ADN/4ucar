"""kpi-service FastAPI entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from backend.services.kpi_service.api.routes import router as kpi_router

app = FastAPI(title="ucar-kpi-service")
app.include_router(kpi_router)


@app.get("/healthz", tags=["meta"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
