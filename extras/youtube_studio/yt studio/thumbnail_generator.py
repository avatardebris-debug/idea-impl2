"""Thumbnail generator for YouTube Studio."""

from enum import Enum
from typing import List, Optional
from dataclasses import dataclass


class ThumbnailStyle(Enum):
    """Thumbnail style options."""
    MINIMALIST = "minimalist"
    BOLD = "bold"
    COLORFUL = "colorful"
    PROFESSIONAL = "professional"
    PLAYFUL = "playful"
    DRAMATIC = "dramatic"


@dataclass
class ThumbnailSuggestion:
    """A thumbnail suggestion."""
    style: str
    description: str
    color_scheme: str
    text_overlay: str
    image_prompt: str


class ThumbnailGenerator:
    """Generates thumbnail suggestions."""
    
    COLOR_SCHEMES = {
        ThumbnailStyle.MINIMALIST: ["#FFFFFF", "#000000", "#CCCCCC"],
        ThumbnailStyle.BOLD: ["#FF0000", "#000000", "#FFFFFF"],
        ThumbnailStyle.COLORFUL: ["#FF6B6B", "#4ECDC4", "#45B7D1"],
        ThumbnailStyle.PROFESSIONAL: ["#2C3E50", "#ECF0F1", "#3498DB"],
        ThumbnailStyle.PLAYFUL: ["#FFD93D", "#FF6B6B", "#6BCB77"],
        ThumbnailStyle.DRAMATIC: ["#000000", "#8B0000", "#FFD700"],
    }
    
    def generate_thumbnails(self, content: str, style: Optional[ThumbnailStyle] = None) -> List[ThumbnailSuggestion]:
        """Generate thumbnail suggestions."""
        if style is None:
            style = ThumbnailStyle.BOLD
        
        suggestions = []
        color_scheme = self.COLOR_SCHEMES.get(style, self.COLOR_SCHEMES[ThumbnailStyle.BOLD])
        
        # Generate multiple variations
        for i in range(3):
            text_overlay = self._generate_text_overlay(content, style)
            description = self._generate_description(content, style, i)
            image_prompt = self._generate_image_prompt(content, style, color_scheme)
            
            suggestion = ThumbnailSuggestion(
                style=style.value,
                description=description,
                color_scheme=', '.join(color_scheme),
                text_overlay=text_overlay,
                image_prompt=image_prompt
            )
            suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_text_overlay(self, content: str, style: ThumbnailStyle) -> str:
        """Generate text overlay for thumbnail."""
        words = content.split()[:3]
        text = ' '.join(words).upper()
        
        if style == ThumbnailStyle.MINIMALIST:
            return text[:20]
        elif style == ThumbnailStyle.BOLD:
            return text[:15] + '!'
        elif style == ThumbnailStyle.PLAYFUL:
            return text[:10] + '!'
        return text[:25]
    
    def _generate_description(self, content: str, style: ThumbnailStyle, index: int) -> str:
        """Generate thumbnail description."""
        descriptions = [
            f"Eye-catching thumbnail with {style.value} style",
            f"Professional thumbnail design with {style.value} elements",
            f"Creative thumbnail with {style.value} aesthetic"
        ]
        return descriptions[index % len(descriptions)]
    
    def _generate_image_prompt(self, content: str, style: ThumbnailStyle, colors: List[str]) -> str:
        """Generate image prompt for thumbnail."""
        return f"{style.value} thumbnail with colors {', '.join(colors)} for content about {content[:30]}"
