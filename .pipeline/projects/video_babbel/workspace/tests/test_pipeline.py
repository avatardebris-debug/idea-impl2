"""Tests for the VideoBabbel pipeline."""

from unittest.mock import MagicMock, patch

import pytest

from video_babbel.core import VideoBabbelError
from video_babbel.pipeline import VideoBabbel


class TestVideoBabbel:
    """Tests for the VideoBabbel pipeline class."""

    def test_init_default_values(self):
        """VideoBabbel should initialize with default values."""
        pipeline = VideoBabbel()
        assert pipeline.target_lang == "es"
        assert pipeline.whisper_model == "base"
        assert pipeline.max_sentences == 5

    def test_init_custom_values(self):
        """VideoBabbel should initialize with custom values."""
        pipeline = VideoBabbel(
            target_lang="fr",
            whisper_model="small",
            max_sentences=10,
        )
        assert pipeline.target_lang == "fr"
        assert pipeline.whisper_model == "small"
        assert pipeline.max_sentences == 10

    @patch("video_babbel.pipeline.VideoIngestor")
    @patch("video_babbel.pipeline.Transcriber")
    @patch("video_babbel.pipeline.Translator")
    @patch("video_babbel.pipeline.Summarizer")
    @patch("video_babbel.pipeline.QAEngine")
    def test_process_calls_all_components(
        self, mock_qa, mock_summarizer, mock_translator, mock_transcriber, mock_ingestor
    ):
        """process should call all components in sequence."""
        # Setup mocks
        mock_ingestor_instance = MagicMock()
        mock_ingestor_instance.audio_path = "/fake/audio.wav"
        mock_ingestor.return_value = mock_ingestor_instance

        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.return_value = [
            {"text": "Hello world", "start": 0.0, "end": 1.0},
        ]
        mock_transcriber.return_value = mock_transcriber_instance

        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.return_value = "Hola mundo"
        mock_translator.return_value = mock_translator_instance

        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.summarize.return_value = "Hello world"
        mock_summarizer.return_value = mock_summarizer_instance

        mock_qa_instance = MagicMock()
        mock_qa_instance.answer.return_value = "Hello world"
        mock_qa.return_value = mock_qa_instance

        # Create pipeline and process
        pipeline = VideoBabbel()
        result = pipeline.process("/fake/video.mp4")

        # Verify all components were called
        mock_ingestor.assert_called_once_with("/fake/video.mp4")
        mock_transcriber.assert_called_once_with("base")
        mock_translator.assert_called_once_with("es")
        mock_summarizer.assert_called_once_with(5)
        mock_qa.assert_called_once_with([{"text": "Hello world", "start": 0.0, "end": 1.0}])

        # Verify result structure
        assert "transcript" in result
        assert "translation" in result
        assert "summary" in result
        assert "qa" in result

    @patch("video_babbel.pipeline.VideoIngestor")
    def test_process_handles_ingestion_error(self, mock_ingestor):
        """process should raise VideoBabbelError on ingestion failure."""
        from video_babbel.core import IngestionError
        mock_ingestor.side_effect = IngestionError("ingest failed")

        pipeline = VideoBabbel()
        with pytest.raises(VideoBabbelError, match="Ingestion failed"):
            pipeline.process("/fake/video.mp4")

    @patch("video_babbel.pipeline.VideoIngestor")
    @patch("video_babbel.pipeline.Transcriber")
    def test_process_handles_transcription_error(self, mock_transcriber, mock_ingestor):
        """process should raise VideoBabbelError on transcription failure."""
        from video_babbel.core import TranscriptionError
        mock_ingestor_instance = MagicMock()
        mock_ingestor_instance.audio_path = "/fake/audio.wav"
        mock_ingestor.return_value = mock_ingestor_instance
        mock_transcriber.side_effect = TranscriptionError("transcribe failed")

        pipeline = VideoBabbel()
        with pytest.raises(VideoBabbelError, match="Transcription failed"):
            pipeline.process("/fake/video.mp4")

    @patch("video_babbel.pipeline.VideoIngestor")
    @patch("video_babbel.pipeline.Transcriber")
    @patch("video_babbel.pipeline.Translator")
    def test_process_handles_translation_error(self, mock_translator, mock_transcriber, mock_ingestor):
        """process should raise VideoBabbelError on translation failure."""
        from video_babbel.core import TranslationError
        mock_ingestor_instance = MagicMock()
        mock_ingestor_instance.audio_path = "/fake/audio.wav"
        mock_ingestor.return_value = mock_ingestor_instance
        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.return_value = [
            {"text": "Hello world", "start": 0.0, "end": 1.0},
        ]
        mock_transcriber.return_value = mock_transcriber_instance
        mock_translator.side_effect = TranslationError("translate failed")

        pipeline = VideoBabbel()
        with pytest.raises(VideoBabbelError, match="Translation failed"):
            pipeline.process("/fake/video.mp4")

    @patch("video_babbel.pipeline.VideoIngestor")
    @patch("video_babbel.pipeline.Transcriber")
    @patch("video_babbel.pipeline.Translator")
    @patch("video_babbel.pipeline.Summarizer")
    def test_process_handles_summarization_error(self, mock_summarizer, mock_translator, mock_transcriber, mock_ingestor):
        """process should raise VideoBabbelError on summarization failure."""
        from video_babbel.core import SummarizationError
        mock_ingestor_instance = MagicMock()
        mock_ingestor_instance.audio_path = "/fake/audio.wav"
        mock_ingestor.return_value = mock_ingestor_instance
        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.return_value = [
            {"text": "Hello world", "start": 0.0, "end": 1.0},
        ]
        mock_transcriber.return_value = mock_transcriber_instance
        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.return_value = "Hola mundo"
        mock_translator.return_value = mock_translator_instance
        mock_summarizer.side_effect = SummarizationError("summarize failed")

        pipeline = VideoBabbel()
        with pytest.raises(VideoBabbelError, match="Summarization failed"):
            pipeline.process("/fake/video.mp4")

    @patch("video_babbel.pipeline.VideoIngestor")
    @patch("video_babbel.pipeline.Transcriber")
    @patch("video_babbel.pipeline.Translator")
    @patch("video_babbel.pipeline.Summarizer")
    @patch("video_babbel.pipeline.QAEngine")
    def test_process_returns_correct_structure(self, mock_qa, mock_summarizer, mock_translator, mock_transcriber, mock_ingestor):
        """process should return a dict with correct structure."""
        mock_ingestor_instance = MagicMock()
        mock_ingestor_instance.audio_path = "/fake/audio.wav"
        mock_ingestor.return_value = mock_ingestor_instance

        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.return_value = [
            {"text": "Hello world", "start": 0.0, "end": 1.0},
        ]
        mock_transcriber.return_value = mock_transcriber_instance

        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.return_value = "Hola mundo"
        mock_translator.return_value = mock_translator_instance

        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.summarize.return_value = "Hello world"
        mock_summarizer.return_value = mock_summarizer_instance

        mock_qa_instance = MagicMock()
        mock_qa_instance.answer.return_value = "Hello world"
        mock_qa.return_value = mock_qa_instance

        pipeline = VideoBabbel()
        result = pipeline.process("/fake/video.mp4")

        assert isinstance(result, dict)
        assert "transcript" in result
        assert "translation" in result
        assert "summary" in result
        assert "qa" in result
        assert isinstance(result["transcript"], list)
        assert isinstance(result["translation"], str)
        assert isinstance(result["summary"], str)
        assert isinstance(result["qa"], str)
