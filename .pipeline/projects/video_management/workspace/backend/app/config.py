"""Application configuration from environment variables."""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # YouTube OAuth
    google_client_id: str = os.environ.get("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.environ.get(
        "GOOGLE_REDIRECT_URI", "http://localhost:8000/api/youtube/callback"
    )

    # Database
    database_url: str = os.environ.get(
        "DATABASE_URL", "sqlite:///./video_management.db"
    )

    # Scheduler
    stats_refresh_interval_minutes: int = int(
        os.environ.get("STATS_REFRESH_INTERVAL_MINUTES", "15")
    )

    class Config:
        env_file = ".env"


settings = Settings()
