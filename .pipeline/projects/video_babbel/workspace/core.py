"""Core data models and shared utilities for the VideoBabbel pipeline."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Custom exception hierarchy
# ---------------------------------------------------------------------------

class VideoBabbelError(Exception):
    """Base exception for all VideoBabbel errors.

    Parameters
    ----------
    message : str
        The error message.
    """

    def __init__(self, message: str = "A VideoBabbel error occurred") -> None:
        super().__init__(message)
        self.message: str = message


class IngestionError(VideoBabbelError):
    """Raised when video ingestion fails.

    Parameters
    ----------
    message : str
        The error message.
    video_path : str or None
        Path to the video that failed.
    """

    def __init__(
        self,
        message: str = "Video ingestion failed",
        video_path: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.video_path: Optional[str] = video_path


class TranscriptionError(VideoBabbelError):
    """Raised when transcription fails.

    Parameters
    ----------
    message : str
        The error message.
    """

    def __init__(self, message: str = "Transcription failed") -> None:
        super().__init__(message)


class TranslationError(VideoBabbelError):
    """Raised when translation fails.

    Parameters
    ----------
    message : str
        The error message.
    source_lang : str or None
        Source language code.
    target_lang : str or None
        Target language code.
    """

    def __init__(
        self,
        message: str = "Translation failed",
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.source_lang: Optional[str] = source_lang
        self.target_lang: Optional[str] = target_lang


class SummarizationError(VideoBabbelError):
    """Raised when summarization fails.

    Parameters
    ----------
    message : str
        The error message.
    """

    def __init__(self, message: str = "Summarization failed") -> None:
        super().__init__(message)


class QAError(VideoBabbelError):
    """Raised when Q&A generation fails.

    Parameters
    ----------
    message : str
        The error message.
    """

    def __init__(self, message: str = "Q&A failed") -> None:
        super().__init__(message)


# ---------------------------------------------------------------------------
# Core data models
# ---------------------------------------------------------------------------

@dataclass
class TranscriptSegment:
    """A single segment from a transcript.

    Attributes
    ----------
    start : float
        Start time in seconds.
    end : float
        End time in seconds.
    text : str
        Transcribed text.
    """

    start: float
    end: float
    text: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary."""
        return {"start": self.start, "end": self.end, "text": self.text}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TranscriptSegment":
        """Create from a dictionary."""
        return cls(start=data["start"], end=data["end"], text=data["text"])


@dataclass
class PipelineResult:
    """Result of a full pipeline run.

    Attributes
    ----------
    transcript : list[TranscriptSegment]
        List of transcript segments.
    translation : str
        Translated text.
    summary : str
        Summary text.
    qa : str
        Q&A answer text.
    """

    transcript: List[TranscriptSegment]
    translation: str
    summary: str
    qa: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary."""
        return {
            "transcript": [seg.to_dict() for seg in self.transcript],
            "translation": self.translation,
            "summary": self.summary,
            "qa": self.qa,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineResult":
        """Create from a dictionary."""
        return cls(
            transcript=[TranscriptSegment.from_dict(seg) for seg in data["transcript"]],
            translation=data["translation"],
            summary=data["summary"],
            qa=data["qa"],
        )


# ---------------------------------------------------------------------------
# Core utilities
# ---------------------------------------------------------------------------

def sanitize_text(text: Optional[str]) -> str:
    """Sanitize text by stripping whitespace and normalizing internal spacing.

    Parameters
    ----------
    text : str or None
        The raw text to sanitize.

    Returns
    -------
    str
        The sanitized text. Returns an empty string if *text* is None or
        whitespace-only.
    """
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    cleaned = text.strip()
    # Collapse multiple internal whitespace runs into a single space
    cleaned = " ".join(cleaned.split())
    return cleaned


def get_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger.

    Parameters
    ----------
    name : str
        Logger name (typically ``__name__``).
    log_level : int
        Logging level (default: ``logging.INFO``).

    Returns
    -------
    logging.Logger
        A logger with a StreamHandler that writes to stderr.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(log_level)
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(handler)
    return logger
