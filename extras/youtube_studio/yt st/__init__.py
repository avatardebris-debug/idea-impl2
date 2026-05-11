"""YouTube Studio - A comprehensive tool for YouTube content optimization.

This package provides:
- SEO analysis and optimization
- Template management and rendering
- Video format handling
- Configuration management
"""

from .seo_analyzer import SEOAnalyzer
from .template_engine import TemplateEngine
from .template_manager import TemplateManager
from .video_format_handler import (
    VideoFormatHandler,
    FormatFactory,
    create_handler,
    detect_video_format,
    MP4Handler,
    AVIHandler,
    MOVHandler,
)
from .config import (
    SEOConfig,
    ChannelConfig,
    YouTubeStudioConfig,
)

__all__ = [
    'SEOAnalyzer',
    'TemplateEngine',
    'TemplateManager',
    'VideoFormatHandler',
    'FormatFactory',
    'create_handler',
    'detect_video_format',
    'MP4Handler',
    'AVIHandler',
    'MOVHandler',
    'SEOConfig',
    'ChannelConfig',
    'YouTubeStudioConfig',
]
