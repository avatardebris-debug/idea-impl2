"""Thumbnail generator for YouTube Studio.

This module provides functionality for generating thumbnail metadata
and suggestions for YouTube video thumbnails.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from .constants import (
    DEFAULT_THUMBNAIL_WIDTH,
    DEFAULT_THUMBNAIL_HEIGHT,
    DEFAULT_THUMBNAIL_FORMAT,
)


class ThumbnailStyle(Enum):
    """Available thumbnail styles."""
    BOLD_TEXT = 'bold_text'
    SPLIT_SCREEN = 'split_screen'
    CLOSE_UP = 'close_up'
    MINIMAL = 'minimal'
    ACTION_SHOT = 'action_shot'
    BEFORE_AFTER = 'before_after'
    COMPARISON = 'comparison'
    NUMBERED_LIST = 'numbered_list'
    REACTION = 'reaction'
    TEXT_OVERLAY = 'text_overlay'


@dataclass
class ThumbnailMetadata:
    """Metadata for a thumbnail suggestion.
    
    Attributes:
        style: The thumbnail style.
        description: Description of the thumbnail concept.
        text_overlay: Suggested text overlay.
        color_scheme: Suggested color scheme.
        layout: Layout description.
        confidence: Confidence score (0.0 to 1.0).
        elements: List of visual elements to include.
    """
    style: ThumbnailStyle
    description: str
    text_overlay: str
    color_scheme: str
    layout: str
    confidence: float
    elements: List[str] = field(default_factory=list)


class ThumbnailGenerator:
    """Generator for YouTube video thumbnail suggestions.
    
    This class generates thumbnail metadata and suggestions
    based on video content analysis.
    """
    
    # Color schemes for different moods
    COLOR_SCHEMES = {
        'energetic': ('#FF6B6B', '#4ECDC4', '#FFE66D'),
        'professional': ('#2C3E50', '#3498DB', '#ECF0F1'),
        'warm': ('#F39C12', '#E74C3C', '#F1C40F'),
        'cool': ('#3498DB', '#9B59B6', '#1ABC9C'),
        'dark': ('#2C3E50', '#E74C3C', '#F39C12'),
        'bright': ('#FF6B6B', '#4ECDC4', '#45B7D1'),
        'neon': ('#00FF87', '#60EFFF', '#FF6B6B'),
        'pastel': ('#FFB3BA', '#BAFFC9', '#BAE1FF'),
    }
    
    # Text styles for different thumbnail types
    TEXT_STYLES = {
        ThumbnailStyle.BOLD_TEXT: {
            'font_weight': 'bold',
            'font_size': 'large',
            'shadow': True,
            'outline': True,
        },
        ThumbnailStyle.SPLIT_SCREEN: {
            'font_weight': 'medium',
            'font_size': 'medium',
            'shadow': True,
            'outline': False,
        },
        ThumbnailStyle.CLOSE_UP: {
            'font_weight': 'bold',
            'font_size': 'x-large',
            'shadow': True,
            'outline': True,
        },
        ThumbnailStyle.MINIMAL: {
            'font_weight': 'light',
            'font_size': 'small',
            'shadow': False,
            'outline': False,
        },
        ThumbnailStyle.ACTION_SHOT: {
            'font_weight': 'bold',
            'font_size': 'large',
            'shadow': True,
            'outline': True,
        },
    }
    
    def __init__(self, width: int = DEFAULT_THUMBNAIL_WIDTH,
                 height: int = DEFAULT_THUMBNAIL_HEIGHT,
                 format: str = DEFAULT_THUMBNAIL_FORMAT):
        """Initialize thumbnail generator.
        
        Args:
            width: Thumbnail width in pixels.
            height: Thumbnail height in pixels.
            format: Output format.
        """
        self.width = width
        self.height = height
        self.format = format
    
    def generate_suggestions(self, content: str, num_suggestions: int = 3) -> List[ThumbnailMetadata]:
        """Generate thumbnail suggestions based on content.
        
        Args:
            content: Video content description.
            num_suggestions: Number of suggestions to generate.
            
        Returns:
            List of ThumbnailMetadata objects.
        """
        mood = self._analyze_mood(content)
        topics = self._extract_topics(content)
        styles = self._select_styles(content)
        
        suggestions = []
        for style in styles[:num_suggestions]:
            metadata = self._generate_metadata(style, content, mood, topics)
            suggestions.append(metadata)
        
        return suggestions
    
    def _analyze_mood(self, content: str) -> str:
        """Analyze the mood of the content.
        
        Args:
            content: Video content description.
            
        Returns:
            Mood string.
        """
        content_lower = content.lower()
        
        mood_indicators = {
            'energetic': ['exciting', 'amazing', 'incredible', 'powerful', 'intense'],
            'professional': ['guide', 'tutorial', 'how to', 'learn', 'education'],
            'warm': ['heartwarming', 'inspiring', 'motivating', 'positive', 'uplifting'],
            'cool': ['tech', 'science', 'future', 'innovation', 'digital'],
            'dark': ['warning', 'danger', 'risk', 'problem', 'issue'],
            'bright': ['happy', 'joy', 'celebration', 'success', 'achievement'],
            'neon': ['gaming', 'cyber', 'digital', 'virtual', 'online'],
            'pastel': ['lifestyle', 'beauty', 'fashion', 'wellness', 'relaxing'],
        }
        
        for mood, indicators in mood_indicators.items():
            if any(indicator in content_lower for indicator in indicators):
                return mood
        
        return 'professional'
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract key topics from content.
        
        Args:
            content: Video content description.
            
        Returns:
            List of topics.
        """
        # Simple topic extraction
        words = content.lower().split()
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'shall', 'can',
                      'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                      'as', 'into', 'through', 'during', 'before', 'after', 'above',
                      'below', 'between', 'and', 'but', 'or', 'nor', 'not', 'so',
                      'yet', 'both', 'either', 'neither', 'each', 'every', 'all',
                      'any', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
                      'only', 'own', 'same', 'than', 'too', 'very', 'just', 'because',
                      'if', 'when', 'where', 'how', 'what', 'which', 'who', 'whom',
                      'this', 'that', 'these', 'those', 'i', 'me', 'my', 'myself',
                      'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
                      'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
                      'she', 'her', 'hers', 'herself', 'it', 'its', 'itself',
                      'they', 'them', 'their', 'theirs', 'themselves'}
        
        word_freq = {}
        for word in words:
            word = word.strip('.,!?;:()[]{}\'"')
            if word and word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [topic[0] for topic in topics[:5]]
    
    def _select_styles(self, content: str) -> List[ThumbnailStyle]:
        """Select appropriate thumbnail styles for the content.
        
        Args:
            content: Video content description.
            
        Returns:
            List of selected styles.
        """
        content_lower = content.lower()
        styles = []
        
        # Determine primary style
        if any(word in content_lower for word in ['before', 'after', 'transform', 'change']):
            styles.append(ThumbnailStyle.BEFORE_AFTER)
        elif any(word in content_lower for word in ['compare', 'vs', 'versus', 'difference']):
            styles.append(ThumbnailStyle.COMPARISON)
        elif any(word in content_lower for word in ['list', 'top', 'best', 'number']):
            styles.append(ThumbnailStyle.NUMBERED_LIST)
        elif any(word in content_lower for word in ['reaction', 'face', 'expression']):
            styles.append(ThumbnailStyle.REACTION)
        elif any(word in content_lower for word in ['action', 'sport', 'exercise', 'workout']):
            styles.append(ThumbnailStyle.ACTION_SHOT)
        elif any(word in content_lower for word in ['close', 'detail', 'focus', 'zoom']):
            styles.append(ThumbnailStyle.CLOSE_UP)
        elif any(word in content_lower for word in ['split', 'dual', 'two', 'side']):
            styles.append(ThumbnailStyle.SPLIT_SCREEN)
        elif any(word in content_lower for word in ['minimal', 'simple', 'clean', 'elegant']):
            styles.append(ThumbnailStyle.MINIMAL)
        else:
            styles.append(ThumbnailStyle.BOLD_TEXT)
        
        # Add secondary styles
        styles.append(ThumbnailStyle.TEXT_OVERLAY)
        
        return styles
    
    def _generate_metadata(self, style: ThumbnailStyle, content: str,
                          mood: str, topics: List[str]) -> ThumbnailMetadata:
        """Generate thumbnail metadata for a specific style.
        
        Args:
            style: Thumbnail style.
            content: Video content description.
            mood: Content mood.
            topics: Extracted topics.
            
        Returns:
            ThumbnailMetadata object.
        """
        # Get color scheme
        colors = self.COLOR_SCHEMES.get(mood, self.COLOR_SCHEMES['professional'])
        
        # Get text style
        text_style = self.TEXT_STYLES.get(style, self.TEXT_STYLES[ThumbnailStyle.BOLD_TEXT])
        
        # Generate text overlay
        text_overlay = self._generate_text_overlay(style, topics)
        
        # Generate description
        description = self._generate_description(style, mood, topics)
        
        # Generate layout
        layout = self._generate_layout(style)
        
        # Generate elements
        elements = self._generate_elements(style, topics)
        
        # Calculate confidence
        confidence = self._calculate_confidence(style, content)
        
        return ThumbnailMetadata(
            style=style,
            description=description,
            text_overlay=text_overlay,
            color_scheme=', '.join(colors),
            layout=layout,
            confidence=confidence,
            elements=elements,
        )
    
    def _generate_text_overlay(self, style: ThumbnailStyle, topics: List[str]) -> str:
        """Generate text overlay for the thumbnail.
        
        Args:
            style: Thumbnail style.
            topics: Extracted topics.
            
        Returns:
            Text overlay string.
        """
        if not topics:
            return 'Watch Now'
        
        main_topic = topics[0].capitalize()
        
        text_overlays = {
            ThumbnailStyle.BOLD_TEXT: f'{main_topic}!',
            ThumbnailStyle.SPLIT_SCREEN: f'Before vs After',
            ThumbnailStyle.CLOSE_UP: f'{main_topic}?',
            ThumbnailStyle.MINIMAL: f'{main_topic}',
            ThumbnailStyle.ACTION_SHOT: f'{main_topic}!',
            ThumbnailStyle.BEFORE_AFTER: f'Before → After',
            ThumbnailStyle.COMPARISON: f'vs',
            ThumbnailStyle.NUMBERED_LIST: f'#{len(topics)}',
            ThumbnailStyle.REACTION: f'OMG!',
            ThumbnailStyle.TEXT_OVERLAY: f'{main_topic}',
        }
        
        return text_overlays.get(style, f'{main_topic}')
    
    def _generate_description(self, style: ThumbnailStyle, mood: str,
                             topics: List[str]) -> str:
        """Generate description for the thumbnail.
        
        Args:
            style: Thumbnail style.
            mood: Content mood.
            topics: Extracted topics.
            
        Returns:
            Description string.
        """
        descriptions = {
            ThumbnailStyle.BOLD_TEXT: f'Bold text overlay with {mood} colors',
            ThumbnailStyle.SPLIT_SCREEN: f'Split screen showing contrast',
            ThumbnailStyle.CLOSE_UP: f'Close-up shot with dramatic lighting',
            ThumbnailStyle.MINIMAL: f'Minimalist design with clean lines',
            ThumbnailStyle.ACTION_SHOT: f'Dynamic action shot with motion blur',
            ThumbnailStyle.BEFORE_AFTER: f'Before and after comparison',
            ThumbnailStyle.COMPARISON: f'Side-by-side comparison layout',
            ThumbnailStyle.NUMBERED_LIST: f'Numbered list with icons',
            ThumbnailStyle.REACTION: f'Reaction face with expressive background',
            ThumbnailStyle.TEXT_OVERLAY: f'Text overlay on relevant background',
        }
        
        return descriptions.get(style, 'Custom thumbnail design')
    
    def _generate_layout(self, style: ThumbnailStyle) -> str:
        """Generate layout description for the thumbnail.
        
        Args:
            style: Thumbnail style.
            
        Returns:
            Layout description string.
        """
        layouts = {
            ThumbnailStyle.BOLD_TEXT: 'Centered text with background image',
            ThumbnailStyle.SPLIT_SCREEN: 'Vertical split with two images',
            ThumbnailStyle.CLOSE_UP: 'Full face close-up with text overlay',
            ThumbnailStyle.MINIMAL: 'Clean background with small text',
            ThumbnailStyle.ACTION_SHOT: 'Dynamic action shot with text overlay',
            ThumbnailStyle.BEFORE_AFTER: 'Horizontal split with before/after',
            ThumbnailStyle.COMPARISON: 'Side-by-side comparison layout',
            ThumbnailStyle.NUMBERED_LIST: 'Numbered items with icons',
            ThumbnailStyle.REACTION: 'Reaction face with background',
            ThumbnailStyle.TEXT_OVERLAY: 'Text overlay on relevant background',
        }
        
        return layouts.get(style, 'Custom layout')
    
    def _generate_elements(self, style: ThumbnailStyle, topics: List[str]) -> List[str]:
        """Generate visual elements for the thumbnail.
        
        Args:
            style: Thumbnail style.
            topics: Extracted topics.
            
        Returns:
            List of visual elements.
        """
        elements = []
        
        # Common elements
        elements.append('High contrast colors')
        elements.append('Clear typography')
        
        # Style-specific elements
        if style == ThumbnailStyle.BOLD_TEXT:
            elements.append('Large bold text')
            elements.append('Vibrant background')
        elif style == ThumbnailStyle.SPLIT_SCREEN:
            elements.append('Two distinct images')
            elements.append('Divider line')
        elif style == ThumbnailStyle.CLOSE_UP:
            elements.append('Facial expression')
            elements.append('Dramatic lighting')
        elif style == ThumbnailStyle.MINIMAL:
            elements.append('Clean background')
            elements.append('Small text')
        elif style == ThumbnailStyle.ACTION_SHOT:
            elements.append('Motion blur')
            elements.append('Dynamic angle')
        elif style == ThumbnailStyle.BEFORE_AFTER:
            elements.append('Before image')
            elements.append('After image')
            elements.append('Arrow indicator')
        elif style == ThumbnailStyle.COMPARISON:
            elements.append('Item 1')
            elements.append('Item 2')
            elements.append('VS text')
        elif style == ThumbnailStyle.NUMBERED_LIST:
            elements.append('Numbers')
            elements.append('Icons')
        elif style == ThumbnailStyle.REACTION:
            elements.append('Reaction face')
            elements.append('Expressive background')
        elif style == ThumbnailStyle.TEXT_OVERLAY:
            elements.append('Text overlay')
            elements.append('Relevant background')
        
        # Add topic-specific elements
        if topics:
            elements.append(f'{topics[0].capitalize()} related imagery')
        
        return elements
    
    def _calculate_confidence(self, style: ThumbnailStyle, content: str) -> float:
        """Calculate confidence score for the thumbnail suggestion.
        
        Args:
            style: Thumbnail style.
            content: Video content description.
            
        Returns:
            Confidence score between 0.0 and 1.0.
        """
        confidence = 0.5  # Base confidence
        
        # Adjust based on content relevance
        content_lower = content.lower()
        
        if style == ThumbnailStyle.BOLD_TEXT and any(word in content_lower for word in ['guide', 'tutorial']):
            confidence += 0.2
        elif style == ThumbnailStyle.SPLIT_SCREEN and any(word in content_lower for word in ['before', 'after']):
            confidence += 0.2
        elif style == ThumbnailStyle.CLOSE_UP and any(word in content_lower for word in ['face', 'expression']):
            confidence += 0.2
        elif style == ThumbnailStyle.MINIMAL and any(word in content_lower for word in ['simple', 'clean']):
            confidence += 0.2
        elif style == ThumbnailStyle.ACTION_SHOT and any(word in content_lower for word in ['action', 'sport']):
            confidence += 0.2
        elif style == ThumbnailStyle.BEFORE_AFTER and any(word in content_lower for word in ['transform', 'change']):
            confidence += 0.2
        elif style == ThumbnailStyle.COMPARISON and any(word in content_lower for word in ['compare', 'vs']):
            confidence += 0.2
        elif style == ThumbnailStyle.NUMBERED_LIST and any(word in content_lower for word in ['list', 'top']):
            confidence += 0.2
        elif style == ThumbnailStyle.REACTION and any(word in content_lower for word in ['reaction', 'face']):
            confidence += 0.2
        elif style == ThumbnailStyle.TEXT_OVERLAY:
            confidence += 0.1
        
        return min(confidence, 1.0)
