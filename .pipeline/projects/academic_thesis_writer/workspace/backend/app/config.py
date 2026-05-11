"""Application configuration."""

from __future__ import annotations

import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    # LLM
    llm_provider: str = "openai"  # "openai" | "local"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    local_model_url: str = "http://localhost:8000/v1"
    local_model_name: str = "local-model"

    # Database
    db_path: str = str(Path(__file__).resolve().parent.parent / "data" / "thesis.db")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Citation
    default_citation_style: str = "apa"  # apa | mla | chicago | ieee

    # Generation
    max_tokens: int = 4096
    temperature: float = 0.7

    model_config = {"env_prefix": "THESIS_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
