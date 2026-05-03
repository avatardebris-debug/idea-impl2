"""Configuration dataclass for API keys, endpoints, RSS metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TwitterConfig:
    """Twitter/X API configuration."""
    api_key: str = ""
    api_secret: str = ""
    access_token: str = ""
    access_token_secret: str = ""
    mock: bool = True


@dataclass
class LinkedInConfig:
    """LinkedIn API configuration."""
    access_token: str = ""
    mock: bool = True


@dataclass
class RSSConfig:
    """RSS feed configuration."""
    feed_path: str = "output/rss/feed.xml"
    site_name: str = "Scott Adams Bot"
    site_url: str = "https://example.com"
    description: str = "AI-generated content in Scott Adams' style"
    mock: bool = True


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""
    api_key: str = ""
    model: str = "gpt-4o"
    base_url: Optional[str] = None


@dataclass
class Config:
    """Top-level configuration for the sacbot pipeline."""
    twitter: TwitterConfig = field(default_factory=TwitterConfig)
    linkedin: LinkedInConfig = field(default_factory=LinkedInConfig)
    rss: RSSConfig = field(default_factory=RSSConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    scheduler_interval_seconds: float = 14400.0  # 4 hours
    style_threshold: float = 0.8
    default_content_type: str = "blog"
    topics_path: str = "sacbot/topics.json"
    corpus_path: Optional[str] = None
    n_few_shot: int = 3
    temperature: float = 0.7
    output_dir: str = "output"
    log_level: str = "INFO"
    extra_headers: Dict[str, str] = field(default_factory=dict)
    proxy: Optional[str] = None

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        import os
        return cls(
            twitter=TwitterConfig(
                api_key=os.environ.get("TWITTER_API_KEY", ""),
                api_secret=os.environ.get("TWITTER_API_SECRET", ""),
                access_token=os.environ.get("TWITTER_ACCESS_TOKEN", ""),
                access_token_secret=os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", ""),
                mock=os.environ.get("TWITTER_MOCK", "true").lower() == "true",
            ),
            linkedin=LinkedInConfig(
                access_token=os.environ.get("LINKEDIN_ACCESS_TOKEN", ""),
                mock=os.environ.get("LINKEDIN_MOCK", "true").lower() == "true",
            ),
            rss=RSSConfig(
                feed_path=os.environ.get("RSS_FEED_PATH", "output/rss/feed.xml"),
                mock=os.environ.get("RSS_MOCK", "true").lower() == "true",
            ),
            openai=OpenAIConfig(
                api_key=os.environ.get("OPENAI_API_KEY", ""),
                model=os.environ.get("OPENAI_MODEL", "gpt-4o"),
                base_url=os.environ.get("OPENAI_BASE_URL"),
            ),
            scheduler_interval_seconds=float(os.environ.get("SCHEDULER_INTERVAL", "14400")),
            style_threshold=float(os.environ.get("STYLE_THRESHOLD", "0.8")),
            temperature=float(os.environ.get("TEMPERATURE", "0.7")),
            output_dir=os.environ.get("OUTPUT_DIR", "output"),
        )

    @classmethod
    def from_dict(cls, data: Dict) -> "Config":
        """Load configuration from a dictionary."""
        twitter_data = data.get("twitter", {})
        linkedin_data = data.get("linkedin", {})
        rss_data = data.get("rss", {})
        openai_data = data.get("openai", {})

        return cls(
            twitter=TwitterConfig(**twitter_data),
            linkedin=LinkedInConfig(**linkedin_data),
            rss=RSSConfig(**rss_data),
            openai=OpenAIConfig(**openai_data),
            scheduler_interval_seconds=data.get("scheduler_interval_seconds", 14400.0),
            style_threshold=data.get("style_threshold", 0.8),
            default_content_type=data.get("default_content_type", "blog"),
            topics_path=data.get("topics_path", "sacbot/topics.json"),
            corpus_path=data.get("corpus_path"),
            n_few_shot=data.get("n_few_shot", 3),
            temperature=data.get("temperature", 0.7),
            output_dir=data.get("output_dir", "output"),
            log_level=data.get("log_level", "INFO"),
            extra_headers=data.get("extra_headers", {}),
            proxy=data.get("proxy"),
        )
