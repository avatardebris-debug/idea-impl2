"""FastAPI application — main entry point for the SEC Importer API."""

from __future__ import annotations

from fastapi import FastAPI

from .config import APIConfig
from .routes import companies, filings, search
from .health import router as health_router
from .middleware import setup_middleware

# Load configuration
config = APIConfig()

# Create FastAPI app
app = FastAPI(
    title=config.api_title,
    version=config.api_version,
    description=config.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Setup middleware (CORS, etc.)
setup_middleware(app, config)

# Register routers
app.include_router(companies.router, prefix="/api/v1/companies", tags=["Companies"])
app.include_router(filings.router, prefix="/api/v1/filings", tags=["Filings"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(health_router, prefix="/api/v1", tags=["Health"])


@app.get("/", tags=["Root"])
async def root():
    """API root — returns API info."""
    return {
        "name": config.api_title,
        "version": config.api_version,
        "docs": "/docs",
        "health": "/api/v1/health/ready",
    }
