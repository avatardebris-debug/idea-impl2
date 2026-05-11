"""YouTube Studio - Main module for YouTube video optimization.

This module provides a unified interface for generating all YouTube video
metadata including titles, descriptions, keywords, thumbnails, and transcripts.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime
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
from .title_generator import TitleGenerator, TitleGenerationResult
from .thumbnail_generator import ThumbnailGenerator, ThumbnailMetadata
from .keyword_generator import KeywordGenerator, KeywordResult
from .transcript_builder import TranscriptBuilder, TranscriptMetadata
from .description_builder import DescriptionBuilder, DescriptionResult


@dataclass
class VideoMetadata:
    """Complete video metadata result.
    
    Attributes:
        title: Generated video title.
        titles: List of alternative titles.
        description: Generated video description.
        keywords: List of generated keywords.
        thumbnail_suggestions: List of thumbnail suggestions.
        transcript: Generated transcript.
        generated_at: Generation timestamp.
    """
    title: str
    titles: List[TitleGenerationResult] = field(default_factory=list)
    description: DescriptionResult = None  # type: ignore
    keywords: List[KeywordResult] = field(default_factory=list)
    thumbnail_suggestions: List[ThumbnailMetadata] = field(default_factory=list)
    transcript: TranscriptMetadata = None  # type: ignore
    generated_at: datetime = field(default_factory=datetime.now)


class YouTubeStudio:
    """Main class for YouTube video optimization.
    
    This class provides a unified interface for generating all YouTube video
    metadata including titles, descriptions, keywords, thumbnails, and transcripts.
    
    Usage:
        studio = YouTubeStudio()
        metadata = studio.generate_metadata(
            content="Your video content description here",
            duration=600,
            topic="Python Tutorial"
        )
        print(metadata.title)
        print(metadata.description.full_description)
    """
    
    def __init__(self, config: Dict = None):
        """Initialize YouTube Studio.
        
        Args:
            config: Configuration dictionary. If None, uses default config.
        """
        self.config = config or get_config()
        
        # Initialize generators
        self.title_generator = TitleGenerator(
            max_length=self.config.get('max_title_length', 100)
        )
        self.thumbnail_generator = ThumbnailGenerator(
            width=self.config.get('thumbnail_width', DEFAULT_THUMBNAIL_WIDTH),
            height=self.config.get('thumbnail_height', DEFAULT_THUMBNAIL_HEIGHT),
            format=self.config.get('thumbnail_format', DEFAULT_THUMBNAIL_FORMAT),
        )
        self.keyword_generator = KeywordGenerator(
            min_keywords=self.config.get('min_keywords', MIN_NUMBER_OF_KEYWORDS),
            max_keywords=self.config.get('max_keywords', MAX_NUMBER_OF_KEYWORDS),
        )
        self.transcript_builder = TranscriptBuilder(
            reading_speed=self.config.get('reading_speed', 200)
        )
        self.description_builder = DescriptionBuilder()
    
    def generate_metadata(self, content: str, topic: str = None,
                         duration: float = DEFAULT_VIDEO_DURATION,
                         language: str = DEFAULT_LANGUAGE,
                         category: str = DEFAULT_CATEGORY,
                         num_titles: int = DEFAULT_NUMBER_OF_TITLES,
                         num_keywords: int = DEFAULT_NUMBER_OF_KEYWORDS,
                         num_thumbnails: int = DEFAULT_NUMBER_OF_THUMBNAILS,
                         chapters: List[str] = None,
                         links: List[str] = None,
                         hashtags: List[str] = None) -> VideoMetadata:
        """Generate complete video metadata.
        
        This is the main entry point for generating all YouTube video metadata.
        
        Args:
            content: Video content description.
            topic: Main topic of the video. If None, extracted from content.
            duration: Video duration in seconds.
            language: Language code.
            category: Video category.
            num_titles: Number of title options to generate.
            num_keywords: Number of keywords to generate.
            num_thumbnails: Number of thumbnail suggestions.
            chapters: List of chapter titles.
            links: List of links to include.
            hashtags: List of hashtags.
            
        Returns:
            VideoMetadata object with all generated metadata.
        """
        # Extract topic if not provided
        if not topic:
            topic = self._extract_topic(content)
        
        # Generate titles
        titles = self.title_generator.generate_titles(content, num_titles)
        best_title = titles[0] if titles else TitleGenerationResult(
            title=f'How to {topic}',
            confidence=0.5,
            style='BOLD_TEXT',
        )
        
        # Generate description
        description = self.description_builder.build_description(
            topic=topic,
            chapters=chapters,
            links=links,
            hashtags=hashtags,
            category=category,
        )
        
        # Generate keywords
        keywords = self.keyword_generator.generate_keywords(content, num_keywords)
        
        # Generate thumbnail suggestions
        thumbnail_suggestions = self.thumbnail_generator.generate_suggestions(
            content=content,
            topic=topic,
            num_suggestions=num_thumbnails,
        )
        
        # Generate transcript
        transcript = self.transcript_builder.build_transcript(
            content=content,
            duration=duration,
            language=language,
        )
        
        return VideoMetadata(
            title=best_title.title,
            titles=titles,
            description=description,
            keywords=keywords,
            thumbnail_suggestions=thumbnail_suggestions,
            transcript=transcript,
        )
    
    def generate_titles(self, content: str, num_titles: int = DEFAULT_NUMBER_OF_TITLES) -> List[TitleGenerationResult]:
        """Generate video titles.
        
        Args:
            content: Video content description.
            num_titles: Number of titles to generate.
            
        Returns:
            List of TitleGenerationResult objects.
        """
        return self.title_generator.generate_titles(content, num_titles)
    
    def generate_description(self, topic: str, chapters: List[str] = None,
                           links: List[str] = None, hashtags: List[str] = None,
                           category: str = DEFAULT_CATEGORY) -> DescriptionResult:
        """Generate video description.
        
        Args:
            topic: Main topic of the video.
            chapters: List of chapter titles.
            links: List of links to include.
            hashtags: List of hashtags.
            category: Video category.
            
        Returns:
            DescriptionResult object.
        """
        return self.description_builder.build_description(
            topic=topic,
            chapters=chapters,
            links=links,
            hashtags=hashtags,
            category=category,
        )
    
    def generate_keywords(self, content: str, num_keywords: int = DEFAULT_NUMBER_OF_KEYWORDS) -> List[KeywordResult]:
        """Generate video keywords.
        
        Args:
            content: Video content description.
            num_keywords: Number of keywords to generate.
            
        Returns:
            List of KeywordResult objects.
        """
        return self.keyword_generator.generate_keywords(content, num_keywords)
    
    def generate_thumbnail_suggestions(self, content: str, topic: str = None,
                                      num_suggestions: int = DEFAULT_NUMBER_OF_THUMBNAILS) -> List[ThumbnailMetadata]:
        """Generate thumbnail suggestions.
        
        Args:
            content: Video content description.
            topic: Main topic of the video.
            num_suggestions: Number of suggestions to generate.
            
        Returns:
            List of ThumbnailMetadata objects.
        """
        if not topic:
            topic = self._extract_topic(content)
        return self.thumbnail_generator.generate_suggestions(
            content=content,
            topic=topic,
            num_suggestions=num_suggestions,
        )
    
    def generate_transcript(self, content: str, duration: float = DEFAULT_VIDEO_DURATION,
                          language: str = DEFAULT_LANGUAGE) -> TranscriptMetadata:
        """Generate video transcript.
        
        Args:
            content: Video content description.
            duration: Video duration in seconds.
            language: Language code.
            
        Returns:
            TranscriptMetadata object.
        """
        return self.transcript_builder.build_transcript(
            content=content,
            duration=duration,
            language=language,
        )
    
    def _extract_topic(self, content: str) -> str:
        """Extract topic from content.
        
        Args:
            content: Video content description.
            
        Returns:
            Extracted topic string.
        """
        # Simple topic extraction: first meaningful phrase
        words = content.split()
        topic_words = []
        
        for word in words:
            word = word.strip('.,!?;:()[]{}\'"')
            if word and len(word) > 2:
                topic_words.append(word)
                if len(topic_words) >= 3:
                    break
        
        return ' '.join(topic_words).title() if topic_words else 'Video'
