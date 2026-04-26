"""kpi-service FastAPI entrypoint."""

from fastapi import FastAPI

from backend.services.kpi_service.api.accreditation import router as accreditation_router
from backend.services.kpi_service.api.routes import router as kpi_router

app = FastAPI(
    title="UCAR KPI Service",
    description="KPI computation and accreditation compliance engine for UCAR institutions.",
    version="0.1.0",
)

app.include_router(kpi_router)
app.include_router(accreditation_router)
