"""Main FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routers import videos, fields, tables

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Video Management Platform",
    description="A platform for managing video content with custom fields and tables",
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
app.include_router(videos.router, prefix="/api/videos", tags=["videos"])
app.include_router(fields.router, tags=["fields"])
app.include_router(tables.router, prefix="/api/tables", tags=["tables"])
