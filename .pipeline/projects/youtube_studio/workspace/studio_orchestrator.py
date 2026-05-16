"""
Studio Orchestrator Module

This module provides the StudioOrchestrator class that coordinates all
YouTube Studio components for generating complete video metadata.
"""

import sys
import pathlib
# Ensure the workspace directory is on sys.path so sibling modules resolve
# correctly when pytest is run from the repo root rather than this directory.
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import os

from title_generator import TitleGenerator, TitleGenerationResult
from thumbnail_generator import ThumbnailGenerator, ThumbnailStyle, ThumbnailMetadata
from keyword_generator import KeywordGenerator, KeywordResult, KeywordPriority
from transcript_builder import TranscriptBuilder, TranscriptSection
from templates.template_manager import TemplateManager
from templates.template_engine import TemplateEngine
from config import get_config
from constants import (
    MAX_TITLE_LENGTH,
    MAX_KEYWORDS_PER_TAG,
    MAX_NUMBER_OF_KEYWORDS,
    MIN_NUMBER_OF_KEYWORDS,
)



@dataclass
class VideoMetadata:
    """Complete video metadata for YouTube upload"""
    title: str
    description: str
    keywords: List[str]
    thumbnail_suggestions: List[ThumbnailMetadata]
    tags: List[str]
    category: Optional[str] = None
    target_audience: Optional[str] = None
    upload_date: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()


@dataclass
class TranscriptData:
    """Transcript data for a video"""
    title: str
    sections: List[TranscriptSection]
    total_duration: float
    word_count: int
    character_count: int
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class StudioResult:
    """Complete result from YouTube Studio processing"""
    video_id: Optional[str]
    metadata: VideoMetadata
    transcript: Optional[TranscriptData]
    template_used: Optional[str]
    processing_time_ms: float
    success: bool
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class StudioOrchestrator:
    """
    Main orchestrator for YouTube Studio functionality.
    
    This class coordinates all sub-components (title, thumbnail, keyword,
    transcript generators) and provides a unified API for generating
    complete video metadata from input content.
    """
    
    def __init__(
        self,
        title_generator: Optional[TitleGenerator] = None,
        thumbnail_generator: Optional[ThumbnailGenerator] = None,
        keyword_generator: Optional[KeywordGenerator] = None,
        template_manager: Optional[TemplateManager] = None,
        template_engine: Optional[TemplateEngine] = None,
        config: Optional[Any] = None
    ):
        """
        Initialize the studio orchestrator.
        
        Args:
            title_generator: Title generator instance
            thumbnail_generator: Thumbnail generator instance
            keyword_generator: Keyword generator instance
            template_manager: Template manager instance
            template_engine: Template engine instance
            config: Configuration object
        """
        self.config = config or get_config()
        _max_len = (
            self.config.get_title_config().max_length
            if hasattr(self.config, 'get_title_config')
            else MAX_TITLE_LENGTH
        )
        self.title_generator = title_generator or TitleGenerator(max_length=_max_len)
        self.thumbnail_generator = thumbnail_generator or ThumbnailGenerator()
        _min_kw = (
            self.config.get_keyword_config().min_keywords
            if hasattr(self.config, 'get_keyword_config')
            else MIN_NUMBER_OF_KEYWORDS
        )
        _max_kw = (
            self.config.get_keyword_config().max_keywords
            if hasattr(self.config, 'get_keyword_config')
            else MAX_NUMBER_OF_KEYWORDS
        )
        self.keyword_generator = keyword_generator or KeywordGenerator(
            min_keywords=_min_kw,
            max_keywords=_max_kw,
        )
        self.template_manager = template_manager or TemplateManager()
        self.template_engine = template_engine or TemplateEngine()
        self._processing_start: Optional[float] = None
    
    def process_content(
        self,
        content: str,
        video_title: Optional[str] = None,
        video_category: Optional[str] = None,
        target_audience: Optional[str] = None,
        use_template: bool = False,
        template_name: Optional[str] = None
    ) -> StudioResult:
        """
        Process video content and generate complete metadata.
        
        Args:
            content: Input text describing the video content
            video_title: Optional custom title
            video_category: Optional video category
            target_audience: Optional target audience description
            use_template: Whether to use a template for generation
            template_name: Name of template to use
            
        Returns:
            StudioResult with complete metadata
        """
        self._processing_start = datetime.now().timestamp()
        errors = []
        
        try:
            # Generate title
            if video_title:
                title_result = self._process_custom_title(video_title)
            else:
                title_result = self.title_generator.generate_single_title(content)
            
            # Generate thumbnail suggestions
            thumbnail_suggestions = self.thumbnail_generator.generate_thumbnails(content, num_thumbnails=3)
            
            # Generate keywords
            keywords = self.keyword_generator.generate_keywords(content, num_keywords=20)
            keyword_strings = [kw.keyword for kw in keywords]
            
            # Build metadata
            metadata = self._build_metadata(
                title=title_result.title,
                description=content,
                keywords=keyword_strings,
                thumbnail_suggestions=thumbnail_suggestions,
                category=video_category,
                target_audience=target_audience,
                template_name=template_name if use_template else None
            )
            
            processing_time = self._calculate_processing_time()
            
            return StudioResult(
                video_id=None,
                metadata=metadata,
                transcript=None,
                template_used=template_name if use_template else None,
                processing_time_ms=processing_time,
                success=True,
                errors=errors
            )
            
        except Exception as e:
            processing_time = self._calculate_processing_time()
            errors.append(str(e))
            
            return StudioResult(
                video_id=None,
                metadata=None,
                transcript=None,
                template_used=None,
                processing_time_ms=processing_time,
                success=False,
                errors=errors
            )
    
    def process_transcript(
        self,
        content: str,
        title: Optional[str] = None,
        sections: Optional[List[Dict]] = None
    ) -> TranscriptData:
        """
        Process transcript content and create structured transcript.
        
        Args:
            content: Transcript text content
            title: Optional transcript title
            sections: Optional list of section dictionaries with title and content
            
        Returns:
            TranscriptData with structured transcript
        """
        builder = TranscriptBuilder(title=title or "Untitled Transcript")
        
        if sections:
            # Add sections from provided data
            for i, section in enumerate(sections):
                start_time = section.get('start_time', 0.0)
                end_time = section.get('end_time', None)
                builder.add_section(
                    title=section.get('title', f'Section {i+1}'),
                    content=section.get('content', ''),
                    start_time=start_time,
                    end_time=end_time
                )
        else:
            # Split content into sections based on paragraphs
            paragraphs = content.split('\n\n')
            current_time = 0.0
            
            for paragraph in paragraphs[:10]:  # Limit to 10 sections
                if paragraph.strip():
                    builder.add_section(
                        title=f'Section {len(builder.get_sections()) + 1}',
                        content=paragraph.strip(),
                        start_time=current_time
                    )
                    current_time += 5.0  # Estimate 5 seconds per paragraph
        
        sections_data = builder.get_sections()
        total_duration = builder.get_total_duration()
        summary = builder.get_summary()
        
        return TranscriptData(
            title=builder.title,
            sections=sections_data,
            total_duration=total_duration,
            word_count=summary['total_words'],
            character_count=summary['total_characters'],
            created_at=datetime.now().isoformat()
        )
    
    def generate_from_template(
        self,
        template_name: str,
        variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate metadata from a specific template.
        
        Args:
            template_name: Name of template to use
            variables: Variable values for the template
            
        Returns:
            Dictionary with generated metadata
        """
        template = self.template_manager.get_template(template_name)
        
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Render template using the engine
        rendered = self.template_engine.render(template['content'], variables)
        
        if not rendered.success:
            raise ValueError(f"Template rendering failed: {rendered.errors}")
        
        return {
            'template_name': template_name,
            'variables': variables,
            'rendered': rendered.rendered_content,
            'variables_used': rendered.variables_used
        }
    
    def export_metadata(
        self,
        metadata: VideoMetadata,
        format: str = 'json',
        output_path: Optional[str] = None
    ) -> str:
        """
        Export video metadata to a file.
        
        Args:
            metadata: Video metadata to export
            format: Output format (json, csv, txt)
            output_path: Optional output file path
            
        Returns:
            Path to exported file
        """
        import json
        import csv
        
        if not output_path:
            output_path = f"metadata_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        
        try:
            if format == 'json':
                data = {
                    'title': metadata.title,
                    'description': metadata.description,
                    'keywords': metadata.keywords,
                    'tags': metadata.tags,
                    'category': metadata.category,
                    'target_audience': metadata.target_audience,
                    'thumbnail_suggestions': [
                        {
                            'style': ts.style,
                            'text': ts.text,
                            'description': ts.description
                        }
                        for ts in metadata.thumbnail_suggestions
                    ],
                    'created_at': metadata.created_at,
                    'updated_at': metadata.updated_at
                }
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            
            elif format == 'csv':
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Field', 'Value'])
                    writer.writerow(['Title', metadata.title])
                    writer.writerow(['Description', metadata.description])
                    writer.writerow(['Keywords', '; '.join(metadata.keywords)])
                    writer.writerow(['Tags', '; '.join(metadata.tags)])
                    writer.writerow(['Category', metadata.category or ''])
                    writer.writerow(['Target Audience', metadata.target_audience or ''])
                    writer.writerow(['Created At', metadata.created_at])
            
            elif format == 'txt':
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"Title: {metadata.title}\n")
                    f.write(f"Description: {metadata.description}\n")
                    f.write(f"Keywords: {'; '.join(metadata.keywords)}\n")
                    f.write(f"Tags: {'; '.join(metadata.tags)}\n")
                    f.write(f"Category: {metadata.category or 'N/A'}\n")
                    f.write(f"Target Audience: {metadata.target_audience or 'N/A'}\n")
                    f.write(f"Created At: {metadata.created_at}\n")
            
            return output_path
            
        except IOError as e:
            raise IOError(f"Failed to export metadata: {e}")
    
    def validate_metadata(self, metadata: VideoMetadata) -> tuple:
        """
        Validate video metadata against YouTube best practices.
        
        Args:
            metadata: Video metadata to validate
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Check title length
        if len(metadata.title) > MAX_TITLE_LENGTH:
            issues.append(f"Title exceeds {MAX_TITLE_LENGTH} characters ({len(metadata.title)})")
        
        # Check title length minimum
        if len(metadata.title) < 10:
            issues.append("Title is too short (minimum 10 characters recommended)")
        
        # Check keywords count
        if len(metadata.keywords) < MIN_NUMBER_OF_KEYWORDS:
            issues.append(f"Too few keywords ({len(metadata.keywords)}, minimum {MIN_NUMBER_OF_KEYWORDS} recommended)")
        
        if len(metadata.keywords) > MAX_NUMBER_OF_KEYWORDS:
            issues.append(f"Too many keywords ({len(metadata.keywords)}, maximum {MAX_NUMBER_OF_KEYWORDS} recommended)")
        
        # Check keyword length
        for i, keyword in enumerate(metadata.keywords):
            if len(keyword) > MAX_KEYWORDS_PER_TAG:
                issues.append(f"Keyword {i+1} exceeds {MAX_KEYWORDS_PER_TAG} characters")
        
        # Check for empty fields
        if not metadata.title.strip():
            issues.append("Title cannot be empty")
        
        if not metadata.description.strip():
            issues.append("Description cannot be empty")
        
        return len(issues) == 0, issues
    
    def get_processing_stats(self) -> Dict:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        return {
            'templates_loaded': len(self.template_manager.get_template_names()),
            'title_generator_config': {
                'max_length': self.title_generator.max_length,
            },
            'thumbnail_generator_config': {
                'width': self.thumbnail_generator.width,
                'height': self.thumbnail_generator.height,
            },
            'keyword_generator_config': {
                'min_keywords': self.keyword_generator.min_keywords,
                'max_keywords': self.keyword_generator.max_keywords,
            }
        }
    
    def _process_custom_title(self, title: str) -> TitleGenerationResult:
        """Process a custom title."""
        return TitleGenerationResult(
            title=title,
            score=1.0,
            style='custom',
            description='Custom title provided by user'
        )
    
    def _build_metadata(
        self,
        title: str,
        description: str,
        keywords: List[str],
        thumbnail_suggestions: List[ThumbnailMetadata],
        category: Optional[str] = None,
        target_audience: Optional[str] = None,
        template_name: Optional[str] = None
    ) -> VideoMetadata:
        """Build complete video metadata."""
        # Convert keyword results to strings
        keyword_strings = [kw.keyword for kw in keywords] if isinstance(keywords[0], KeywordResult) else keywords
        
        return VideoMetadata(
            title=title,
            description=description,
            keywords=keyword_strings,
            thumbnail_suggestions=thumbnail_suggestions,
            tags=keyword_strings[:10],  # First 10 keywords as tags
            category=category,
            target_audience=target_audience,
            upload_date=datetime.now().isoformat(),
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def _calculate_processing_time(self) -> float:
        """Calculate processing time in milliseconds."""
        if self._processing_start:
            elapsed = (datetime.now().timestamp() - self._processing_start) * 1000
            return round(elapsed, 2)
        return 0.0
    
    def clear_cache(self):
        """Clear any cached data."""
        self._processing_start = None
