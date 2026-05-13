"""Tests for the VideoIngestor class."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from video_babbel.core import IngestionError
from video_babbel.ingestor import VideoIngestor


class TestVideoIngestor:
    """Tests for the VideoIngestor class."""

    def test_nonexistent_video_raises_ingestion_error(self):
        """IngestionError should be raised for a non-existent video file."""
        with pytest.raises(IngestionError, match="Video file not found"):
            VideoIngestor(video_path="/nonexistent/video.mp4")

    @patch("video_babbel.ingestor.subprocess.run")
    def test_audio_extraction_calls_ffmpeg(self, mock_run):
        """ffmpeg should be called with correct arguments."""
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake video data")
            video_path = f.name

        try:
            ingestor = VideoIngestor(video_path=video_path)
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            args = call_args[0][0]
            assert "ffmpeg" in args
            assert "-i" in args
            assert video_path in args
            assert "-vn" in args
            assert "-acodec" in args
            assert "pcm_s16le" in args
            assert ingestor.audio_path is not None
        finally:
            ingestor.cleanup()
            os.unlink(video_path)

    @patch("video_babbel.ingestor.subprocess.run")
    def test_ffmpeg_failure_raises_ingestion_error(self, mock_run):
        """IngestionError should be raised when ffmpeg fails."""
        from subprocess import CalledProcessError
        mock_run.side_effect = CalledProcessError(1, "ffmpeg", stderr="error")

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake video data")
            video_path = f.name

        try:
            with pytest.raises(IngestionError, match="ffmpeg failed"):
                VideoIngestor(video_path=video_path)
        finally:
            os.unlink(video_path)

    def test_audio_path_property_returns_string(self):
        """audio_path property should return a string."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake video data")
            video_path = f.name

        try:
            with patch("video_babbel.ingestor.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr="")
                ingestor = VideoIngestor(video_path=video_path)
                assert isinstance(ingestor.audio_path, str)
                assert len(ingestor.audio_path) > 0
        finally:
            os.unlink(video_path)

    def test_cleanup_does_not_raise(self):
        """cleanup should not raise even if called multiple times."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake video data")
            video_path = f.name

        try:
            with patch("video_babbel.ingestor.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr="")
                ingestor = VideoIngestor(video_path=video_path)
                ingestor.cleanup()
                ingestor.cleanup()  # Should not raise
        finally:
            os.unlink(video_path)

    def test_from_path_classmethod(self):
        """from_path should create a VideoIngestor instance."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(b"fake video data")
            video_path = f.name

        try:
            with patch("video_babbel.ingestor.subprocess.run") as mock_run:
                mock_run.return_value = MagicMock(returncode=0, stderr="")
                ingestor = VideoIngestor.from_path(video_path)
                assert isinstance(ingestor, VideoIngestor)
        finally:
            os.unlink(video_path)
