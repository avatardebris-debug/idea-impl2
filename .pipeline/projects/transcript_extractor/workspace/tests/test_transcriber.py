"""
Comprehensive tests for WhisperTranscriber class.
"""

import pytest
from unittest.mock import patch, MagicMock

from transcript_extractor.transcriber import WhisperTranscriber
from transcript_extractor.models.whisper_wrapper import TranscriptionResultData


class TestWhisperTranscriberInit:
    """Tests for WhisperTranscriber initialization."""
    
    def test_init_default_model(self):
        """Test default model initialization."""
        with patch("transcript_extractor.transcriber.WhisperWrapper") as MockWrapper:
            transcriber = WhisperTranscriber()
            MockWrapper.assert_called_once_with(
                model_size="small",
                model_path=None,
                device="auto",
                compute_type="float32",
            )
            assert transcriber.model_size == "small"
    
    def test_init_custom_model(self):
        """Test custom model initialization."""
        with patch("transcript_extractor.transcriber.WhisperWrapper") as MockWrapper:
            transcriber = WhisperTranscriber(model_size="large")
            MockWrapper.assert_called_once_with(
                model_size="large",
                model_path=None,
                device="auto",
                compute_type="float32",
            )
            assert transcriber.model_size == "large"
    
    def test_init_with_model_path(self):
        """Test initialization with custom model path."""
        with patch("transcript_extractor.transcriber.WhisperWrapper") as MockWrapper:
            transcriber = WhisperTranscriber(model_path="/custom/model")
            MockWrapper.assert_called_once_with(
                model_size="small",
                model_path="/custom/model",
                device="auto",
                compute_type="float32",
            )
            assert transcriber.model_path == "/custom/model"
    
    def test_init_with_device(self):
        """Test initialization with custom device."""
        with patch("transcript_extractor.transcriber.WhisperWrapper") as MockWrapper:
            transcriber = WhisperTranscriber(device="cuda")
            MockWrapper.assert_called_once_with(
                model_size="small",
                model_path=None,
                device="cuda",
                compute_type="float32",
            )
    
    def test_init_with_compute_type(self):
        """Test initialization with custom compute type."""
        with patch("transcript_extractor.transcriber.WhisperWrapper") as MockWrapper:
            transcriber = WhisperTranscriber(compute_type="int8")
            MockWrapper.assert_called_once_with(
                model_size="small",
                model_path=None,
                device="auto",
                compute_type="int8",
            )


class TestTranscribe:
    """Tests for transcribe method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        mock_wrapper = MagicMock()
        mock_wrapper.transcribe.return_value = TranscriptionResultData(
            text="Test transcript",
            segments=[
                MagicMock(text="Test", start=0, end=1, language="en"),
            ],
            language="en",
            duration=1.0,
            word_count=1,
        )
        with patch("transcript_extractor.transcriber.WhisperWrapper", return_value=mock_wrapper):
            self.transcriber = WhisperTranscriber(model_size="small")
    
    def test_transcribe_success(self):
        """Test successful transcription."""
        result = self.transcriber.transcribe("test_audio.wav")
        assert result.text == "Test transcript"
        assert result.language == "en"
        assert result.duration == 1.0
        assert result.word_count == 1
        assert len(result.segments) == 1
    
    def test_transcribe_with_language(self):
        """Test transcription with specific language."""
        mock_wrapper = MagicMock()
        mock_wrapper.transcribe.return_value = TranscriptionResultData(
            text="Test transcript",
            segments=[],
            language="es",
            duration=1.0,
            word_count=1,
        )
        with patch("transcript_extractor.transcriber.WhisperWrapper", return_value=mock_wrapper):
            transcriber = WhisperTranscriber(model_size="small")
            result = transcriber.transcribe("test_audio.wav", language="es")
            assert result.language == "es"
    
    def test_transcribe_with_timestamps(self):
        """Test transcription with timestamps."""
        mock_wrapper = MagicMock()
        mock_wrapper.transcribe.return_value = TranscriptionResultData(
            text="Test transcript",
            segments=[MagicMock(text="Test", start=0, end=1, language="en")],
            language="en",
            duration=1.0,
            word_count=1,
        )
        with patch("transcript_extractor.transcriber.WhisperWrapper", return_value=mock_wrapper):
            transcriber = WhisperTranscriber(model_size="small")
            result = transcriber.transcribe("test_audio.wav", include_timestamps=True)
            assert len(result.segments) == 1
            mock_wrapper.transcribe.assert_called_once_with(
                audio_path="test_audio.wav",
                language='en',
                word_timestamps=True,
            )
    
    def test_transcribe_without_timestamps(self):
        """Test transcription without timestamps."""
        mock_wrapper = MagicMock()
        mock_wrapper.transcribe.return_value = TranscriptionResultData(
            text="Test transcript",
            segments=[],
            language="en",
            duration=1.0,
            word_count=1,
        )
        with patch("transcript_extractor.transcriber.WhisperWrapper", return_value=mock_wrapper):
            transcriber = WhisperTranscriber(model_size="small")
            result = transcriber.transcribe("test_audio.wav", include_timestamps=False)
            assert len(result.segments) == 0
            mock_wrapper.transcribe.assert_called_once_with(
                audio_path="test_audio.wav",
                language='en',
                word_timestamps=False,
            )
    
    def test_transcribe_returns_correct_type(self):
        """Test that transcribe returns TranscriptionResultData."""
        mock_wrapper = MagicMock()
        mock_wrapper.transcribe.return_value = TranscriptionResultData(
            text="Test transcript",
            segments=[],
            language="en",
            duration=1.0,
            word_count=1,
        )
        with patch("transcript_extractor.transcriber.WhisperWrapper", return_value=mock_wrapper):
            transcriber = WhisperTranscriber(model_size="small")
            result = transcriber.transcribe("test_audio.wav")
            assert isinstance(result, TranscriptionResultData)


class TestTranscribeWithProgress:
    """Tests for transcribe_with_progress method."""
    
    def test_transcribe_with_progress_success(self):
        """Test transcription with progress callback."""
        mock_wrapper = MagicMock()
        mock_wrapper.transcribe.return_value = TranscriptionResultData(
            text="Test transcript",
            segments=[],
            language="en",
            duration=1.0,
            word_count=1,
        )
        with patch("transcript_extractor.transcriber.WhisperWrapper", return_value=mock_wrapper):
            transcriber = WhisperTranscriber(model_size="small")
            progress_calls = []
            def progress_callback(percentage):
                progress_calls.append(percentage)
            result = transcriber.transcribe_with_progress(
                "test_audio.wav",
                progress_callback=progress_callback,
            )
            # progress_callback should be called at start and end
            assert len(progress_calls) == 2
            assert progress_calls[0] == 0.0
            assert progress_calls[1] == 100.0


class TestTranscriberIntegration:
    """Integration tests for WhisperTranscriber."""
    
    def test_transcriber_workflow(self):
        """Test complete transcription workflow."""
        mock_wrapper = MagicMock()
        mock_wrapper.transcribe.return_value = TranscriptionResultData(
            text="Hello world test transcript",
            segments=[
                MagicMock(text="Hello", start=0, end=0.5, language="en"),
                MagicMock(text="world", start=0.5, end=1.0, language="en"),
            ],
            language="en",
            duration=1.0,
            word_count=3,
        )
        with patch("transcript_extractor.transcriber.WhisperWrapper", return_value=mock_wrapper):
            transcriber = WhisperTranscriber(model_size="small")
            result = transcriber.transcribe("test_audio.wav")
            
            assert result.text == "Hello world test transcript"
            assert result.language == "en"
            assert result.duration == 1.0
            assert result.word_count == 3
            assert len(result.segments) == 2
            assert result.segments[0].text == "Hello"
            assert result.segments[1].text == "world"
