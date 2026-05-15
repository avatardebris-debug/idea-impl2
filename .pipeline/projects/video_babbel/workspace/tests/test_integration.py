"""Integration (smoke) tests for the VideoBabbel pipeline.

All external dependencies (ffmpeg, whisper, googletrans) are mocked so
these tests run without any real hardware or network access.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure the workspace root is on sys.path so imports work
_ws = Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from video_babbel.core import (
    IngestionError,
    QAError,
    SummarizationError,
    TranslationError,
    TranscriptionError,
    VideoBabbelError,
)
from video_babbel.pipeline import VideoBabbel


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_all_components():
    """Return a dict of mock instances for every pipeline component."""
    mocks = {}

    # VideoIngestor
    mock_ingestor_cls = MagicMock()
    mock_ingestor_instance = MagicMock()
    mock_ingestor_instance.audio_path = "/fake/audio.wav"
    mock_ingestor_cls.return_value = mock_ingestor_instance
    mocks["ingestor"] = (mock_ingestor_cls, mock_ingestor_instance)

    # Transcriber
    mock_transcriber_cls = MagicMock()
    mock_transcriber_instance = MagicMock()
    mock_transcriber_instance.transcribe.return_value = [
        {"text": "Hello world", "start": 0.0, "end": 1.0},
    ]
    mock_transcriber_cls.return_value = mock_transcriber_instance
    mocks["transcriber"] = (mock_transcriber_cls, mock_transcriber_instance)

    # Translator
    mock_translator_cls = MagicMock()
    mock_translator_instance = MagicMock()
    mock_translator_instance.translate.return_value = "Hola mundo"
    mock_translator_cls.return_value = mock_translator_instance
    mocks["translator"] = (mock_translator_cls, mock_translator_instance)

    # Summarizer
    mock_summarizer_cls = MagicMock()
    mock_summarizer_instance = MagicMock()
    mock_summarizer_instance.summarize.return_value = "Hello world summary"
    mock_summarizer_cls.return_value = mock_summarizer_instance
    mocks["summarizer"] = (mock_summarizer_cls, mock_summarizer_instance)

    # QAEngine
    mock_qa_cls = MagicMock()
    mock_qa_instance = MagicMock()
    mock_qa_instance.answer.return_value = "The main topic is AI."
    mock_qa_cls.return_value = mock_qa_instance
    mocks["qa"] = (mock_qa_cls, mock_qa_instance)

    return mocks


# ---------------------------------------------------------------------------
# Full pipeline flow
# ---------------------------------------------------------------------------

class TestFullPipelineFlow:
    """End-to-end smoke tests for the pipeline."""

    @patch("video_babbel.pipeline.VideoIngestor")
    @patch("video_babbel.pipeline.Transcriber")
    @patch("video_babbel.pipeline.Translator")
    @patch("video_babbel.pipeline.Summarizer")
    @patch("video_babbel.pipeline.QAEngine")
    def test_full_pipeline_succeeds(
        self,
        mock_qa_cls,
        mock_summarizer_cls,
        mock_translator_cls,
        mock_transcriber_cls,
        mock_ingestor_cls,
    ):
        """The full pipeline should succeed when all components work."""
        # Arrange
        mock_ingestor_instance = MagicMock()
        mock_ingestor_instance.audio_path = "/fake/audio.wav"
        mock_ingestor_cls.return_value = mock_ingestor_instance

        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.return_value = [
            {"text": "Hello world", "start": 0.0, "end": 1.0},
        ]
        mock_transcriber_cls.return_value = mock_transcriber_instance

        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.return_value = "Hola mundo"
        mock_translator_cls.return_value = mock_translator_instance

        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.summarize.return_value = "Hello world summary"
        mock_summarizer_cls.return_value = mock_summarizer_instance

        mock_qa_instance = MagicMock()
        mock_qa_instance.answer.return_value = "The main topic is AI."
        mock_qa_cls.return_value = mock_qa_instance

        # Act
        pipeline = VideoBabbel(target_lang="es", whisper_model="base", max_sentences=5, backend="google")
        result = pipeline.process("/fake/video.mp4")

        # Assert
        assert isinstance(result, dict)
        assert result["transcript"] == [{"text": "Hello world", "start": 0.0, "end": 1.0}]
        assert result["translation"] == "Hola mundo"
        assert result["summary"] == "Hello world summary"
        assert result["qa"] == "The main topic is AI."

        # Verify all components were called in the right order
        mock_ingestor_cls.assert_called_once_with("/fake/video.mp4")
        mock_transcriber_cls.assert_called_once_with("base")
        mock_translator_cls.assert_called_once_with("es", backend="google")
        mock_summarizer_cls.assert_called_once_with(5)
        mock_qa_cls.assert_called_once()

    @patch("video_babbel.pipeline.VideoIngestor")
    @patch("video_babbel.pipeline.Transcriber")
    @patch("video_babbel.pipeline.Translator")
    @patch("video_babbel.pipeline.Summarizer")
    @patch("video_babbel.pipeline.QAEngine")
    def test_pipeline_with_custom_params(
        self,
        mock_qa_cls,
        mock_summarizer_cls,
        mock_translator_cls,
        mock_transcriber_cls,
        mock_ingestor_cls,
    ):
        """Pipeline should honour custom constructor parameters."""
        mock_ingestor_instance = MagicMock()
        mock_ingestor_instance.audio_path = "/fake/audio.wav"
        mock_ingestor_cls.return_value = mock_ingestor_instance

        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.return_value = [
            {"text": "Test", "start": 0.0, "end": 1.0},
        ]
        mock_transcriber_cls.return_value = mock_transcriber_instance

        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.return_value = "Test FR"
        mock_translator_cls.return_value = mock_translator_instance

        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.summarize.return_value = "Summary"
        mock_summarizer_cls.return_value = mock_summarizer_instance

        mock_qa_instance = MagicMock()
        mock_qa_instance.answer.return_value = "Answer"
        mock_qa_cls.return_value = mock_qa_instance

        pipeline = VideoBabbel(
            target_lang="fr",
            whisper_model="small",
            max_sentences=10,
            backend="deepL",
        )
        result = pipeline.process("/fake/video.mp4")

        assert result["translation"] == "Test FR"
        mock_transcriber_cls.assert_called_once_with("small")
        mock_translator_cls.assert_called_once_with("fr", backend="deepL")
        mock_summarizer_cls.assert_called_once_with(10)


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------

class TestErrorPropagation:
    """Each component failure should raise a VideoBabbelError."""

    @patch("video_babbel.pipeline.VideoIngestor")
    def test_ingestion_error(self, mock_ingestor):
        mock_ingestor.side_effect = IngestionError("ingest failed")
        pipeline = VideoBabbel()
        with pytest.raises(VideoBabbelError, match="ingest failed"):
            pipeline.process("/fake/video.mp4")

    @patch("video_babbel.pipeline.VideoIngestor")
    @patch("video_babbel.pipeline.Transcriber")
    def test_transcription_error(self, mock_transcriber, mock_ingestor):
        mock_ingestor_instance = MagicMock()
        mock_ingestor_instance.audio_path = "/fake/audio.wav"
        mock_ingestor.return_value = mock_ingestor_instance
        mock_transcriber.side_effect = TranscriptionError("transcribe failed")
        pipeline = VideoBabbel()
        with pytest.raises(VideoBabbelError, match="transcribe failed"):
            pipeline.process("/fake/video.mp4")

    @patch("video_babbel.pipeline.VideoIngestor")
    @patch("video_babbel.pipeline.Transcriber")
    @patch("video_babbel.pipeline.Translator")
    def test_translation_error(self, mock_translator, mock_transcriber, mock_ingestor):
        mock_ingestor_instance = MagicMock()
        mock_ingestor_instance.audio_path = "/fake/audio.wav"
        mock_ingestor.return_value = mock_ingestor_instance
        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.return_value = [{"text": "Hi", "start": 0.0, "end": 1.0}]
        mock_transcriber.return_value = mock_transcriber_instance
        mock_translator.side_effect = TranslationError("translate failed")
        pipeline = VideoBabbel()
        with pytest.raises(VideoBabbelError, match="translate failed"):
            pipeline.process("/fake/video.mp4")

    @patch("video_babbel.pipeline.VideoIngestor")
    @patch("video_babbel.pipeline.Transcriber")
    @patch("video_babbel.pipeline.Translator")
    @patch("video_babbel.pipeline.Summarizer")
    def test_summarization_error(self, mock_summarizer, mock_translator, mock_transcriber, mock_ingestor):
        mock_ingestor_instance = MagicMock()
        mock_ingestor_instance.audio_path = "/fake/audio.wav"
        mock_ingestor.return_value = mock_ingestor_instance
        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.return_value = [{"text": "Hi", "start": 0.0, "end": 1.0}]
        mock_transcriber.return_value = mock_transcriber_instance
        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.return_value = "Hola"
        mock_translator.return_value = mock_translator_instance
        mock_summarizer.side_effect = SummarizationError("summarize failed")
        pipeline = VideoBabbel()
        with pytest.raises(VideoBabbelError, match="summarize failed"):
            pipeline.process("/fake/video.mp4")

    @patch("video_babbel.pipeline.VideoIngestor")
    @patch("video_babbel.pipeline.Transcriber")
    @patch("video_babbel.pipeline.Translator")
    @patch("video_babbel.pipeline.Summarizer")
    @patch("video_babbel.pipeline.QAEngine")
    def test_qa_error(self, mock_qa, mock_summarizer, mock_translator, mock_transcriber, mock_ingestor):
        mock_ingestor_instance = MagicMock()
        mock_ingestor_instance.audio_path = "/fake/audio.wav"
        mock_ingestor.return_value = mock_ingestor_instance
        mock_transcriber_instance = MagicMock()
        mock_transcriber_instance.transcribe.return_value = [{"text": "Hi", "start": 0.0, "end": 1.0}]
        mock_transcriber.return_value = mock_transcriber_instance
        mock_translator_instance = MagicMock()
        mock_translator_instance.translate.return_value = "Hola"
        mock_translator.return_value = mock_translator_instance
        mock_summarizer_instance = MagicMock()
        mock_summarizer_instance.summarize.return_value = "Summary"
        mock_summarizer.return_value = mock_summarizer_instance
        mock_qa.side_effect = QAError("qa failed")
        pipeline = VideoBabbel()
        with pytest.raises(VideoBabbelError, match="qa failed"):
            pipeline.process("/fake/video.mp4")


# ---------------------------------------------------------------------------
# QA engine standalone
# ---------------------------------------------------------------------------

class TestQAEngine:
    """Tests for the QA engine in isolation."""

    def test_answer_returns_string(self):
        """QA engine answer should return a string."""
        from video_babbel.pipeline import QAEngine

        qa = QAEngine(segments=[{"text": "Hello world", "start": 0.0, "end": 1.0}])
        answer = qa.answer("Hello?")
        assert isinstance(answer, str)
        assert len(answer) > 0

    def test_answer_with_empty_transcript(self):
        """QA engine should handle empty transcript gracefully."""
        from video_babbel.pipeline import QAEngine

        qa = QAEngine(segments=[])
        answer = qa.answer("What is the topic?")
        assert isinstance(answer, str)


# ---------------------------------------------------------------------------
# Core data models
# ---------------------------------------------------------------------------

class TestTranscriptSegment:
    """Tests for the TranscriptSegment dataclass."""

    def test_to_dict(self):
        from video_babbel.core import TranscriptSegment

        seg = TranscriptSegment(start=0.0, end=1.0, text="Hello")
        d = seg.to_dict()
        assert d == {"start": 0.0, "end": 1.0, "text": "Hello"}

    def test_from_dict(self):
        from video_babbel.core import TranscriptSegment

        data = {"start": 0.0, "end": 1.0, "text": "Hello"}
        seg = TranscriptSegment.from_dict(data)
        assert seg.start == 0.0
        assert seg.end == 1.0
        assert seg.text == "Hello"


class TestPipelineResult:
    """Tests for the PipelineResult dataclass."""

    def test_to_dict(self):
        from video_babbel.core import PipelineResult, TranscriptSegment

        result = PipelineResult(
            transcript=[TranscriptSegment(start=0.0, end=1.0, text="Hi")],
            translation="Hola",
            summary="Summary",
            qa="Answer",
        )
        d = result.to_dict()
        assert d["translation"] == "Hola"
        assert d["summary"] == "Summary"
        assert d["qa"] == "Answer"
        assert len(d["transcript"]) == 1

    def test_from_dict(self):
        from video_babbel.core import PipelineResult, TranscriptSegment

        data = {
            "transcript": [{"start": 0.0, "end": 1.0, "text": "Hi"}],
            "translation": "Hola",
            "summary": "Summary",
            "qa": "Answer",
        }
        result = PipelineResult.from_dict(data)
        assert result.translation == "Hola"
        assert result.summary == "Summary"
        assert result.qa == "Answer"
        assert len(result.transcript) == 1
        assert isinstance(result.transcript[0], TranscriptSegment)


# ---------------------------------------------------------------------------
# Core utilities
# ---------------------------------------------------------------------------

class TestSanitizeText:
    """Tests for the sanitize_text utility."""

    def test_none_input(self):
        from video_babbel.core import sanitize_text
        assert sanitize_text(None) == ""

    def test_whitespace_only(self):
        from video_babbel.core import sanitize_text
        assert sanitize_text("   \n\t  ") == ""

    def test_normal_text(self):
        from video_babbel.core import sanitize_text
        assert sanitize_text("  Hello  world  ") == "Hello world"

    def test_empty_string(self):
        from video_babbel.core import sanitize_text
        assert sanitize_text("") == ""

    def test_non_string_input(self):
        from video_babbel.core import sanitize_text
        assert sanitize_text(123) == "123"


class TestGetLogger:
    """Tests for the get_logger utility."""

    def test_returns_logger(self):
        from video_babbel.core import get_logger
        import logging

        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_logger_has_handler(self):
        from video_babbel.core import get_logger

        logger = get_logger("test_logger2")
        assert len(logger.handlers) > 0
