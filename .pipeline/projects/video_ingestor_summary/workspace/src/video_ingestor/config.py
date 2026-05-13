"""Configuration for the video ingestor system.

Loads settings from environment variables with sensible defaults.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env file if present
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


class Settings:
    """Application settings loaded from environment variables."""

    # Server
    HOST: str = os.getenv("VIDEO_INGESTOR_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("VIDEO_INGESTOR_PORT", "8000"))

    # Storage
    DATABASE_PATH: str = os.getenv(
        "VIDEO_INGESTOR_DB_PATH",
        str(Path(__file__).resolve().parent.parent.parent / "data" / "ingestor.db"),
    )

    # Temp files
    TEMP_DIR: str = os.getenv(
        "VIDEO_INGESTOR_TEMP_DIR",
        str(Path(__file__).resolve().parent.parent.parent / "data" / "temp"),
    )

    # Whisper
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
    WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    WHISPER_LANG: Optional[str] = os.getenv("WHISPER_LANG", None)

    # Ingestion
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("VIDEO_INGESTOR_MAX_UPLOAD_MB", "500"))
    ALLOWED_FORMATS: list[str] = [
        ext.lower() for ext in os.getenv(
            "VIDEO_INGESTOR_ALLOWED_FORMATS",
            "mp4,mov,avi,mkv",
        ).split(",")
    ]

    # HTTP
    DOWNLOAD_TIMEOUT: int = int(os.getenv("VIDEO_INGESTOR_DOWNLOAD_TIMEOUT", "120"))

    # Phase 2: Embedding
    EMBEDDING_MODEL: str = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/all-MiniLM-L6-v2",
    )
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "200"))
    CHUNK_OVERLAP_RATIO: float = float(os.getenv("CHUNK_OVERLAP_RATIO", "0.2"))

    # Phase 2: Vector store
    VECTOR_DB_PATH: str = os.getenv(
        "VECTOR_DB_PATH",
        str(Path(__file__).resolve().parent.parent.parent / "data" / "chroma.db"),
    )
    VECTOR_TOP_K: int = int(os.getenv("VECTOR_TOP_K", "5"))

    # Phase 2: LLM
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    @staticmethod
    def _has_cuda() -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False


settings = Settings()
