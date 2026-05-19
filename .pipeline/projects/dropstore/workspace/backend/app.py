"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.utils.database import init_db, seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    await seed_database()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="DropStore API",
    description="Automated dropshipping store builder",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers
from backend.routers import niche_router, catalog_router, shopify_router

app.include_router(niche_router.router, prefix="/api/v1")
app.include_router(catalog_router.router, prefix="/api/v1")
app.include_router(shopify_router.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}
