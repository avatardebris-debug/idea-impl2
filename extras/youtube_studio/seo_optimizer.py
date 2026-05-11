"""SEO Optimizer for YouTube Studio.

This module provides a unified interface for generating optimized
video metadata including titles, keywords, descriptions, and thumbnails.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

from .title_generator import TitleGenerator, TitleGenerationResult
from .keyword_generator import KeywordGenerator, KeywordResult
from .description_builder import DescriptionBuilder, DescriptionResult
from .thumbnail_generator import ThumbnailGenerator, ThumbnailMetadata
from .config import get_config


@dataclass
class VideoMetadata:
    """Complete video metadata package.
    
    Attributes:
        title: Optimized video title.
        titles: List of alternative title options.
        keywords: List of optimized keywords.
        description: Optimized video description.
        thumbnail_suggestions: List of thumbnail metadata suggestions.
        generated_at: Generation timestamp.
    """
    title: str
    titles: List[TitleGenerationResult]
    keywords: List[KeywordResult]
    description: DescriptionResult
    thumbnail_suggestions: List[ThumbnailMetadata]
    generated_at: datetime = field(default_factory=datetime.now)


class SEOOptimizer:
    """Unified SEO optimizer for YouTube video metadata.
    
    This class coordinates title generation, keyword extraction,
    description building, and thumbnail suggestions to produce
    complete, optimized video metadata.
    """
    
    def __init__(self, max_title_length: int = 100,
                 num_titles: int = 5,
                 num_keywords: int = 15,
                 num_thumbnails: int = 3):
        """Initialize SEO optimizer.
        
        Args:
            max_title_length: Maximum title length in characters.
            num_titles: Number of title options to generate.
            num_keywords: Number of keywords to generate.
            num_thumbnails: Number of thumbnail suggestions to generate.
        """
        self.title_generator = TitleGenerator(max_length=max_title_length)
        self.keyword_generator = KeywordGenerator()
        self.description_builder = DescriptionBuilder()
        self.thumbnail_generator = ThumbnailGenerator()
        self.num_titles = num_titles
        self.num_keywords = num_keywords
        self.num_thumbnails = num_thumbnails
    
    def optimize(self, content: str, topic: str = None,
                 chapters: List[str] = None,
                 links: List[str] = None,
                 hashtags: List[str] = None,
                 category: str = 'Education') -> VideoMetadata:
        """Generate complete optimized video metadata.
        
        Args:
            content: Video content description.
            topic: Main topic of the video (optional, extracted from content if not provided).
            chapters: List of chapter titles.
            links: List of links to include.
            hashtags: List of hashtags.
            category: Video category.
            
        Returns:
            VideoMetadata with all optimized metadata.
        """
        # Use provided topic or extract from content
        if not topic:
            topics = self.title_generator._extract_topics(content)
            topic = topics[0].capitalize() if topics else 'Video'
        
        # Generate titles
        titles = self.title_generator.generate_multiple_titles(content, self.num_titles)
        best_title = titles[0].title if titles else 'Untitled Video'
        
        # Generate keywords
        keywords = self.keyword_generator.generate_keywords(content, self.num_keywords)
        
        # Build description
        description = self.description_builder.build_description(
            topic=topic,
            chapters=chapters,
            links=links,
            hashtags=hashtags,
            category=category,
        )
        
        # Generate thumbnail suggestions
        thumbnail_suggestions = self.thumbnail_generator.generate_suggestions(
            content, self.num_thumbnails
        )
        
        return VideoMetadata(
            title=best_title,
            titles=titles,
            keywords=keywords,
            description=description,
            thumbnail_suggestions=thumbnail_suggestions,
        )
    
    def optimize_title(self, content: str) -> TitleGenerationResult:
        """Generate a single optimized title.
        
        Args:
            content: Video content description.
            
        Returns:
            Best TitleGenerationResult.
        """
        return self.title_generator.generate_single_title(content)
    
    def optimize_keywords(self, content: str) -> List[KeywordResult]:
        """Generate optimized keywords.
        
        Args:
            content: Video content description.
            
        Returns:
            List of KeywordResult objects.
        """
        return self.keyword_generator.generate_keywords(content, self.num_keywords)
    
    def optimize_description(self, topic: str, chapters: List[str] = None,
                            links: List[str] = None,
                            hashtags: List[str] = None,
                            category: str = 'Education') -> DescriptionResult:
        """Build an optimized description.
        
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
    
    def optimize_thumbnails(self, content: str) -> List[ThumbnailMetadata]:
        """Generate thumbnail suggestions.
        
        Args:
            content: Video content description.
            
        Returns:
            List of ThumbnailMetadata objects.
        """
        return self.thumbnail_generator.generate_suggestions(content, self.num_thumbnails)
    
    def export_metadata(self, metadata: VideoMetadata,
                       format: str = 'json') -> str:
        """Export metadata in the specified format.
        
        Args:
            metadata: VideoMetadata to export.
            format: Output format ('json' or 'csv').
            
        Returns:
            Exported metadata as string.
        """
        if format == 'json':
            return self._export_json(metadata)
        elif format == 'csv':
            return self._export_csv(metadata)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_json(self, metadata: VideoMetadata) -> str:
        """Export metadata as JSON string."""
        import json
        
        def serialize(obj):
            """Recursively serialize objects for JSON."""
            if hasattr(obj, '__dataclass_fields__'):
                return {
                    field.name: serialize(getattr(obj, field.name))
                    for field in obj.__dataclass_fields__.values()
                }
            elif isinstance(obj, list):
                return [serialize(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, str):
                return obj
            elif isinstance(obj, (int, float, bool, type(None))):
                return obj
            else:
                return str(obj)
        
        data = serialize(metadata)
        return json.dumps(data, indent=2)
    
    def _export_csv(self, metadata: VideoMetadata) -> str:
        """Export metadata as CSV string."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write titles
        writer.writerow(['Type', 'Value', 'Score', 'Style'])
        for title in metadata.titles:
            writer.writerow(['Title', title.title, f'{title.score:.2f}', title.style])
        
        # Write keywords
        for keyword in metadata.keywords:
            writer.writerow(['Keyword', keyword.keyword, f'{keyword.relevance:.2f}',
                           keyword.priority.value])
        
        # Write description
        writer.writerow(['Description', metadata.description.full_description, '', ''])
        
        # Write thumbnail suggestions
        for thumb in metadata.thumbnail_suggestions:
            writer.writerow([
                'Thumbnail',
                thumb.description,
                f'{thumb.confidence:.2f}',
                thumb.style.value,
            ])
        
        return output.getvalue()
