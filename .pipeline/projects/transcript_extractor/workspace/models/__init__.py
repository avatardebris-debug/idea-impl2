"""
Models package initialization.

Provides wrappers for Whisper/Faster-Whisper API.
"""

from .whisper_wrapper import WhisperTranscriber, WhisperWrapper

__all__ = ["WhisperTranscriber", "WhisperWrapper"]
