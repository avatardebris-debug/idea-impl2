"""Health check endpoints."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import APIConfig
from .dependencies import get_db, get_config
from .schemas import HealthResponse

router = APIRouter()

_start_time = time.time()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(
    db: Session = Depends(get_db),
    config: APIConfig = Depends(get_config),
):
    """Comprehensive health check."""
    # Check database connectivity
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    # Count records (best-effort)
    filings_count = 0
    tickers_count = 0
    try:
        result = db.execute(text("SELECT COUNT(*) FROM filings"))
        filings_count = result.scalar() or 0
    except Exception:
        pass
    try:
        result = db.execute(text("SELECT COUNT(DISTINCT ticker) FROM filings"))
        tickers_count = result.scalar() or 0
    except Exception:
        pass

    uptime = time.time() - _start_time

    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        version=config.api_version,
        database=db_status,
        uptime_seconds=round(uptime, 2),
        tickers_count=tickers_count,
        filings_count=filings_count,
    )


@router.get("/health/live", tags=["Health"])
async def liveness_check():
    """Liveness probe — always returns 200."""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/health/ready", tags=["Health"])
async def readiness_check(
    db: Session = Depends(get_db),
):
    """Readiness probe — checks database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return {"status": "not_ready", "detail": str(e)}
