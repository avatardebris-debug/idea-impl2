"""Academic Thesis Writer - Main entry point.

FastAPI application that exposes the thesis writer API.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .api.routes import router as api_router
from .config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    logger.info("Starting Academic Thesis Writer v%s", settings.app_version)
    yield
    logger.info("Shutting down Academic Thesis Writer")


app = FastAPI(
    title="Academic Thesis Writer",
    description="AI-powered thesis writing assistant with citation management.",
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.app_version}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
