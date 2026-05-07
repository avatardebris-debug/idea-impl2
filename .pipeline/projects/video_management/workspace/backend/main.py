"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import tables_router, fields_router, videos_router

app = FastAPI(
    title="Video Management Platform",
    description="API for managing video content with custom fields and tables",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tables_router)
app.include_router(fields_router)
app.include_router(videos_router)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
