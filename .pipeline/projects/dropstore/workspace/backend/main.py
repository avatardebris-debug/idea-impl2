"""Dropstore — FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.routers import niche_router, catalog_router, shopify_router
from backend.utils.database import Base, engine, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init DB on startup, cleanup on shutdown."""
    init_db()
    yield


app = FastAPI(
    title="Dropstore API",
    description="Dropshipping niche finder, catalog builder, and Shopify sync engine",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(niche_router.router, prefix="/api", tags=["niches"])
app.include_router(catalog_router.router, prefix="/api", tags=["catalog"])
app.include_router(shopify_router.router, prefix="/api", tags=["shopify"])


@app.get("/health")
async def health():
    return {"status": "ok"}
