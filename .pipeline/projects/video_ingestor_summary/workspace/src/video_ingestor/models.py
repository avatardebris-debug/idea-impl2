"""Pydantic models for the video ingestor API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Status of an ingest job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscriptSegment(BaseModel):
    """A single segment of transcribed text with timestamps."""
    text: str
    start: float
    end: float
    words: Optional[list[dict]] = None  # word-level timing if available


class JobResult(BaseModel):
    """Result of a completed transcription job."""
    job_id: str
    status: JobStatus
    transcript: list[TranscriptSegment] = []
    full_text: str = ""
    metadata: dict = {}
    error: Optional[str] = None


class IngestRequest(BaseModel):
    """Request body for URL-based ingestion."""
    url: str = Field(..., description="URL of the video to ingest")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    whisper_model: str
    device: str
    database_path: str


class JobStatusResponse(BaseModel):
    """Response for GET /jobs/{job_id}."""
    job_id: str
    status: JobStatus
    transcript: list[TranscriptSegment] = []
    full_text: str = ""
    metadata: dict = {}
    error: Optional[str] = None
    created_at: Optional[str] = None
    completed_at: Optional[str] = None
