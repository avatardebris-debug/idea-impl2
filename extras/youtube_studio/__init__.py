"""YouTube Studio - YouTube video optimization toolkit.

This package provides tools for generating optimized YouTube video metadata
including titles, descriptions, keywords, thumbnails, and transcripts.

Usage:
    from youtube_studio import YouTubeStudio
    
    studio = YouTubeStudio()
    metadata = studio.generate_metadata(
        content="Your video content description",
        topic="Python Tutorial",
        duration=600
    )
    print(metadata.title)
    print(metadata.description.full_description)
"""

from .youtube_studio import YouTubeStudio, VideoMetadata
from .title_generator import TitleGenerator, TitleGenerationResult
from .thumbnail_generator import ThumbnailGenerator, ThumbnailMetadata, ThumbnailStyle
from .keyword_generator import KeywordGenerator, KeywordResult, KeywordPriority
from .transcript_builder import TranscriptBuilder, TranscriptMetadata, TranscriptSection
from .description_builder import DescriptionBuilder, DescriptionResult, DescriptionSection
from .config import get_config
from .constants import (
    DEFAULT_VIDEO_DURATION,
    DEFAULT_LANGUAGE,
    DEFAULT_CATEGORY,
    DEFAULT_THUMBNAIL_WIDTH,
    DEFAULT_THUMBNAIL_HEIGHT,
    DEFAULT_THUMBNAIL_FORMAT,
    MIN_NUMBER_OF_KEYWORDS,
    MAX_NUMBER_OF_KEYWORDS,
    DEFAULT_NUMBER_OF_TITLES,
    DEFAULT_NUMBER_OF_KEYWORDS,
    DEFAULT_NUMBER_OF_THUMBNAILS,
)

__all__ = [
    # Main class
    'YouTubeStudio',
    'VideoMetadata',
    
    # Title generation
    'TitleGenerator',
    'TitleGenerationResult',
    
    # Thumbnail generation
    'ThumbnailGenerator',
    'ThumbnailMetadata',
    'ThumbnailStyle',
    
    # Keyword generation
    'KeywordGenerator',
    'KeywordResult',
    'KeywordPriority',
    
    # Transcript building
    'TranscriptBuilder',
    'TranscriptMetadata',
    'TranscriptSection',
    
    # Description building
    'DescriptionBuilder',
    'DescriptionResult',
    'DescriptionSection',
    
    # Config
    'get_config',
    
    # Constants
    'DEFAULT_VIDEO_DURATION',
    'DEFAULT_LANGUAGE',
    'DEFAULT_CATEGORY',
    'DEFAULT_THUMBNAIL_WIDTH',
    'DEFAULT_THUMBNAIL_HEIGHT',
    'DEFAULT_THUMBNAIL_FORMAT',
    'MIN_NUMBER_OF_KEYWORDS',
    'MAX_NUMBER_OF_KEYWORDS',
    'DEFAULT_NUMBER_OF_TITLES',
    'DEFAULT_NUMBER_OF_KEYWORDS',
    'DEFAULT_NUMBER_OF_THUMBNAILS',
]

__version__ = '1.0.0'
