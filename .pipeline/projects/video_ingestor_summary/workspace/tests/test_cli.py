"""Tests for video_ingestor.cli."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure the package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from video_ingestor.cli import main


@pytest.fixture
def mock_storage():
    """Create a mock Storage instance."""
    storage = MagicMock()
    storage.get_job.return_value = {
        "job_id": "test-job-id",
        "status": "completed",
        "full_text": "This is a test transcript.",
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
    return storage


@pytest.fixture
def mock_pipeline():
    """Create a mock IngestionPipeline instance."""
    pipeline = MagicMock()
    pipeline.ingest_from_url.return_value = "test-job-id"
    return pipeline


class TestCLIMain:
    def test_main_no_command(self, capsys):
        """Test that main() prints help when no command is given."""
        with patch("sys.argv", ["cli.py"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "positional arguments:" in captured.out.lower()

    def test_main_status(self, capsys, mock_storage):
        """Test the 'status' subcommand."""
        with patch("sys.argv", ["cli.py", "status", "test-job-id"]):
            with patch("video_ingestor.cli.Storage") as MockStorage:
                MockStorage.return_value = mock_storage
                main()
        mock_storage.connect.assert_called_once()
        mock_storage.close.assert_called_once()
        mock_storage.get_job.assert_called_once_with("test-job-id")
        captured = capsys.readouterr()
        assert "test-job-id" in captured.out
        assert "completed" in captured.out
        assert "This is a test transcript" in captured.out

    def test_main_status_not_found(self, capsys, mock_storage):
        """Test the 'status' subcommand when job is not found."""
        mock_storage.get_job.return_value = None
        with patch("sys.argv", ["cli.py", "status", "nonexistent-job"]):
            with patch("video_ingestor.cli.Storage") as MockStorage:
                MockStorage.return_value = mock_storage
                with pytest.raises(SystemExit) as exc_info:
                    main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_main_list(self, capsys, mock_storage):
        """Test the 'list' subcommand."""
        with patch("sys.argv", ["cli.py", "list"]):
            with patch("video_ingestor.cli.Storage") as MockStorage:
                MockStorage.return_value = mock_storage
                main()
        mock_storage.connect.assert_called_once()
        mock_storage.close.assert_called_once()
        mock_storage.list_jobs.assert_called_once()
        captured = capsys.readouterr()
        assert "test-job-id" in captured.out
        assert "completed" in captured.out

    def test_main_list_empty(self, capsys, mock_storage):
        """Test the 'list' subcommand when no jobs exist."""
        mock_storage.list_jobs.return_value = []
        with patch("sys.argv", ["cli.py", "list"]):
            with patch("video_ingestor.cli.Storage") as MockStorage:
                MockStorage.return_value = mock_storage
                main()
        captured = capsys.readouterr()
        assert "No jobs found" in captured.out

    def test_main_ingest(self, capsys, mock_storage, mock_pipeline):
        """Test the 'ingest' subcommand."""
        with patch("sys.argv", ["cli.py", "ingest", "http://example.com/video.mp4"]):
            with patch("video_ingestor.cli.Storage") as MockStorage:
                with patch("video_ingestor.cli.IngestionPipeline") as MockPipeline:
                    MockStorage.return_value = mock_storage
                    MockPipeline.return_value = mock_pipeline
                    main()
        mock_storage.connect.assert_called_once()
        mock_storage.close.assert_called_once()
        mock_pipeline.ingest_from_url.assert_called_once_with("http://example.com/video.mp4")
        captured = capsys.readouterr()
        assert "test-job-id" in captured.out
        assert "processing" in captured.out

    def test_main_ingest_with_model(self, capsys, mock_storage, mock_pipeline):
        """Test the 'ingest' subcommand with --model flag."""
        with patch("sys.argv", ["cli.py", "ingest", "http://example.com/video.mp4", "--model", "large-v3"]):
            with patch("video_ingestor.cli.Storage") as MockStorage:
                with patch("video_ingestor.cli.IngestionPipeline") as MockPipeline:
                    MockStorage.return_value = mock_storage
                    MockPipeline.return_value = mock_pipeline
                    main()
        # The --model flag is parsed but not used in the current implementation
        # This test verifies the argument is accepted without error
        captured = capsys.readouterr()
        assert "test-job-id" in captured.out

    def test_main_ingest_with_limit(self, capsys, mock_storage):
        """Test the 'list' subcommand with --limit flag."""
        with patch("sys.argv", ["cli.py", "list", "--limit", "5"]):
            with patch("video_ingestor.cli.Storage") as MockStorage:
                MockStorage.return_value = mock_storage
                main()
        mock_storage.list_jobs.assert_called_once_with(limit=5)
