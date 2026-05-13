"""Tests for video_ingestor.config."""

import os
import sys
from unittest.mock import patch

import pytest


class TestSettings:
    def test_default_values(self):
        # Import fresh to get default values
        # Remove cached module if present
        if "video_ingestor.config" in sys.modules:
            del sys.modules["video_ingestor.config"]
        from video_ingestor.config import Settings

        s = Settings()
        assert s.HOST == "0.0.0.0"
        assert s.PORT == 8000
        assert s.WHISPER_MODEL == "base"
        assert "mp4" in s.ALLOWED_FORMATS
        assert "mov" in s.ALLOWED_FORMATS

    def test_env_override(self):
        # Remove cached module to get fresh env var reads
        if "video_ingestor.config" in sys.modules:
            del sys.modules["video_ingestor.config"]

        with patch.dict(os.environ, {"VIDEO_INGESTOR_PORT": "9999", "WHISPER_MODEL": "small"}):
            from video_ingestor.config import Settings

            s = Settings()
            assert s.PORT == 9999
            assert s.WHISPER_MODEL == "small"

    def test_has_cuda_false(self):
        # Remove cached module to get fresh env var reads
        if "video_ingestor.config" in sys.modules:
            del sys.modules["video_ingestor.config"]

        # Patch torch at the module level before importing config
        with patch("torch.cuda.is_available", return_value=False):
            from video_ingestor.config import Settings

            s = Settings()
            # _has_cuda should return False when torch is not available
            assert s._has_cuda() is False
