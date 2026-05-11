"""
Thumbnail Generator Module

This module provides the ThumbnailGenerator class for creating thumbnail
metadata and templates for YouTube videos.
"""

from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


@dataclass
class ThumbnailMetadata:
    """Metadata for a generated thumbnail"""
    style: str
    description: str
    recommended_dimensions: Tuple[int, int]
    file_format: str
    color_scheme: str
    text_overlay: str
    elements: List[str]


class ThumbnailStyle(Enum):
    """Available thumbnail styles"""
    MODERN = "modern"
    MINIMALIST = "minimalist"
    BOLD = "bold"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    PROFESSIONAL = "professional"


class ThumbnailGenerator:
    """
    Generator for creating thumbnail metadata and templates.
    
    This class produces structured thumbnail concepts with descriptions,
    dimensions, and design recommendations for YouTube videos.
    """
    
    # Default dimensions (16:9 aspect ratio)
    DEFAULT_WIDTH = 1280
    DEFAULT_HEIGHT = 720
    
    # Thumbnail style configurations
    STYLE_CONFIGS = {
        ThumbnailStyle.MODERN: {
            'color_scheme': 'gradient',
            'font_style': 'sans-serif',
            'layout': 'centered',
            'elements': ['text_overlay', 'icon', 'gradient_background']
        },
        ThumbnailStyle.MINIMALIST: {
            'color_scheme': 'solid',
            'font_style': 'clean',
            'layout': 'clean',
            'elements': ['minimal_text', 'single_image']
        },
        ThumbnailStyle.BOLD: {
            'color_scheme': 'high_contrast',
            'font_style': 'bold',
            'layout': 'dynamic',
            'elements': ['large_text', 'bold_colors', 'arrows', 'shapes']
        },
        ThumbnailStyle.EDUCATIONAL: {
            'color_scheme': 'professional',
            'font_style': 'readable',
            'layout': 'structured',
            'elements': ['title_text', 'diagram', 'bullet_points']
        },
        ThumbnailStyle.ENTERTAINMENT: {
            'color_scheme': 'vibrant',
            'font_style': 'fun',
            'layout': 'energetic',
            'elements': ['emoji', 'expressions', 'bright_colors']
        },
        ThumbnailStyle.PROFESSIONAL: {
            'color_scheme': 'corporate',
            'font_style': 'formal',
            'layout': 'balanced',
            'elements': ['logo', 'headshot', 'clean_text']
        }
    }
    
    # Color palettes for different styles
    COLOR_PALETTES = {
        'gradient': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'],
        'solid': ['#FFFFFF', '#2C3E50', '#34495E', '#ECF0F1'],
        'high_contrast': ['#FFD700', '#000000', '#FF0000', '#FFFFFF'],
        'professional': ['#1E3A5F', '#2C5282', '#4299E1', '#F7FAFC'],
        'vibrant': ['#FF69B4', '#FF1493', '#FF6347', '#FFD700'],
        'corporate': ['#2C3E50', '#34495E', '#7F8C8D', '#BDC3C7']
    }
    
    def __init__(self, width: int = DEFAULT_WIDTH, height: int = DEFAULT_HEIGHT):
        """
        Initialize the thumbnail generator.
        
        Args:
            width: Default thumbnail width in pixels
            height: Default thumbnail height in pixels
        """
        self.width = width
        self.height = height
    
    def generate_thumbnails(self, content: str, num_thumbnails: int = 3) -> List[ThumbnailMetadata]:
        """
        Generate multiple thumbnail concepts from input content.
        
        Args:
            content: Input text describing the video content
            num_thumbnails: Number of thumbnail concepts to generate
            
        Returns:
            List of ThumbnailMetadata objects
        """
        thumbnails = []
        
        # Analyze content to determine appropriate styles
        content_lower = content.lower()
        style = self._detect_appropriate_style(content_lower)
        
        # Generate variations
        for i in range(num_thumbnails):
            thumbnail_style = self._get_variation_style(style, i)
            thumbnail = self._create_thumbnail_metadata(content, thumbnail_style)
            thumbnails.append(thumbnail)
        
        return thumbnails
    
    def generate_single_thumbnail(self, content: str, style: Optional[ThumbnailStyle] = None) -> ThumbnailMetadata:
        """
        Generate a single thumbnail concept.
        
        Args:
            content: Input text describing the video content
            style: Optional specific style to use
            
        Returns:
            ThumbnailMetadata object
        """
        if style is None:
            style = self._detect_appropriate_style(content.lower())
        
        return self._create_thumbnail_metadata(content, style)
    
    def _detect_appropriate_style(self, content: str) -> ThumbnailStyle:
        """
        Detect the most appropriate thumbnail style from content.
        
        Args:
            content: Input text
            
        Returns:
            Detected ThumbnailStyle
        """
        # Check for educational content
        educational_terms = ['tutorial', 'learn', 'guide', 'how to', 'course', 'class', 'training']
        if any(term in content for term in educational_terms):
            return ThumbnailStyle.EDUCATIONAL
        
        # Check for entertainment content
        entertainment_terms = ['funny', 'entertainment', 'viral', 'comedy', 'prank']
        if any(term in content for term in entertainment_terms):
            return ThumbnailStyle.ENTERTAINMENT
        
        # Check for professional content
        professional_terms = ['business', 'professional', 'corporate', 'expert', 'guide']
        if any(term in content for term in professional_terms):
            return ThumbnailStyle.PROFESSIONAL
        
        # Check for bold/dynamic content
        bold_terms = ['tips', 'tricks', 'secrets', 'best', 'top', 'ultimate']
        if any(term in content for term in bold_terms):
            return ThumbnailStyle.BOLD
        
        # Default to modern
        return ThumbnailStyle.MODERN
    
    def _get_variation_style(self, base_style: ThumbnailStyle, index: int) -> ThumbnailStyle:
        """
        Get a style variation based on index.
        
        Args:
            base_style: Base style to vary
            index: Variation index
            
        Returns:
            Variated ThumbnailStyle
        """
        if index == 0:
            return base_style
        
        # Return different styles for variations
        styles = list(ThumbnailStyle)
        return styles[(list(ThumbnailStyle).index(base_style) + index) % len(styles)]
    
    def _create_thumbnail_metadata(self, content: str, style: ThumbnailStyle) -> ThumbnailMetadata:
        """
        Create thumbnail metadata for a specific style.
        
        Args:
            content: Input text
            style: Thumbnail style
            
        Returns:
            ThumbnailMetadata object
        """
        config = self.STYLE_CONFIGS[style]
        
        # Extract key phrases for text overlay
        text_overlay = self._extract_text_overlay(content, style)
        
        # Determine color scheme
        color_scheme = config['color_scheme']
        
        # Build element list
        elements = config['elements'].copy()
        
        # Add content-specific elements
        if 'diagram' in elements and ('tutorial' in content.lower() or 'guide' in content.lower()):
            elements.append('step_indicators')
        
        if 'emoji' in elements:
            elements.append('reaction_emoji')
        
        return ThumbnailMetadata(
            style=style.value,
            description=self._generate_description(content, style),
            recommended_dimensions=(self.width, self.height),
            file_format='jpg',
            color_scheme=color_scheme,
            text_overlay=text_overlay,
            elements=elements
        )
    
    def _extract_text_overlay(self, content: str, style: ThumbnailStyle) -> str:
        """
        Extract appropriate text overlay for thumbnail.
        
        Args:
            content: Input text
            style: Thumbnail style
            
        Returns:
            Text overlay string
        """
        # Extract key phrases
        words = content.split()
        
        # Find meaningful phrases
        if len(words) >= 3:
            # Use first 3-5 words as text overlay
            key_phrase = ' '.join(words[:5])
            return key_phrase[:50]  # Limit to 50 characters
        
        return content[:30]
    
    def _generate_description(self, content: str, style: ThumbnailStyle) -> str:
        """
        Generate a description for the thumbnail concept.
        
        Args:
            content: Input text
            style: Thumbnail style
            
        Returns:
            Description string
        """
        base_description = f"Thumbnail design in {style.value} style"
        
        # Add specific recommendations based on style
        if style == ThumbnailStyle.MODERN:
            base_description += " with gradient background and centered text overlay"
        elif style == ThumbnailStyle.BOLD:
            base_description += " with high contrast colors and large text"
        elif style == ThumbnailStyle.EDUCATIONAL:
            base_description += " with clear structure and readable fonts"
        elif style == ThumbnailStyle.ENTERTAINMENT:
            base_description += " with vibrant colors and engaging elements"
        elif style == ThumbnailStyle.PROFESSIONAL:
            base_description += " with corporate color scheme and clean layout"
        elif style == ThumbnailStyle.MINIMALIST:
            base_description += " with clean design and minimal elements"
        
        return base_description
    
    def get_style_recommendations(self) -> Dict[str, str]:
        """
        Get recommendations for each thumbnail style.
        
        Returns:
            Dictionary mapping style names to recommendations
        """
        recommendations = {}
        
        for style, config in self.STYLE_CONFIGS.items():
            recommendations[style.value] = (
                f"Use {config['color_scheme']} colors, "
                f"{config['font_style']} font, "
                f"{config['layout']} layout"
            )
        
        return recommendations
    
    def get_color_palette(self, style: ThumbnailStyle) -> List[str]:
        """
        Get color palette for a specific style.
        
        Args:
            style: Thumbnail style
            
        Returns:
            List of hex color codes
        """
        config = self.STYLE_CONFIGS[style]
        return self.COLOR_PALETTES.get(config['color_scheme'], ['#FFFFFF', '#000000'])
    
    def validate_thumbnail_concept(self, metadata: ThumbnailMetadata) -> Tuple[bool, str]:
        """
        Validate a thumbnail concept.
        
        Args:
            metadata: Thumbnail metadata to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        # Check if style is valid
        if metadata.style not in [s.value for s in ThumbnailStyle]:
            return False, f"Invalid style: {metadata.style}"
        
        # Check if dimensions are appropriate
        width, height = metadata.recommended_dimensions
        if width != 1280 or height != 720:
            return False, f"Dimensions should be 1280x720, got {width}x{height}"
        
        # Check if file format is supported
        if metadata.file_format.lower() not in ['jpg', 'png', 'gif']:
            return False, f"Unsupported file format: {metadata.file_format}"
        
        # Check if text overlay is reasonable
        if len(metadata.text_overlay) > 100:
            return False, "Text overlay is too long (max 100 characters)"
        
        return True, "Thumbnail concept is valid"
