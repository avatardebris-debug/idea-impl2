"""Audio transcription module — uses Whisper to transcribe audio."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from video_babbel.core import TranscriptionError, get_logger

logger = get_logger(__name__)


def _get_whisper():
    """Import and return whisper module, raising TranscriptionError if unavailable."""
    try:
        import whisper
        return whisper
    except ImportError:
        raise TranscriptionError("openai-whisper is not installed")


class Transcriber:
    """Transcribes audio files using OpenAI Whisper.

    Parameters
    ----------
    model_name : str
        Whisper model size (e.g. ``"tiny"``, ``"base"``, ``"small"``,
        ``"medium"``, ``"large"``).  Default is ``"base"``.
    """

    def __init__(self, model_name: str = "base") -> None:
        self.model_name = model_name
        logger.info("Initializing Transcriber with model '%s'", model_name)

    def transcribe(self, audio_path: str) -> List[Dict[str, Any]]:
        """Transcribe an audio file.

        Parameters
        ----------
        audio_path : str
            Path to the audio file.

        Returns
        ----- --
        list[dict]
            List of transcription segments, each containing ``text``,
            ``start``, and ``end`` keys.

        Raises
        ------
        TranscriptionError
            If transcription fails.
        """
        logger.info("Transcribing audio file: %s", audio_path)
        try:
            whisper = _get_whisper()
            model = whisper.load_model(self.model_name)
            result = model.transcribe(audio_path)

            segments = result.get("segments", [])
            filtered = []
            for seg in segments:
                text = seg.get("text", "")
                if text and text.strip():
                    filtered.append(
                        {
                            "text": text.strip(),
                            "start": seg.get("start", 0.0),
                            "end": seg.get("end", 0.0),
                        }
                    )

            logger.info("Transcription complete: %d segments", len(filtered))
            return filtered
        except TranscriptionError:
            raise
        except Exception as exc:
            raise TranscriptionError(f"Transcription failed: {exc}") from exc
