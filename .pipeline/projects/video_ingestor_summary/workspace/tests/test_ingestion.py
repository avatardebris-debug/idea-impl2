"""Tests for video_ingestor.ingestion (mocked Whisper)."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from video_ingestor.ingestion import IngestionPipeline, IngestionError
from video_ingestor.storage import Storage


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def storage(db_path):
    s = Storage(db_path)
    s.connect()
    yield s
    s.close()


@pytest.fixture
def pipeline(storage):
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {
        "segments": [
            {"text": "Hello world", "start": 0.0, "end": 2.0},
        ],
        "text": "Hello world",
    }
    return IngestionPipeline(storage, model=mock_model)


class TestIngestionPipeline:
    def test_transcribe(self, pipeline):
        # Create a dummy audio file
        fd, audio_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        with open(audio_path, "wb") as f:
            f.write(b"\x00" * 100)

        segments, full_text = pipeline.transcribe(audio_path)
        assert full_text == "Hello world"
        assert len(segments) == 1
        os.remove(audio_path)

    def test_ingest_from_url_success(self, pipeline, storage, tmp_path):
        # Create a dummy video file
        video_path = str(tmp_path / "test.mp4")
        with open(video_path, "wb") as f:
            f.write(b"\x00" * 100)

        # Create a dummy audio file
        fd, audio_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        with open(audio_path, "wb") as f:
            f.write(b"\x00" * 100)

        # Mock download_video to return our dummy file
        # Mock extract_audio to return our dummy audio file
        with patch.object(pipeline, "download_video", return_value=video_path):
            with patch.object(pipeline, "extract_audio", return_value=audio_path):
                job_id = pipeline.ingest_from_url("http://example.com/video.mp4")
                assert job_id is not None
                job = storage.get_job(job_id)
                assert job["status"] == "completed"
                assert job["full_text"] == "Hello world"

    def test_ingest_from_url_failure(self, pipeline, storage):
        with patch.object(pipeline, "download_video", side_effect=Exception("network error")):
            with pytest.raises(IngestionError, match="Ingestion failed"):
                pipeline.ingest_from_url("http://example.com/video.mp4")
            # Job should be marked as failed
            # (we can't easily get the job_id here, but the exception is raised)
