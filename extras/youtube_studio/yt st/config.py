"""Configuration for YouTube Studio.

This module provides configuration management for YouTube Studio,
including SEO settings and channel preferences.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SEOConfig:
    """SEO configuration settings."""
    
    max_title_length: int = 100
    max_description_length: int = 5000
    max_keywords: int = 15
    min_keyword_length: int = 3
    max_keyword_length: int = 50
    keyword_relevance_threshold: float = 0.3
    title_optimization_weight: float = 0.4
    description_optimization_weight: float = 0.3
    keyword_optimization_weight: float = 0.3
    
    def validate_title_length(self, title: str) -> bool:
        """Validate title length against configuration."""
        return len(title) <= self.max_title_length
    
    def validate_description_length(self, description: str) -> bool:
        """Validate description length against configuration."""
        return len(description) <= self.max_description_length
    
    def validate_keyword(self, keyword: str) -> bool:
        """Validate a keyword against configuration."""
        if not keyword or not keyword.strip():
            return False
        keyword = keyword.strip()
        return (self.min_keyword_length <= len(keyword) <= self.max_keyword_length)


@dataclass
class ChannelConfig:
    """Channel configuration settings."""
    
    channel_name: str = "My Channel"
    channel_description: str = ""
    channel_keywords: List[str] = field(default_factory=list)
    channel_avatar_url: str = ""
    channel_banner_url: str = ""
    channel_language: str = "en"
    channel_country: str = "US"
    
    def add_keyword(self, keyword: str) -> bool:
        """Add a keyword to the channel."""
        if keyword and keyword not in self.channel_keywords:
            self.channel_keywords.append(keyword)
            return True
        return False
    
    def remove_keyword(self, keyword: str) -> bool:
        """Remove a keyword from the channel."""
        if keyword in self.channel_keywords:
            self.channel_keywords.remove(keyword)
            return True
        return False


@dataclass
class YouTubeStudioConfig:
    """Main YouTube Studio configuration."""
    
    seo: SEOConfig = field(default_factory=SEOConfig)
    channel: ChannelConfig = field(default_factory=ChannelConfig)
    
    # General settings
    auto_generate_keywords: bool = True
    auto_optimize_titles: bool = True
    auto_generate_descriptions: bool = True
    default_video_category: str = "Education"
    default_video_language: str = "en"
    
    # Thumbnail settings
    thumbnail_style: str = "bold"
    thumbnail_size: str = "large"
    thumbnail_color_scheme: str = "auto"
    
    # Output settings
    output_format: str = "json"
    output_directory: str = "./output"
    backup_enabled: bool = True
    
    def update_seo_config(self, **kwargs) -> None:
        """Update SEO configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self.seo, key):
                setattr(self.seo, key, value)
    
    def update_channel_config(self, **kwargs) -> None:
        """Update channel configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self.channel, key):
                setattr(self.channel, key, value)
    
    def validate_config(self) -> Dict[str, List[str]]:
        """Validate the entire configuration.
        
        Returns:
            Dictionary of validation errors by category
        """
        errors = {}
        
        # Validate SEO config
        if self.seo.max_title_length <= 0:
            errors.setdefault('seo', []).append("max_title_length must be positive")
        if self.seo.max_description_length <= 0:
            errors.setdefault('seo', []).append("max_description_length must be positive")
        if self.seo.max_keywords <= 0:
            errors.setdefault('seo', []).append("max_keywords must be positive")
        if self.seo.min_keyword_length <= 0:
            errors.setdefault('seo', []).append("min_keyword_length must be positive")
        if self.seo.max_keyword_length <= self.seo.min_keyword_length:
            errors.setdefault('seo', []).append("max_keyword_length must be greater than min_keyword_length")
        
        # Validate channel config
        if not self.channel.channel_name or not self.channel.channel_name.strip():
            errors.setdefault('channel', []).append("channel_name cannot be empty")
        
        # Validate general settings
        if self.default_video_category not in [
            "Film & Animation", "Autos & Vehicles", "Music", "Pets & Animals",
            "Sports", "Gaming", "People & Blogs", "Comedy", "Entertainment",
            "News & Politics", "Howto & Style", "Education", "Science & Technology",
            "Nonprofits & Activism"
        ]:
            errors.setdefault('general', []).append("Invalid default_video_category")
        
        return errors
    
    def to_dict(self) -> Dict[str, object]:
        """Convert configuration to dictionary."""
        return {
            'seo': {
                'max_title_length': self.seo.max_title_length,
                'max_description_length': self.seo.max_description_length,
                'max_keywords': self.seo.max_keywords,
                'min_keyword_length': self.seo.min_keyword_length,
                'max_keyword_length': self.seo.max_keyword_length,
                'keyword_relevance_threshold': self.seo.keyword_relevance_threshold,
                'title_optimization_weight': self.seo.title_optimization_weight,
                'description_optimization_weight': self.seo.description_optimization_weight,
                'keyword_optimization_weight': self.seo.keyword_optimization_weight,
            },
            'channel': {
                'channel_name': self.channel.channel_name,
                'channel_description': self.channel.channel_description,
                'channel_keywords': self.channel.channel_keywords,
                'channel_avatar_url': self.channel.channel_avatar_url,
                'channel_banner_url': self.channel.channel_banner_url,
                'channel_language': self.channel.channel_language,
                'channel_country': self.channel.channel_country,
            },
            'auto_generate_keywords': self.auto_generate_keywords,
            'auto_optimize_titles': self.auto_optimize_titles,
            'auto_generate_descriptions': self.auto_generate_descriptions,
            'default_video_category': self.default_video_category,
            'default_video_language': self.default_video_language,
            'thumbnail_style': self.thumbnail_style,
            'thumbnail_size': self.thumbnail_size,
            'thumbnail_color_scheme': self.thumbnail_color_scheme,
            'output_format': self.output_format,
            'output_directory': self.output_directory,
            'backup_enabled': self.backup_enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> 'YouTubeStudioConfig':
        """Create configuration from dictionary."""
        config = cls()
        
        if 'seo' in data:
            seo_data = data['seo']
            config.update_seo_config(**{k: v for k, v in seo_data.items() if hasattr(config.seo, k)})
        
        if 'channel' in data:
            channel_data = data['channel']
            config.update_channel_config(**{k: v for k, v in channel_data.items() if hasattr(config.channel, k)})
        
        # Update general settings
        for key in ['auto_generate_keywords', 'auto_optimize_titles', 'auto_generate_descriptions',
                    'default_video_category', 'default_video_language', 'thumbnail_style',
                    'thumbnail_size', 'thumbnail_color_scheme', 'output_format',
                    'output_directory', 'backup_enabled']:
            if key in data:
                setattr(config, key, data[key])
        
        return config