"""Integration test for the full video ingestor pipeline."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from video_ingestor.api import app, storage, pipeline
from video_ingestor.storage import Storage
from video_ingestor.ingestion import IngestionPipeline


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_integration.db")


@pytest.fixture
def test_storage(db_path):
    s = Storage(db_path)
    s.connect()
    yield s
    s.close()


@pytest.fixture
def test_pipeline(test_storage):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [
            {"text": "Hello world", "start": 0.0, "end": 2.0},
        ],
        "text": "Hello world",
    }
    return IngestionPipeline(test_storage, model=mock_model)


@pytest.fixture
def client(test_storage, test_pipeline):
    import video_ingestor.api as api_module
    api_module.storage = test_storage
    api_module.pipeline = test_pipeline
    return TestClient(app)


class TestIntegrationPipeline:
    """End-to-end integration test: ingest -> extract -> transcribe -> store -> retrieve."""

    def test_full_pipeline_from_url(self, client, test_storage, test_pipeline):
        """Simulate the full pipeline: ingest from URL, transcribe, retrieve."""
        with patch.object(test_pipeline, "ingest_from_url", return_value="test-job-id"):
            resp = client.post("/ingest/url", json={"url": "http://example.com/video.mp4"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["job_id"] == "test-job-id"
            assert data["status"] == "processing"

    def test_full_pipeline_from_upload(self, client, test_storage, test_pipeline, tmp_path):
        """Simulate the full pipeline: upload file, transcribe, retrieve."""
        # Create a dummy video file
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"\x00" * 100)

        with patch("video_ingestor.api.pipeline.ingest_from_file", return_value="test-job-id-upload"):
            with open(video_file, "rb") as f:
                resp = client.post(
                    "/ingest/upload",
                    files={"file": ("test.mp4", f, "video/mp4")},
                )
            assert resp.status_code == 200
            data = resp.json()
            assert data["job_id"] == "test-job-id-upload"
            assert data["status"] == "processing"

    def test_retrieve_completed_job(self, client, test_storage):
        """Store a completed job and verify retrieval."""
        job_id = test_storage.create_job("/tmp/test.mp4", {"source": "url"})
        test_storage.update_job_status(job_id, "processing")
        test_storage.update_job_transcript(
            job_id,
            '[{"text": "Hello world", "start": 0.0, "end": 2.0}]',
            "Hello world",
        )
        test_storage.update_job_status(job_id, "completed")

        resp = client.get(f"/jobs/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == job_id
        assert data["status"] == "completed"
        assert data["full_text"] == "Hello world"

    def test_retrieve_failed_job(self, client, test_storage):
        """Store a failed job and verify retrieval."""
        job_id = test_storage.create_job("/tmp/test.mp4", {"source": "url"})
        test_storage.update_job_status(job_id, "failed", error="network error")

        resp = client.get(f"/jobs/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == job_id
        assert data["status"] == "failed"
        assert data["error"] == "network error"

    def test_list_and_delete_jobs(self, client, test_storage):
        """Create multiple jobs, list them, then delete one."""
        job_ids = []
        for i in range(3):
            job_id = test_storage.create_job(f"/tmp/test{i}.mp4", {})
            job_ids.append(job_id)

        # List all
        resp = client.get("/jobs")
        assert resp.status_code == 200
        jobs = resp.json()
        assert len(jobs) == 3

        # Delete one
        resp = client.delete(f"/jobs/{job_ids[0]}")
        assert resp.status_code == 200
        assert resp.json()["deleted"] is True

        # Verify deletion
        resp = client.get("/jobs")
        assert len(resp.json()) == 2

        # Verify the deleted job is gone
        resp = client.get(f"/jobs/{job_ids[0]}")
        assert resp.status_code == 404
