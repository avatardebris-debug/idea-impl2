"""Configuration management for YouTube Studio."""

from dataclasses import dataclass, field
from typing import Optional
from .constants import (
    MAX_TITLE_LENGTH,
    MIN_NUMBER_OF_KEYWORDS,
    MAX_NUMBER_OF_KEYWORDS,
    DEFAULT_THUMBNAIL_WIDTH,
    DEFAULT_THUMBNAIL_HEIGHT,
    TEMPLATE_DIR,
)


@dataclass
class TitleConfig:
    """Configuration for title generation."""
    max_length: int = MAX_TITLE_LENGTH
    min_length: int = 10
    style_weights: dict = field(default_factory=lambda: {
        'clickworthy': 0.3,
        'descriptive': 0.3,
        'question': 0.2,
        'howto': 0.2,
    })


@dataclass
class ThumbnailConfig:
    """Configuration for thumbnail generation."""
    width: int = DEFAULT_THUMBNAIL_WIDTH
    height: int = DEFAULT_THUMBNAIL_HEIGHT
    format: str = 'png'
    num_suggestions: int = 3
    styles: list = field(default_factory=lambda: [
        'bold_text',
        'split_screen',
        'close_up',
        'minimal',
        'action_shot',
    ])


@dataclass
class KeywordConfig:
    """Configuration for keyword generation."""
    min_keywords: int = MIN_NUMBER_OF_KEYWORDS
    max_keywords: int = MAX_NUMBER_OF_KEYWORDS
    priority_levels: list = field(default_factory=lambda: [
        'high',
        'medium',
        'low',
    ])


@dataclass
class ExportConfig:
    """Configuration for metadata export."""
    default_format: str = 'json'
    output_directory: str = 'output'
    include_timestamp: bool = True


@dataclass
class StudioConfig:
    """Main configuration for YouTube Studio."""
    title: TitleConfig = field(default_factory=TitleConfig)
    thumbnail: ThumbnailConfig = field(default_factory=ThumbnailConfig)
    keyword: KeywordConfig = field(default_factory=KeywordConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    template_directory: str = TEMPLATE_DIR

    def get_title_config(self) -> TitleConfig:
        """Get title configuration."""
        return self.title

    def get_thumbnail_config(self) -> ThumbnailConfig:
        """Get thumbnail configuration."""
        return self.thumbnail

    def get_keyword_config(self) -> KeywordConfig:
        """Get keyword configuration."""
        return self.keyword

    def get_export_config(self) -> ExportConfig:
        """Get export configuration."""
        return self.export


# Module-level singleton
_config: Optional[StudioConfig] = None


def get_config() -> StudioConfig:
    """Get the global configuration singleton."""
    global _config
    if _config is None:
        _config = StudioConfig()
    return _config


def set_config(config: StudioConfig) -> None:
    """Set the global configuration."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset the global configuration to defaults."""
    global _config
    _config = None
