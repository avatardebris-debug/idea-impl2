"""Configuration loader for ReviewPulse Aggregator.

Loads settings from a .env file (or config.example) and exposes them
as a Pydantic BaseSettings model.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file."""

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/reviewpulse"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Google Places API
    google_places_api_key: str = ""

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # Sync / rate-limit defaults
    google_places_default_delay: float = 1.0
    google_places_max_retries: int = 5

    # Yelp API
    yelp_api_key: str = ""
    yelp_api_secret: str = ""
    yelp_default_delay: float = 0.2
    yelp_max_retries: int = 5

    # Facebook Graph API
    facebook_app_id: str = ""
    facebook_app_secret: str = ""
    facebook_default_delay: float = 0.2
    facebook_max_retries: int = 5

    # LLM Configuration
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = ""
    llm_temperature: float = 0.7

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-haiku-20240307"

    # App
    app_name: str = "ReviewPulse Aggregator"
    debug: bool = False

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton settings instance
settings = Settings()
