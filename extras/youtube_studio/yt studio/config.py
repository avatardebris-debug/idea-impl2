"""Configuration for YouTube Studio."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class SEOConfig:
    """SEO configuration."""
    max_title_length: int = 60
    max_description_length: int = 5000
    max_keywords: int = 15
    max_tags: int = 500
    seo_score_threshold: int = 50
    title_length: int = 60
    keyword_count: int = 10


@dataclass
class AppConfig:
    """Application configuration."""
    seo: SEOConfig = field(default_factory=SEOConfig)
    debug: bool = False
    log_level: str = "INFO"


@dataclass
class YouTubeStudioConfig:
    """YouTube Studio specific configuration."""
    seo: SEOConfig = field(default_factory=SEOConfig)
    api_key: Optional[str] = None
    channel_id: Optional[str] = None
    default_category: str = "education"
    default_language: str = "en"
