"""ReviewPulse Aggregator — FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.api.routes import reviews


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    # Startup: log config, warm up connections, etc.
    print(f"[ReviewPulse] Starting {settings.app_name}")
    print(f"[ReviewPulse] Database URL: {settings.database_url[:30]}...")
    print(f"[ReviewPulse] Redis URL: {settings.redis_url}")
    yield
    # Shutdown
    print("[ReviewPulse] Shutting down.")


app = FastAPI(
    title=settings.app_name,
    description="Aggregates local business reviews, scores sentiment, and generates response drafts.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register routers
app.include_router(reviews.router, prefix="/api", tags=["reviews"])


@app.get("/health")
async def health():
    """Health-check endpoint."""
    return {"status": "ok", "service": settings.app_name}


@app.get("/docs")
async def docs():
    """Redirect to OpenAPI docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/openapi.json")
