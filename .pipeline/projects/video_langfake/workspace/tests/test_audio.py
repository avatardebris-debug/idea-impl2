"""Tests for video_langfake.audio module."""

import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from video_langfake.audio import (
    extract_audio,
    transcribe_audio,
    detect_language,
    save_transcription,
    load_transcription,
)
from video_langfake.exceptions import AudioError, TranscriptionError


class TestExtractAudio:
    def test_extract_audio_file_not_found(self):
        with pytest.raises(AudioError, match="Video file not found"):
            extract_audio("/nonexistent/video.mp4")

    @patch("video_langfake.audio.os.path.exists", return_value=True)
    @patch("video_langfake.audio.MOVIEPY_AVAILABLE", False)
    def test_extract_audio_moviepy_not_available(self, mock_exists):
        with pytest.raises(AudioError, match="moviepy is required"):
            extract_audio("/tmp/test.mp4")

    @patch("video_langfake.audio.VideoFileClip")
    def test_extract_audio_creates_wav(self, mock_clip):
        mock_audio = MagicMock()
        mock_clip.return_value.audio = mock_audio
        import tempfile
        tmp_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp_video.close()
        try:
            result = extract_audio(tmp_video.name)
            assert result.endswith(".wav")
            assert os.path.exists(result)
            mock_clip.return_value.audio.write_audiofile.assert_called_once()
        finally:
            if os.path.exists(tmp_video.name):
                os.unlink(tmp_video.name)
            if os.path.exists(result):
                os.unlink(result)

    @patch("video_langfake.audio.VideoFileClip")
    def test_extract_audio_with_output_path(self, mock_clip):
        mock_audio = MagicMock()
        mock_audio.write_audiofile.side_effect = lambda path, **kwargs: open(path, "w").close()
        mock_clip.return_value.audio = mock_audio
        tmp_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp_video.close()
        tmp_output = tempfile.mktemp(suffix=".wav")
        try:
            result = extract_audio(tmp_video.name, output_path=tmp_output)
            assert result == tmp_output
        finally:
            if os.path.exists(tmp_video.name):
                os.unlink(tmp_video.name)
            if os.path.exists(tmp_output):
                os.unlink(tmp_output)


class TestTranscribeAudio:
    def test_transcribe_audio_file_not_found(self):
        with pytest.raises(TranscriptionError, match="Audio file not found"):
            transcribe_audio("/nonexistent/audio.wav")

    @patch("video_langfake.audio.WHISPER_AVAILABLE", False)
    def test_transcribe_audio_mock(self):
        tmp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_audio.close()
        try:
            result = transcribe_audio(tmp_audio.name)
            assert "text" in result
            assert "segments" in result
            assert "words" in result
            assert result["text"] == "This is a mock transcription for testing purposes."
        finally:
            if os.path.exists(tmp_audio.name):
                os.unlink(tmp_audio.name)

    @patch("video_langfake.audio._transcribe_with_whisper")
    def test_transcribe_audio_with_whisper(self, mock_whisper):
        mock_whisper.return_value = {"text": "hello", "segments": [], "words": []}
        tmp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_audio.close()
        try:
            result = transcribe_audio(tmp_audio.name, language="en")
            mock_whisper.assert_called_once_with(tmp_audio.name, "en")
        finally:
            if os.path.exists(tmp_audio.name):
                os.unlink(tmp_audio.name)


class TestDetectLanguage:
    def test_detect_language_no_input(self):
        with pytest.raises(AudioError, match="No audio file available"):
            detect_language(audio_path=None, video_path=None)

    @patch("video_langfake.audio.extract_audio")
    @patch("video_langfake.audio.WHISPER_AVAILABLE", False)
    def test_detect_language_from_video_mock(self, mock_extract):
        tmp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_audio.close()
        mock_extract.return_value = tmp_audio.name
        try:
            result = detect_language(video_path="/tmp/test.mp4")
            assert result["language"] == "en"
            assert result["confidence"] == 0.85
        finally:
            if os.path.exists(tmp_audio.name):
                os.unlink(tmp_audio.name)

    @patch("video_langfake.audio._detect_with_whisper")
    def test_detect_language_from_audio_whisper(self, mock_detect):
        mock_detect.return_value = {"language": "es", "confidence": 0.92, "all_languages": []}
        tmp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_audio.close()
        try:
            result = detect_language(audio_path=tmp_audio.name)
            assert result["language"] == "es"
        finally:
            if os.path.exists(tmp_audio.name):
                os.unlink(tmp_audio.name)


class TestSaveLoadTranscription:
    def test_save_and_load_transcription(self):
        tmp_file = tempfile.mktemp(suffix=".json")
        transcription = {
            "text": "Hello world",
            "segments": [{"start": 0.0, "end": 1.0, "text": "Hello world"}],
            "words": [{"word": "Hello", "start": 0.0, "end": 0.5}],
        }
        try:
            result = save_transcription(transcription, tmp_file)
            assert result == tmp_file
            assert os.path.exists(tmp_file)
            loaded = load_transcription(tmp_file)
            assert loaded["text"] == transcription["text"]
            assert len(loaded["segments"]) == len(transcription["segments"])
        finally:
            if os.path.exists(tmp_file):
                os.unlink(tmp_file)

    def test_load_transcription_file_not_found(self):
        with pytest.raises(TranscriptionError, match="Transcription file not found"):
            load_transcription("/nonexistent/transcription.json")
