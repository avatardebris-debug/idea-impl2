"""Health check endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..dependencies import get_db
from .config import APIConfig
from .schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(
    db: Session = Depends(get_db),
    config: APIConfig = Depends(),
):
    """Health check endpoint.

    Returns the overall service status and database connectivity.
    """
    db_status = "disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    status_code = status.HTTP_200_OK if db_status == "connected" else status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        version=config.api_version,
    )


@router.get("/health/ready", response_model=HealthResponse, tags=["Health"])
async def readiness_check(
    db: Session = Depends(get_db),
    config: APIConfig = Depends(),
):
    """Readiness check — is the service ready to accept traffic?"""
    db_status = "disconnected"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    ready = db_status == "connected"

    return HealthResponse(
        status="ready" if ready else "not_ready",
        database=db_status,
        version=config.api_version,
    )


@router.get("/health/live", tags=["Health"])
async def liveness_check():
    """Liveness check — is the process alive?"""
    return {"status": "ok"}
