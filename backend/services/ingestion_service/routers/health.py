"""GET /health — service health check.

Returns DB connectivity, Redis connectivity, and PaddleOCR model status.
Does not require authentication — used by load balancers and monitoring.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    from backend.services.ingestion_service.config import get_settings
    from backend.shared.logging import get_logger

    logger = get_logger(__name__)
    settings = get_settings()
    results: dict[str, str] = {}

    # ── Database ─────────────────────────────────────────────────────────────
    # Use the same `database_url` as the rest of the service so a single
    # env var (DATABASE_URL) controls connectivity end-to-end.
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        engine = create_async_engine(settings.database_url, pool_size=1)
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        await engine.dispose()
        results["database"] = "ok"
    except Exception as exc:
        results["database"] = f"error: {exc}"

    # ── Redis ─────────────────────────────────────────────────────────────────
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        results["redis"] = "ok"
    except Exception as exc:
        results["redis"] = f"error: {exc}"

    # ── PaddleOCR ─────────────────────────────────────────────────────────────
    try:
        import importlib
        importlib.import_module("paddleocr")
        results["paddleocr"] = "available"
    except ImportError:
        results["paddleocr"] = "not_installed"

    overall = "ok" if all(v in ("ok", "available") for v in results.values()) else "degraded"
    return {"status": overall, "checks": results}
