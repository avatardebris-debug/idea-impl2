"""Video ingestion pipeline: download, extract audio, transcribe."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import ffmpeg
import requests
import whisper

from .config import settings
from .storage import Storage


class IngestionError(Exception):
    """Raised when ingestion fails."""


class IngestionPipeline:
    """Orchestrates video download, audio extraction, and transcription."""

    def __init__(self, storage: Storage, model: Optional[whisper.Whisper] = None):
        self.storage = storage
        self.model = model
        self.temp_dir = Path(settings.TEMP_DIR)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def _ensure_model(self) -> whisper.Whisper:
        """Load or return the Whisper model."""
        if self.model is None:
            self.model = whisper.load_model(settings.WHISPER_MODEL)
        return self.model

    def download_video(self, url: str) -> str:
        """Download a video from a URL to a temp file. Returns the file path."""
        resp = requests.get(url, timeout=settings.DOWNLOAD_TIMEOUT, stream=True)
        resp.raise_for_status()

        # Determine extension from content-type or URL
        content_type = resp.headers.get("Content-Type", "")
        ext = "mp4"
        if "mp4" in content_type:
            ext = "mp4"
        elif "quicktime" in content_type or "mov" in content_type:
            ext = "mov"
        elif "avi" in content_type:
            ext = "avi"
        elif "x-matroska" in content_type or "mkv" in content_type:
            ext = "mkv"

        # Also try URL extension
        if "." in url.split("?")[0]:
            url_ext = url.split("?")[0].rsplit(".", 1)[-1].lower()
            if url_ext in ("mp4", "mov", "avi", "mkv", "webm", "flv", "wmv"):
                ext = url_ext

        fd, path = tempfile.mkstemp(suffix=f".{ext}", dir=self.temp_dir)
        os.close(fd)

        with open(path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        return path

    def extract_audio(self, video_path: str) -> str:
        """Extract audio from video file using ffmpeg. Returns audio file path."""
        audio_path = video_path.rsplit(".", 1)[0] + ".wav"

        try:
            ffmpeg.input(video_path).output(
                audio_path,
                acodec="pcm_s16le",
                ac=1,
                ar="16000",
                loglevel="error",
            ).run(overwrite_output=True)
        except ffmpeg.Error as e:
            raise IngestionError(f"ffmpeg extraction failed: {e.stderr.decode() if e.stderr else str(e)}")

        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            raise IngestionError("Extracted audio file is empty or missing")

        return audio_path

    def transcribe(self, audio_path: str) -> tuple[list[dict], str]:
        """Transcribe audio using Whisper. Returns (segments, full_text)."""
        model = self._ensure_model()
        result = model.transcribe(
            audio_path,
            language=settings.WHISPER_LANG,
            fp16=settings.WHISPER_DEVICE == "cuda",
        )
        segments = result.get("segments", [])
        full_text = result.get("text", "")
        return segments, full_text

    def ingest_from_file(self, video_path: str, metadata: Optional[dict] = None) -> str:
        """Full pipeline: extract audio -> transcribe -> store for a local file.

        Returns the job ID.
        """
        metadata = metadata or {}
        metadata["source_file"] = video_path

        # Create job
        job_id = self.storage.create_job(video_path=video_path, metadata=metadata)
        self.storage.update_job_status(job_id, "processing")

        audio_path = ""
        try:
            # Step 1: Extract audio
            audio_path = self.extract_audio(video_path)
            self.storage.update_job_status(job_id, "processing")

            # Step 2: Transcribe
            segments, full_text = self.transcribe(audio_path)

            # Step 3: Store result
            self.storage.update_job_transcript(
                job_id,
                transcript_json=json.dumps(segments),
                full_text=full_text,
            )

            return job_id

        except Exception as e:
            self.storage.update_job_status(job_id, "failed", error=str(e))
            raise IngestionError(f"Ingestion failed: {e}") from e

        finally:
            # Clean up temp files
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    pass

    def ingest_from_url(self, url: str, metadata: Optional[dict] = None) -> str:
        """Full pipeline: download -> extract audio -> transcribe -> store.

        Returns the job ID.
        """
        metadata = metadata or {}
        metadata["source_url"] = url

        # Create job
        job_id = self.storage.create_job(video_path="", metadata=metadata)
        self.storage.update_job_status(job_id, "processing")

        video_path = ""
        audio_path = ""
        try:
            # Step 1: Download
            video_path = self.download_video(url)
            self.storage.update_job_status(job_id, "processing")

            # Step 2: Extract audio
            audio_path = self.extract_audio(video_path)
            self.storage.update_job_status(job_id, "processing")

            # Step 3: Transcribe
            segments, full_text = self.transcribe(audio_path)

            # Step 4: Store result
            self.storage.update_job_transcript(
                job_id,
                transcript_json=json.dumps(segments),
                full_text=full_text,
            )

            return job_id

        except Exception as e:
            self.storage.update_job_status(job_id, "failed", error=str(e))
            raise IngestionError(f"Ingestion failed: {e}") from e

        finally:
            # Clean up temp files
            for path in (video_path, audio_path):
                if path and os.path.exists(path):
                    try:
                        os.remove(path)
                    except OSError:
                        pass
