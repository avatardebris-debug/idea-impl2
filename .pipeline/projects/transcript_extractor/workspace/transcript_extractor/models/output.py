"""
Output dataclass for transcription pipeline results.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TranscriptionOutput:
    """Represents the output of a transcription pipeline run."""
    success: bool = False
    transcript: str = ""
    summary: str = ""
    output_path: Optional[str] = None
    error: Optional[str] = None
    format: Optional[str] = None
    duration: float = 0.0
    language: Optional[str] = None
