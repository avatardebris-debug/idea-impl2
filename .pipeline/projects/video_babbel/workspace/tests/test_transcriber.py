"""Tests for the Transcriber class."""

from unittest.mock import MagicMock, patch

import pytest

from video_babbel.core import TranscriptionError
from video_babbel.transcriber import Transcriber


class TestTranscriber:
    """Tests for the Transcriber class."""

    def test_init_default_model(self):
        """Default model should be 'base'."""
        transcriber = Transcriber()
        assert transcriber.model_name == "base"

    def test_init_custom_model(self):
        """Custom model should be set correctly."""
        transcriber = Transcriber(model_name="small")
        assert transcriber.model_name == "small"

    @patch("video_babbel.transcriber.whisper")
    def test_transcribe_returns_segments(self, mock_whisper):
        """transcribe should return a list of segment dicts."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [
                {"text": "Hello world", "start": 0.0, "end": 1.0},
                {"text": "How are you?", "start": 1.0, "end": 2.0},
            ]
        }
        mock_whisper.load_model.return_value = mock_model

        transcriber = Transcriber()
        segments = transcriber.transcribe("/fake/audio.wav")

        assert len(segments) == 2
        assert segments[0]["text"] == "Hello world"
        assert segments[0]["start"] == 0.0
        assert segments[0]["end"] == 1.0
        assert segments[1]["text"] == "How are you?"
        assert segments[1]["start"] == 1.0
        assert segments[1]["end"] == 2.0

    @patch("video_babbel.transcriber.whisper")
    def test_transcribe_filters_empty_text(self, mock_whisper):
        """transcribe should filter out segments with empty text."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [
                {"text": "Hello", "start": 0.0, "end": 1.0},
                {"text": "", "start": 1.0, "end": 2.0},
                {"text": "  ", "start": 2.0, "end": 3.0},
                {"text": "World", "start": 3.0, "end": 4.0},
            ]
        }
        mock_whisper.load_model.return_value = mock_model

        transcriber = Transcriber()
        segments = transcriber.transcribe("/fake/audio.wav")

        assert len(segments) == 2
        assert segments[0]["text"] == "Hello"
        assert segments[1]["text"] == "World"

    @patch("video_babbel.transcriber.whisper")
    def test_transcribe_empty_segments(self, mock_whisper):
        """transcribe should return empty list for no segments."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"segments": []}
        mock_whisper.load_model.return_value = mock_model

        transcriber = Transcriber()
        segments = transcriber.transcribe("/fake/audio.wav")

        assert segments == []

    @patch("video_babbel.transcriber.whisper")
    def test_transcribe_missing_text_key(self, mock_whisper):
        """transcribe should handle segments missing 'text' key."""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [
                {"start": 0.0, "end": 1.0},
                {"text": "Hello", "start": 1.0, "end": 2.0},
            ]
        }
        mock_whisper.load_model.return_value = mock_model

        transcriber = Transcriber()
        segments = transcriber.transcribe("/fake/audio.wav")

        assert len(segments) == 1
        assert segments[0]["text"] == "Hello"

    def test_transcribe_missing_whisper_raises_error(self):
        """TranscriptionError should be raised if whisper is not installed."""
        with patch.dict("sys.modules", {"whisper": None}):
            transcriber = Transcriber()
            with pytest.raises(TranscriptionError, match="openai-whisper is not installed"):
                transcriber.transcribe("/fake/audio.wav")

    @patch("video_babbel.transcriber.whisper")
    def test_transcribe_whisper_error_raises_error(self, mock_whisper):
        """TranscriptionError should be raised if whisper fails."""
        mock_whisper.load_model.side_effect = Exception("whisper error")

        transcriber = Transcriber()
        with pytest.raises(TranscriptionError, match="Transcription failed"):
            transcriber.transcribe("/fake/audio.wav")
