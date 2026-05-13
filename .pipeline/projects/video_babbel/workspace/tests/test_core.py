"""Tests for core utilities: sanitize_text and get_logger."""

import logging
import sys
from io import StringIO

import pytest

from video_babbel.core import (
    IngestionError,
    QAError,
    SummarizationError,
    TranslationError,
    TranscriptionError,
    VideoBabbelError,
    get_logger,
    sanitize_text,
)


# ---- sanitize_text tests ----

class TestSanitizeText:
    """Tests for the sanitize_text function."""

    def test_none_input(self):
        assert sanitize_text(None) == ""

    def test_empty_string(self):
        assert sanitize_text("") == ""

    def test_whitespace_only(self):
        assert sanitize_text("   \t\n  ") == ""

    def test_normal_text(self):
        assert sanitize_text("Hello World") == "Hello World"

    def test_leading_trailing_whitespace(self):
        assert sanitize_text("  Hello World  ") == "Hello World"

    def test_multiple_internal_spaces(self):
        assert sanitize_text("Hello    World") == "Hello World"

    def test_tabs_and_newlines(self):
        assert sanitize_text("Hello\t\nWorld") == "Hello World"

    def test_non_string_input(self):
        assert sanitize_text(42) == "42"

    def test_single_word(self):
        assert sanitize_text("Hello") == "Hello"

    def test_unicode_text(self):
        assert sanitize_text("こんにちは 世界") == "こんにちは 世界"


# ---- get_logger tests ----

class TestGetLogger:
    """Tests for the get_logger function."""

    def test_returns_logger(self):
        logger = get_logger("test_logger")
        assert isinstance(logger, logging.Logger)

    def test_logger_has_name(self):
        logger = get_logger("test_logger_name")
        assert logger.name == "test_logger_name"

    def test_logger_has_handler(self):
        logger = get_logger("test_logger_handler")
        assert len(logger.handlers) > 0

    def test_logger_level(self):
        logger = get_logger("test_logger_level", log_level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_logger_level_default(self):
        logger = get_logger("test_logger_default")
        assert logger.level == logging.INFO

    def test_logger_does_not_duplicate_handlers(self):
        logger = get_logger("test_logger_no_dup")
        initial_handlers = len(logger.handlers)
        get_logger("test_logger_no_dup")
        assert len(logger.handlers) == initial_handlers


# ---- Exception hierarchy tests ----

class TestExceptionHierarchy:
    """Tests for the custom exception hierarchy."""

    def test_video_babbel_error_base(self):
        err = VideoBabbelError("test message")
        assert str(err) == "test message"
        assert err.message == "test message"

    def test_ingestion_error(self):
        err = IngestionError("ingest failed", video_path="/path/to/video.mp4")
        assert str(err) == "ingest failed"
        assert err.video_path == "/path/to/video.mp4"

    def test_transcription_error(self):
        err = TranscriptionError("transcribe failed")
        assert str(err) == "transcribe failed"

    def test_translation_error(self):
        err = TranslationError("translate failed", source_lang="en", target_lang="es")
        assert str(err) == "translate failed"
        assert err.source_lang == "en"
        assert err.target_lang == "es"

    def test_summarization_error(self):
        err = SummarizationError("summarize failed")
        assert str(err) == "summarize failed"

    def test_qa_error(self):
        err = QAError("qa failed")
        assert str(err) == "qa failed"

    def test_all_exceptions_inherit_from_video_babbel_error(self):
        assert issubclass(IngestionError, VideoBabbelError)
        assert issubclass(TranscriptionError, VideoBabbelError)
        assert issubclass(TranslationError, VideoBabbelError)
        assert issubclass(SummarizationError, VideoBabbelError)
        assert issubclass(QAError, VideoBabbelError)
