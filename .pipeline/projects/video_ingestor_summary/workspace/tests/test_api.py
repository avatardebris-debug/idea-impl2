"""Tests for video_ingestor.api."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from video_ingestor.api import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_storage():
    """Create a mock Storage instance."""
    storage = MagicMock()
    storage.get_job.return_value = {
        "job_id": "test-job-id",
        "status": "completed",
        "transcript": [
            {"text": "Hello world", "start": 0.0, "end": 2.0},
        ],
        "full_text": "Hello world",
        "metadata": {"source_url": "http://example.com/video.mp4"},
        "error": None,
        "created_at": "2024-01-01T00:00:00+00:00",
        "completed_at": "2024-01-01T00:01:00+00:00",
    }
    storage.list_jobs.return_value = [
        {
            "job_id": "test-job-id",
            "status": "completed",
            "video_path": "/tmp/test.mp4",
            "created_at": "2024-01-01T00:00:00+00:00",
            "completed_at": "2024-01-01T00:01:00+00:00",
        }
    ]
    storage.create_job.return_value = "test-job-id"
    storage.update_job_status.return_value = None
    storage.update_job_transcript.return_value = None
    storage.delete_job.return_value = True
    return storage


@pytest.fixture
def mock_pipeline():
    """Create a mock IngestionPipeline instance."""
    pipeline = MagicMock()
    pipeline.ingest_from_url.return_value = "test-job-id"
    pipeline.ingest_from_file.return_value = "test-job-id"
    return pipeline


class TestAPI:
    def test_get_job(self, client, mock_storage):
        """Test the GET /jobs/{job_id} endpoint."""
        import video_ingestor.api as api_module
        with patch.object(api_module, "storage", mock_storage):
            response = client.get("/jobs/test-job-id")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-id"
        assert data["status"] == "completed"
        assert data["full_text"] == "Hello world"

    def test_get_job_not_found(self, client, mock_storage):
        """Test the GET /jobs/{job_id} endpoint when job is not found."""
        import video_ingestor.api as api_module
        mock_storage.get_job.return_value = None
        with patch.object(api_module, "storage", mock_storage):
            response = client.get("/jobs/nonexistent-job")
        assert response.status_code == 404

    def test_list_jobs(self, client, mock_storage):
        """Test the GET /jobs endpoint."""
        import video_ingestor.api as api_module
        with patch.object(api_module, "storage", mock_storage):
            response = client.get("/jobs")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["job_id"] == "test-job-id"

    def test_list_jobs_with_params(self, client, mock_storage):
        """Test the GET /jobs endpoint with limit and offset."""
        import video_ingestor.api as api_module
        with patch.object(api_module, "storage", mock_storage):
            response = client.get("/jobs?limit=10&offset=5")
        assert response.status_code == 200
        mock_storage.list_jobs.assert_called_with(limit=10, offset=5)

    def test_ingest_from_url(self, client, mock_storage, mock_pipeline):
        """Test the POST /ingest/url endpoint."""
        import video_ingestor.api as api_module
        with patch.object(api_module, "storage", mock_storage):
            with patch.object(api_module, "pipeline", mock_pipeline):
                response = client.post("/ingest/url", json={"url": "http://example.com/video.mp4"})
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-id"
        assert data["status"] == "processing"
        mock_pipeline.ingest_from_url.assert_called_once_with("http://example.com/video.mp4")

    def test_ingest_from_file(self, client, mock_storage, mock_pipeline):
        """Test the POST /ingest/upload endpoint."""
        import video_ingestor.api as api_module
        with patch.object(api_module, "storage", mock_storage):
            with patch.object(api_module, "pipeline", mock_pipeline):
                with patch.object(api_module, "settings") as mock_settings:
                    mock_settings.TEMP_DIR = "/tmp"
                    with patch.object(api_module.uuid, "uuid4", return_value=MagicMock(hex="1234")):
                        response = client.post(
                            "/ingest/upload",
                            files={"file": ("test.mp4", b"fake video content", "video/mp4")},
                        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "test-job-id"
        assert data["status"] == "processing"
        mock_pipeline.ingest_from_file.assert_called_once()

    def test_delete_job(self, client, mock_storage):
        """Test the DELETE /jobs/{job_id} endpoint."""
        import video_ingestor.api as api_module
        with patch.object(api_module, "storage", mock_storage):
            response = client.delete("/jobs/test-job-id")
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True
        assert data["job_id"] == "test-job-id"
        mock_storage.delete_job.assert_called_once_with("test-job-id")

    def test_delete_job_not_found(self, client, mock_storage):
        """Test the DELETE /jobs/{job_id} endpoint when job is not found."""
        import video_ingestor.api as api_module
        mock_storage.delete_job.return_value = False
        with patch.object(api_module, "storage", mock_storage):
            response = client.delete("/jobs/nonexistent-job")
        assert response.status_code == 404

    def test_health(self, client):
        """Test the GET /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "whisper_model" in data
        assert "device" in data
        assert "database_path" in data
