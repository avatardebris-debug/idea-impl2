"""Tests for video_ingestor.storage."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from video_ingestor.storage import Storage


@pytest.fixture
def db_path(tmp_path):
    """Create a temporary database path."""
    return str(tmp_path / "test.db")


@pytest.fixture
def storage(db_path):
    """Create a storage instance with temporary database."""
    s = Storage(db_path)
    s.connect()
    yield s
    s.close()


class TestStorage:
    def test_connect_creates_database(self, db_path):
        """Test that connect creates the database file."""
        s = Storage(db_path)
        assert not os.path.exists(db_path)
        s.connect()
        assert os.path.exists(db_path)
        s.close()

    def test_create_job(self, storage):
        """Test creating a new job."""
        job_id = storage.create_job(
            video_path="http://example.com/video.mp4",
            metadata={"source": "url"}
        )
        assert job_id is not None
        assert len(job_id) == 36  # UUID format

        # Verify job exists in database
        job = storage.get_job(job_id)
        assert job is not None
        assert job["status"] == "pending"
        assert job["video_path"] == "http://example.com/video.mp4"
        assert job["metadata"] == {"source": "url"}

    def test_create_job_with_file_path(self, storage):
        """Test creating a job with a file path."""
        job_id = storage.create_job(
            video_path="/path/to/video.mp4",
            metadata={"source": "file"}
        )
        job = storage.get_job(job_id)
        assert job["video_path"] == "/path/to/video.mp4"
        assert job["metadata"] == {"source": "file"}

    def test_update_job_status(self, storage):
        """Test updating job status."""
        job_id = storage.create_job(video_path="test.mp4")
        
        # Update to processing
        storage.update_job_status(job_id, "processing")
        job = storage.get_job(job_id)
        assert job["status"] == "processing"

        # Update to completed
        storage.update_job_status(job_id, "completed")
        job = storage.get_job(job_id)
        assert job["status"] == "completed"

        # Update to failed
        storage.update_job_status(job_id, "failed", error="Test error")
        job = storage.get_job(job_id)
        assert job["status"] == "failed"
        assert job["error"] == "Test error"

    def test_update_job_transcript(self, storage):
        """Test updating job transcript."""
        job_id = storage.create_job(video_path="test.mp4")
        
        storage.update_job_transcript(
            job_id,
            transcript_json='[{"text": "Hello", "start": 0.0, "end": 1.0}]',
            full_text="Hello"
        )
        
        job = storage.get_job(job_id)
        assert job["transcript"] == '[{"text": "Hello", "start": 0.0, "end": 1.0}]'
        assert job["full_text"] == "Hello"

    def test_get_job_not_found(self, storage):
        """Test getting a non-existent job."""
        job = storage.get_job("non-existent-id")
        assert job is None

    def test_list_jobs(self, storage):
        """Test listing jobs."""
        # Create multiple jobs
        job_ids = []
        for i in range(5):
            job_id = storage.create_job(video_path=f"test{i}.mp4")
            job_ids.append(job_id)
        
        jobs = storage.list_jobs()
        assert len(jobs) == 5
        
        # Verify jobs are returned in reverse chronological order
        assert jobs[0]["created_at"] >= jobs[-1]["created_at"]

    def test_list_jobs_with_limit(self, storage):
        """Test listing jobs with limit."""
        # Create multiple jobs
        for i in range(10):
            storage.create_job(video_path=f"test{i}.mp4")
        
        jobs = storage.list_jobs(limit=5)
        assert len(jobs) == 5

    def test_list_jobs_with_offset(self, storage):
        """Test listing jobs with offset."""
        # Create multiple jobs
        job_ids = []
        for i in range(5):
            job_id = storage.create_job(video_path=f"test{i}.mp4")
            job_ids.append(job_id)
        
        # Get first 2
        jobs1 = storage.list_jobs(limit=2, offset=0)
        assert len(jobs1) == 2
        
        # Get next 2
        jobs2 = storage.list_jobs(limit=2, offset=2)
        assert len(jobs2) == 2
        
        # Verify they are different jobs
        assert jobs1[0]["job_id"] != jobs2[0]["job_id"]

    def test_delete_job(self, storage):
        """Test deleting a job."""
        job_id = storage.create_job(video_path="test.mp4")
        
        # Verify job exists
        assert storage.get_job(job_id) is not None
        
        # Delete job
        deleted = storage.delete_job(job_id)
        assert deleted is True
        
        # Verify job is gone
        assert storage.get_job(job_id) is None

    def test_delete_nonexistent_job(self, storage):
        """Test deleting a non-existent job."""
        deleted = storage.delete_job("non-existent-id")
        assert deleted is False

    def test_close(self, storage):
        """Test closing the database connection."""
        storage.close()
        # Should not raise an error

    def test_multiple_jobs_different_metadata(self, storage):
        """Test creating jobs with different metadata."""
        job1_id = storage.create_job(
            video_path="test1.mp4",
            metadata={"source": "url", "url": "http://example.com/1"}
        )
        job2_id = storage.create_job(
            video_path="test2.mp4",
            metadata={"source": "file", "path": "/local/video.mp4"}
        )
        
        job1 = storage.get_job(job1_id)
        job2 = storage.get_job(job2_id)
        
        assert job1["metadata"]["url"] == "http://example.com/1"
        assert job2["metadata"]["path"] == "/local/video.mp4"

    def test_job_timestamps(self, storage):
        """Test that job timestamps are set correctly."""
        job_id = storage.create_job(video_path="test.mp4")
        job = storage.get_job(job_id)
        
        assert job["created_at"] is not None
        assert job["completed_at"] is None  # Not completed yet
        
        # Complete the job
        storage.update_job_status(job_id, "completed")
        job = storage.get_job(job_id)
        
        assert job["completed_at"] is not None
