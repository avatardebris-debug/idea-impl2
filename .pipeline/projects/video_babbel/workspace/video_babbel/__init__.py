"""VideoBabbel — Video Translation Pipeline.

A modular pipeline for video transcription, translation, summarization,
and Q&A.

Public API
----------
- ``VideoBabbel`` — end-to-end pipeline
- ``VideoIngestor`` — video → audio extraction
- ``Transcriber`` — audio → text transcription
- ``Translator`` — text translation between languages
- ``Summarizer`` — transcript summarization
- ``QAEngine`` — question answering from transcripts

Core utilities
--------------
- ``sanitize_text`` — text sanitization
- ``get_logger`` — logger factory

Custom exceptions
-----------------
- ``VideoBabbelError`` — base exception
- ``IngestionError`` — ingestion failures
- ``TranscriptionError`` — transcription failures
- ``TranslationError`` — translation failures
- ``SummarizationError`` — summarization failures
- ``QAError`` — Q&A failures
"""

from __future__ import annotations

__all__: list[str] = [
    "VideoBabbel",
    "VideoIngestor",
    "Transcriber",
    "Translator",
    "Summarizer",
    "QAEngine",
    "sanitize_text",
    "get_logger",
    "VideoBabbelError",
    "IngestionError",
    "TranscriptionError",
    "TranslationError",
    "SummarizationError",
    "QAError",
]

from video_babbel.core import (
    QAError,
    SummarizationError,
    TranslationError,
    TranscriptionError,
    VideoBabbelError,
    get_logger,
    sanitize_text,
)
from video_babbel.ingestor import VideoIngestor
from video_babbel.pipeline import VideoBabbel
from video_babbel.qa import QAEngine
from video_babbel.summarizer import Summarizer
from video_babbel.transcriber import Transcriber
from video_babbel.translator import Translator
