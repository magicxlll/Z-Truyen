"""Healthcheck and application version routes."""

from datetime import datetime, timezone
from fastapi import APIRouter
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/healthz")
async def healthcheck() -> dict[str, str]:
    """Basic health check endpoint returning server status."""
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/version")
async def version_info() -> dict[str, str]:
    """Version metadata endpoint."""
    return {
        "app": "z-truyen-backend",
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
