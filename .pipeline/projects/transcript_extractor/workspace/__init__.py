"""
Transcript Extractor - Phase 1

A comprehensive tool for extracting transcripts from video and audio files
using Whisper-based models, with basic summary functionality.
"""

from .config import Config
from .constants import (
    SUPPORTED_FORMATS,
    OUTPUT_FORMATS,
    MODEL_SIZES,
    DEFAULT_MODEL,
    DEFAULT_LANGUAGE,
    DEFAULT_SUMMARY_LENGTH,
    SAMPLE_RATE,
)
from .audio_extractor import AudioExtractor
from .transcriber import WhisperTranscriber
from .parser import TranscriptParser, TranscriptFormatter, TranscriptionSegment, TranscriptionResultData
from .summarizer import SummaryGenerator
from .pipeline import TranscriptionPipeline, TranscriptionOutput

__version__ = "1.0.0"
__all__ = [
    "Config",
    "SUPPORTED_FORMATS",
    "OUTPUT_FORMATS",
    "MODEL_SIZES",
    "DEFAULT_MODEL",
    "DEFAULT_LANGUAGE",
    "DEFAULT_SUMMARY_LENGTH",
    "SAMPLE_RATE",
    "AudioExtractor",
    "WhisperTranscriber",
    "TranscriptParser",
    "TranscriptFormatter",
    "TranscriptionSegment",
    "TranscriptionResultData",
    "SummaryGenerator",
    "TranscriptionPipeline",
    "TranscriptionOutput",
]
