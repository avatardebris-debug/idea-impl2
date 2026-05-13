"""FastAPI application for the video ingestor."""

from __future__ import annotations

import os
import uuid
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from .config import settings
from .ingestion import IngestionPipeline, IngestionError
from .models import HealthResponse, JobStatusResponse, IngestRequest
from .storage import Storage

# Create global instances
storage = Storage()
pipeline = IngestionPipeline(storage)

app = FastAPI(
    title="Video Ingestor API",
    description="Ingest videos from URLs, extract audio, and transcribe with Whisper.",
    version="0.1.0",
)


@app.on_event("startup")
async def startup() -> None:
    """Initialize database on startup."""
    storage.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    """Close database on shutdown."""
    storage.close()


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        whisper_model=settings.WHISPER_MODEL,
        device=settings.WHISPER_DEVICE,
        database_path=settings.DATABASE_PATH,
    )


@app.post("/ingest/url", response_model=dict)
async def ingest_from_url(req: IngestRequest) -> dict:
    """Start ingestion from a video URL. Returns job_id immediately."""
    try:
        job_id = pipeline.ingest_from_url(req.url)
        return {"job_id": job_id, "status": "processing"}
    except IngestionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@app.post("/ingest/upload", response_model=dict)
async def ingest_from_upload(file: UploadFile = File(...)) -> dict:
    """Start ingestion from an uploaded video file. Returns job_id immediately."""
    # Save uploaded file
    os.makedirs(settings.TEMP_DIR, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else "mp4"
    video_path = os.path.join(settings.TEMP_DIR, f"{uuid.uuid4()}.{ext}")
    with open(video_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        job_id = pipeline.ingest_from_file(video_path)
        return {"job_id": job_id, "status": "processing"}
    except IngestionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Get the status and result of a job."""
    job = storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        transcript=job["transcript"],
        full_text=job["full_text"],
        metadata=job["metadata"],
        error=job["error"],
        created_at=job["created_at"],
        completed_at=job["completed_at"],
    )


@app.get("/jobs", response_model=list[dict])
async def list_jobs(limit: int = 50, offset: int = 0) -> list[dict]:
    """List recent jobs."""
    return storage.list_jobs(limit=limit, offset=offset)


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str) -> dict:
    """Delete a job and its files."""
    deleted = storage.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"deleted": True, "job_id": job_id}
