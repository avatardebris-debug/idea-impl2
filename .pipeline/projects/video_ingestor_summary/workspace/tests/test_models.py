"""Tests for video_ingestor.models."""

import pytest
from datetime import datetime, timezone

from video_ingestor.models import (
    JobStatus,
    TranscriptSegment,
    JobResult,
    IngestRequest,
    HealthResponse,
    JobStatusResponse,
)


class TestJobStatus:
    def test_job_status_enum_values(self):
        assert JobStatus.PENDING == "pending"
        assert JobStatus.PROCESSING == "processing"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.FAILED == "failed"

    def test_job_status_from_string(self):
        assert JobStatus("pending") == JobStatus.PENDING
        assert JobStatus("processing") == JobStatus.PROCESSING
        assert JobStatus("completed") == JobStatus.COMPLETED
        assert JobStatus("failed") == JobStatus.FAILED

    def test_job_status_invalid_value(self):
        with pytest.raises(ValueError):
            JobStatus("invalid")


class TestTranscriptSegment:
    def test_transcript_segment_minimal(self):
        seg = TranscriptSegment(text="Hello", start=0.0, end=5.0)
        assert seg.text == "Hello"
        assert seg.start == 0.0
        assert seg.end == 5.0
        assert seg.words is None

    def test_transcript_segment_with_words(self):
        words = [{"word": "Hello", "start": 0.0, "end": 1.0}]
        seg = TranscriptSegment(text="Hello", start=0.0, end=5.0, words=words)
        assert seg.words == words

    def test_transcript_segment_validation(self):
        with pytest.raises(ValueError):
            TranscriptSegment(text="")

    def test_transcript_segment_negative_start(self):
        seg = TranscriptSegment(text="Hello", start=-1.0, end=5.0)
        assert seg.start == -1.0

    def test_transcript_segment_end_before_start(self):
        seg = TranscriptSegment(text="Hello", start=5.0, end=0.0)
        assert seg.start == 5.0
        assert seg.end == 0.0


class TestJobResult:
    def test_job_result_defaults(self):
        result = JobResult(job_id="test-1", status=JobStatus.COMPLETED)
        assert result.job_id == "test-1"
        assert result.status == JobStatus.COMPLETED
        assert result.transcript == []
        assert result.full_text == ""
        assert result.metadata == {}
        assert result.error is None

    def test_job_result_with_data(self):
        segments = [
            {"text": "Hello", "start": 0.0, "end": 5.0}
        ]
        result = JobResult(
            job_id="test-1",
            status=JobStatus.COMPLETED,
            transcript=segments,
            full_text="Hello world",
            metadata={"source": "test"},
        )
        assert result.job_id == "test-1"
        assert result.status == JobStatus.COMPLETED
        assert result.transcript == segments
        assert result.full_text == "Hello world"
        assert result.metadata == {"source": "test"}

    def test_job_result_with_error(self):
        result = JobResult(
            job_id="test-1",
            status=JobStatus.FAILED,
            error="Something went wrong",
        )
        assert result.error == "Something went wrong"


class TestIngestRequest:
    def test_ingest_request_url(self):
        req = IngestRequest(url="https://example.com/video.mp4")
        assert req.url == "https://example.com/video.mp4"
        assert req.metadata == {}

    def test_ingest_request_with_metadata(self):
        req = IngestRequest(
            url="https://example.com/video.mp4",
            metadata={"title": "Test Video"},
        )
        assert req.url == "https://example.com/video.mp4"
        assert req.metadata == {"title": "Test Video"}

    def test_ingest_request_validation(self):
        with pytest.raises(ValueError):
            IngestRequest(url="")


class TestHealthResponse:
    def test_health_response_defaults(self):
        resp = HealthResponse()
        assert resp.status == "ok"
        assert resp.version == "0.1.0"
        assert resp.whisper_model == "base"
        assert resp.device == "cpu"
        assert resp.database_path == "data/chroma.db"

    def test_health_response_with_values(self):
        resp = HealthResponse(
            status="ok",
            version="1.0.0",
            whisper_model="small",
            device="cuda",
            database_path="/custom/path.db",
        )
        assert resp.status == "ok"
        assert resp.version == "1.0.0"
        assert resp.whisper_model == "small"
        assert resp.device == "cuda"
        assert resp.database_path == "/custom/path.db"


class TestJobStatusResponse:
    def test_job_status_response_defaults(self):
        resp = JobStatusResponse(
            job_id="test-1",
            status=JobStatus.PENDING,
        )
        assert resp.job_id == "test-1"
        assert resp.status == JobStatus.PENDING
        assert resp.transcript == []
        assert resp.full_text == ""
        assert resp.metadata == {}
        assert resp.error is None
        assert resp.created_at is None
        assert resp.completed_at is None

    def test_job_status_response_with_data(self):
        now = datetime.now(timezone.utc).isoformat()
        resp = JobStatusResponse(
            job_id="test-1",
            status=JobStatus.COMPLETED,
            transcript=[{"text": "Hello", "start": 0.0, "end": 5.0}],
            full_text="Hello world",
            metadata={"source": "test"},
            error=None,
            created_at=now,
            completed_at=now,
        )
        assert resp.job_id == "test-1"
        assert resp.status == JobStatus.COMPLETED
        assert len(resp.transcript) == 1
        assert resp.full_text == "Hello world"
        assert resp.metadata == {"source": "test"}
        assert resp.created_at == now
        assert resp.completed_at == now
