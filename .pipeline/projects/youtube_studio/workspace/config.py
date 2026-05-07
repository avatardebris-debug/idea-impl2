"""
YouTube Studio - Configuration Module

This module provides centralized configuration management for the YouTube Studio application.
All settings related to video formats, templates, and API endpoints are defined here.
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class VideoFormatConfig:
    """Configuration for video format handling"""
    supported_formats: List[str] = field(default_factory=lambda: ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'wmv'])
    preferred_format: str = 'mp4'
    default_codec: str = 'h264'
    audio_codec: str = 'aac'
    max_duration_seconds: int = 12 * 60 * 60  # 12 hours
    min_duration_seconds: int = 0


@dataclass
class ThumbnailConfig:
    """Configuration for thumbnail generation"""
    max_size_bytes: int = 2 * 1024 * 1024  # 2MB
    min_width: int = 1280
    min_height: int = 720
    max_width: int = 1280
    max_height: int = 720
    aspect_ratio: tuple = (16, 9)
    default_style: str = 'modern'


@dataclass
class KeywordConfig:
    """Configuration for keyword generation"""
    min_keywords: int = 10
    max_keywords: int = 500  # Character limit
    max_words_per_tag: int = 3
    min_relevance_score: float = 0.5
    default_priority: str = 'medium'


@dataclass
class TitleConfig:
    """Configuration for title generation"""
    max_length: int = 100
    min_length: int = 10
    seo_weight: float = 0.7
    engagement_weight: float = 0.3


@dataclass
class TemplateConfig:
    """Configuration for template management"""
    version: str = '1.0.0'
    variable_prefix: str = '{{'
    variable_suffix: str = '}}'
    default_template_path: str = 'templates/default_template.json'


@dataclass
class APIConfig:
    """Configuration for API endpoints"""
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: int = 1
    endpoints: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExportConfig:
    """Configuration for export functionality"""
    export_directory: str = 'exports'
    filename_template: str = '{video_id}_{timestamp}'
    date_format: str = '%Y%m%d_%H%M%S'
    pretty_json: bool = True
    supported_formats: List[str] = field(default_factory=lambda: ['json', 'yaml', 'txt', 'srt', 'vtt'])


@dataclass
class FileConfig:
    """Configuration for file handling"""
    max_file_size_bytes: int = 100 * 1024 * 1024  # 100MB
    supported_import_formats: List[str] = field(default_factory=lambda: ['txt', 'srt', 'vtt', 'json', 'yaml', 'yml'])
    default_encoding: str = 'utf-8'


@dataclass
class OutputConfig:
    """Configuration for output formatting"""
    precision_seconds: int = 2
    timestamp_format: str = '%H:%M:%S'
    transcript_line_width: int = 80


@dataclass
class SEOConfig:
    """Configuration for SEO-related settings"""
    max_title_length: int = 100
    max_description_length: int = 5000
    max_tags: int = 15
    max_tag_length: int = 500
    default_priority: str = 'medium'
    min_relevance_score: float = 0.5
    keyword_density_target: float = 0.02


class YouTubeStudioConfig:
    """
    Main configuration class for YouTube Studio.
    
    This class provides centralized access to all configuration settings
    through a single interface. It supports both programmatic configuration
    and loading from environment variables.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the YouTube Studio configuration.
        
        Args:
            config_dir: Optional directory path for configuration files
        """
        self._config_dir = config_dir or os.getcwd()
        
        # Initialize all configuration sections
        self.video_formats = VideoFormatConfig()
        self.thumbnails = ThumbnailConfig()
        self.keywords = KeywordConfig()
        self.titles = TitleConfig()
        self.templates = TemplateConfig()
        self.api = APIConfig()
        self.export = ExportConfig()
        self.files = FileConfig()
        self.output = OutputConfig()
        
        # Load environment-specific settings if available
        self._load_env_settings()
    
    def _load_env_settings(self):
        """Load settings from environment variables"""
        # Video formats
        env_formats = os.environ.get('YOUTUBE_STUDIO_FORMATS')
        if env_formats:
            self.video_formats.supported_formats = env_formats.split(',')
        
        # Preferred format
        env_format = os.environ.get('YOUTUBE_STUDIO_PREFERRED_FORMAT')
        if env_format:
            self.video_formats.preferred_format = env_format
        
        # API settings
        env_timeout = os.environ.get('YOUTUBE_STUDIO_API_TIMEOUT')
        if env_timeout:
            try:
                self.api.timeout_seconds = int(env_timeout)
            except ValueError:
                pass
        
        # Export directory
        env_export_dir = os.environ.get('YOUTUBE_STUDIO_EXPORT_DIR')
        if env_export_dir:
            self.export.export_directory = env_export_dir
    
    def get_video_format_config(self) -> VideoFormatConfig:
        """Get video format configuration"""
        return self.video_formats
    
    def get_thumbnail_config(self) -> ThumbnailConfig:
        """Get thumbnail configuration"""
        return self.thumbnails
    
    def get_keyword_config(self) -> KeywordConfig:
        """Get keyword configuration"""
        return self.keywords
    
    def get_title_config(self) -> TitleConfig:
        """Get title configuration"""
        return self.titles
    
    def get_template_config(self) -> TemplateConfig:
        """Get template configuration"""
        return self.templates
    
    def get_api_config(self) -> APIConfig:
        """Get API configuration"""
        return self.api
    
    def get_export_config(self) -> ExportConfig:
        """Get export configuration"""
        return self.export
    
    def get_file_config(self) -> FileConfig:
        """Get file handling configuration"""
        return self.files
    
    def get_output_config(self) -> OutputConfig:
        """Get output formatting configuration"""
        return self.output
    
    def get_all_config(self) -> Dict[str, any]:
        """Get all configuration as a dictionary"""
        return {
            'video_formats': {
                'supported_formats': self.video_formats.supported_formats,
                'preferred_format': self.video_formats.preferred_format,
                'default_codec': self.video_formats.default_codec,
                'audio_codec': self.video_formats.audio_codec,
                'max_duration_seconds': self.video_formats.max_duration_seconds,
                'min_duration_seconds': self.video_formats.min_duration_seconds,
            },
            'thumbnails': {
                'max_size_bytes': self.thumbnails.max_size_bytes,
                'min_width': self.thumbnails.min_width,
                'min_height': self.thumbnails.min_height,
                'max_width': self.thumbnails.max_width,
                'max_height': self.thumbnails.max_height,
                'aspect_ratio': self.thumbnails.aspect_ratio,
                'default_style': self.thumbnails.default_style,
            },
            'keywords': {
                'min_keywords': self.keywords.min_keywords,
                'max_keywords': self.keywords.max_keywords,
                'max_words_per_tag': self.keywords.max_words_per_tag,
                'min_relevance_score': self.keywords.min_relevance_score,
                'default_priority': self.keywords.default_priority,
            },
            'titles': {
                'max_length': self.titles.max_length,
                'min_length': self.titles.min_length,
                'seo_weight': self.titles.seo_weight,
                'engagement_weight': self.titles.engagement_weight,
            },
            'templates': {
                'version': self.templates.version,
                'variable_prefix': self.templates.variable_prefix,
                'variable_suffix': self.templates.variable_suffix,
                'default_template_path': self.templates.default_template_path,
            },
            'api': {
                'timeout_seconds': self.api.timeout_seconds,
                'retry_attempts': self.api.retry_attempts,
                'retry_delay_seconds': self.api.retry_delay_seconds,
                'endpoints': self.api.endpoints,
            },
            'export': {
                'export_directory': self.export.export_directory,
                'filename_template': self.export.filename_template,
                'date_format': self.export.date_format,
                'pretty_json': self.export.pretty_json,
                'supported_formats': self.export.supported_formats,
            },
            'files': {
                'max_file_size_bytes': self.files.max_file_size_bytes,
                'supported_import_formats': self.files.supported_import_formats,
                'default_encoding': self.files.default_encoding,
            },
            'output': {
                'precision_seconds': self.output.precision_seconds,
                'timestamp_format': self.output.timestamp_format,
                'transcript_line_width': self.output.transcript_line_width,
            },
        }
    
    def validate_config(self) -> bool:
        """
        Validate the current configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        # Check video format settings
        if not self.video_formats.preferred_format in self.video_formats.supported_formats:
            return False
        
        # Check thumbnail dimensions
        if self.thumbnails.min_width > self.thumbnails.max_width:
            return False
        if self.thumbnails.min_height > self.thumbnails.max_height:
            return False
        
        # Check keyword limits
        if self.keywords.min_keywords < 1:
            return False
        if self.keywords.max_keywords <= self.keywords.min_keywords:
            return False
        
        # Check title limits
        if self.titles.max_length <= self.titles.min_length:
            return False
        
        # Check file size limits
        if self.files.max_file_size_bytes <= 0:
            return False
        
        return True


# Global configuration instance
_config_instance: Optional[YouTubeStudioConfig] = None


def get_config() -> YouTubeStudioConfig:
    """
    Get the global configuration instance.
    
    Returns:
        YouTubeStudioConfig: The global configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = YouTubeStudioConfig()
    return _config_instance


def reset_config():
    """Reset the global configuration instance"""
    global _config_instance
    _config_instance = None


def set_config(config: YouTubeStudioConfig):
    """
    Set the global configuration instance.
    
    Args:
        config: The configuration instance to use
    """
    global _config_instance
    _config_instance = config


# Convenience functions for accessing common settings
def get_supported_formats() -> List[str]:
    """Get list of supported video formats"""
    return get_config().video_formats.supported_formats


def get_preferred_format() -> str:
    """Get preferred video format"""
    return get_config().video_formats.preferred_format


def get_max_title_length() -> int:
    """Get maximum title length"""
    return get_config().titles.max_length


def get_max_keyword_chars() -> int:
    """Get maximum keyword character count"""
    return get_config().keywords.max_keywords


def get_max_thumbnail_size() -> int:
    """Get maximum thumbnail file size in bytes"""
    return get_config().thumbnails.max_size_bytes
