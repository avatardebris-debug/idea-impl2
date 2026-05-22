"""Video ingestion module — extracts audio from video files."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from video_babbel.core import IngestionError, get_logger

logger = get_logger(__name__)


class VideoIngestor:
    """Extracts audio from a video file and saves it as a WAV file.

    Parameters
    ----------
    video_path : str
        Path to the input video file.
    audio_path : str, optional
        Path where the extracted audio will be saved.  A temporary file
        is created if not provided.
    """

    def __init__(self, video_path: str, audio_path: Optional[str] = None) -> None:
        self.video_path = video_path
        self._audio_path: Optional[str] = None
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = None

        if not os.path.isfile(video_path):
            raise IngestionError(f"Video file not found: {video_path}", video_path=video_path)

        if audio_path:
            self._audio_path = audio_path
        else:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="video_babbel_")
            self._audio_path = os.path.join(self._temp_dir.name, "audio.wav")

        self._extract_audio()

    @classmethod
    def from_path(cls, video_path: str) -> "VideoIngestor":
        """Create a VideoIngestor from a video file path.

        Parameters
        ----------
        video_path : str
            Path to the video file.

        Returns
        -------
        VideoIngestor
            An instance ready for transcription.
        """
        return cls(video_path=video_path)

    def _extract_audio(self) -> None:
        """Extract audio from the video file using ffmpeg."""
        logger.info("Extracting audio from %s", self.video_path)
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-i", self.video_path,
                    "-vn",
                    "-acodec", "pcm_s16le",
                    "-ar", "16000",
                    "-ac", "1",
                    "-y",
                    self._audio_path,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info("Audio extraction complete: %s", self._audio_path)
        except subprocess.CalledProcessError as exc:
            raise IngestionError(
                f"ffmpeg failed: {exc.stderr.strip()}",
                video_path=self.video_path,
            ) from exc

    @property
    def audio_path(self) -> str:
        """Return the path to the extracted audio file."""
        if self._audio_path is None:
            raise IngestionError("Audio has not been extracted yet")
        return self._audio_path

    def cleanup(self) -> None:
        """Clean up temporary files."""
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None
            logger.debug("Cleaned up temporary directory")

    def __del__(self) -> None:
        """Ensure cleanup on garbage collection."""
        self.cleanup()
