"""
Thumbnail Validator Module

This module provides the ThumbnailValidator class for validating YouTube thumbnail
metadata against best practices, platform requirements, and engagement criteria.
"""

from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from enum import Enum
import re


@dataclass
class ThumbnailValidationResult:
    """Result of thumbnail validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    score: float  # 0.0 to 1.0
    suggestions: List[str]


class ThumbnailStyle(Enum):
    """Thumbnail style categories"""
    MODERN = "modern"
    MINIMALIST = "minimalist"
    BOLD = "bold"
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    PROFESSIONAL = "professional"


class ThumbnailValidator:
    """
    Validator for YouTube thumbnail concepts and metadata.
    
    This class validates thumbnail designs against YouTube's requirements,
    best practices for click-through rate, and accessibility standards.
    """
    
    # YouTube thumbnail requirements
    MAX_FILE_SIZE_MB = 2
    RECOMMENDED_WIDTH = 1280
    RECOMMENDED_HEIGHT = 720
    MIN_WIDTH = 640
    MIN_HEIGHT = 360
    ASPECT_RATIO = 16 / 9
    
    # Supported formats
    SUPPORTED_FORMATS = {'jpg', 'jpeg', 'png', 'gif'}
    
    # Text overlay guidelines
    MAX_TEXT_OVERLAY_CHARS = 100
    MIN_TEXT_OVERLAY_CHARS = 3
    MAX_TEXT_OVERLAY_WORDS = 20
    
    # Color requirements
    MIN_CONTRAST_RATIO = 4.5  # WCAG AA standard
    
    def __init__(self):
        """Initialize the thumbnail validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
    
    def validate_thumbnail(
        self,
        metadata: 'ThumbnailMetadata',
        file_path: Optional[str] = None
    ) -> ThumbnailValidationResult:
        """
        Validate a thumbnail concept or file.
        
        Args:
            metadata: Thumbnail metadata to validate
            file_path: Optional path to actual thumbnail file
            
        Returns:
            ThumbnailValidationResult with validation results
        """
        self.errors = []
        self.warnings = []
        self.suggestions = []
        
        # Validate metadata
        self._validate_style(metadata)
        self._validate_dimensions(metadata)
        self._validate_format(metadata)
        self._validate_text_overlay(metadata)
        self._validate_color_scheme(metadata)
        self._validate_elements(metadata)
        
        # Validate file if provided
        if file_path:
            self._validate_file(file_path)
        
        # Calculate score
        score = self._calculate_score(metadata)
        
        # Determine validity
        is_valid = len(self.errors) == 0
        
        return ThumbnailValidationResult(
            is_valid=is_valid,
            errors=self.errors,
            warnings=self.warnings,
            score=score,
            suggestions=self.suggestions
        )
    
    def _validate_style(self, metadata: 'ThumbnailMetadata') -> None:
        """Validate thumbnail style."""
        valid_styles = [s.value for s in ThumbnailStyle]
        
        if metadata.style not in valid_styles:
            self.errors.append(
                f"Invalid thumbnail style: '{metadata.style}'. "
                f"Valid styles are: {', '.join(valid_styles)}"
            )
            self.suggestions.append(
                f"Choose from: {', '.join(valid_styles)}"
            )
    
    def _validate_dimensions(self, metadata: 'ThumbnailMetadata') -> None:
        """Validate thumbnail dimensions."""
        width, height = metadata.recommended_dimensions
        
        # Check minimum dimensions
        if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
            self.errors.append(
                f"Dimensions {width}x{height} are too small. "
                f"Minimum required is {self.MIN_WIDTH}x{self.MIN_HEIGHT}."
            )
            self.suggestions.append(
                f"Increase dimensions to at least {self.MIN_WIDTH}x{self.MIN_HEIGHT}"
            )
        
        # Check recommended dimensions
        if width != self.RECOMMENDED_WIDTH or height != self.RECOMMENDED_HEIGHT:
            self.warnings.append(
                f"Dimensions {width}x{height} differ from recommended "
                f"{self.RECOMMENDED_WIDTH}x{self.RECOMMENDED_HEIGHT}."
            )
            self.suggestions.append(
                f"Use recommended dimensions: {self.RECOMMENDED_WIDTH}x{self.RECOMMENDED_HEIGHT}"
            )
        
        # Check aspect ratio
        if height > 0:
            actual_ratio = width / height
            if abs(actual_ratio - self.ASPECT_RATIO) > 0.1:
                self.warnings.append(
                    f"Aspect ratio {actual_ratio:.2f} differs from recommended 16:9."
                )
                self.suggestions.append(
                    "Use 16:9 aspect ratio for optimal display"
                )
    
    def _validate_format(self, metadata: 'ThumbnailMetadata') -> None:
        """Validate thumbnail file format."""
        format_lower = metadata.file_format.lower()
        
        if format_lower not in self.SUPPORTED_FORMATS:
            self.errors.append(
                f"Unsupported file format: '{metadata.file_format}'. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )
            self.suggestions.append(
                f"Convert to one of: {', '.join(self.SUPPORTED_FORMATS)}"
            )
    
    def _validate_text_overlay(self, metadata: 'ThumbnailMetadata') -> None:
        """Validate text overlay requirements."""
        text = metadata.text_overlay
        
        if not text or len(text.strip()) == 0:
            self.warnings.append(
                "No text overlay specified. Text overlays improve click-through rates."
            )
            self.suggestions.append(
                "Add a short, compelling text overlay (3-20 words)"
            )
            return
        
        # Check text length
        if len(text) > self.MAX_TEXT_OVERLAY_CHARS:
            self.errors.append(
                f"Text overlay is too long ({len(text)} characters). "
                f"Maximum is {self.MAX_TEXT_OVERLAY_CHARS} characters."
            )
            self.suggestions.append(
                f"Shorten text overlay to {self.MAX_TEXT_OVERLAY_CHARS} characters or less"
            )
        
        if len(text) < self.MIN_TEXT_OVERLAY_CHARS:
            self.warnings.append(
                f"Text overlay is too short ({len(text)} characters). "
                f"Minimum recommended is {self.MIN_TEXT_OVERLAY_CHARS} characters."
            )
        
        # Check word count
        word_count = len(text.split())
        if word_count > self.MAX_TEXT_OVERLAY_WORDS:
            self.warnings.append(
                f"Text overlay has {word_count} words. "
                f"Consider reducing to {self.MAX_TEXT_OVERLAY_WORDS} words or fewer."
            )
            self.suggestions.append(
                "Use fewer words for better readability on small screens"
            )
        
        # Check for excessive capitalization
        words = text.split()
        all_caps_words = [w for w in words if w.isupper() and len(w) > 1]
        if len(all_caps_words) > len(words) * 0.5:
            self.warnings.append(
                f"Too many words in ALL CAPS ({len(all_caps_words)} words). "
                f"This may appear spammy."
            )
            self.suggestions.append(
                "Use ALL CAPS sparingly for emphasis only"
            )
    
    def _validate_color_scheme(self, metadata: 'ThumbnailMetadata') -> None:
        """Validate color scheme requirements."""
        # Check if color scheme is valid
        valid_schemes = ['gradient', 'solid', 'high_contrast', 'professional', 'vibrant', 'corporate']
        
        if metadata.color_scheme not in valid_schemes:
            self.warnings.append(
                f"Unusual color scheme: '{metadata.color_scheme}'. "
                f"Consider using standard schemes for better compatibility."
            )
        
        # Check for high contrast requirement
        if metadata.color_scheme == 'high_contrast':
            self.warnings.append(
                "High contrast scheme detected. Ensure text remains readable."
            )
            self.suggestions.append(
                "Test text readability on various devices"
            ]
    
    def _validate_elements(self, metadata: 'ThumbnailMetadata') -> None:
        """Validate thumbnail elements."""
        elements = metadata.elements
        
        if not elements or len(elements) == 0:
            self.warnings.append(
                "No elements specified. Thumbnails typically include images, text, or graphics."
            )
            self.suggestions.append(
                "Add at least one visual element (image, text, or graphic)"
            ]
        
        # Check for element conflicts
        if 'emoji' in elements and 'professional' in metadata.style:
            self.warnings.append(
                "Emojis may not be appropriate for professional-style thumbnails."
            )
            self.suggestions.append(
                "Consider using icons or graphics instead of emojis for professional content"
            ]
        
        if 'diagram' in elements and 'entertainment' in metadata.style:
            self.warnings.append(
                "Diagrams may not be engaging for entertainment-style thumbnails."
            )
            self.suggestions.append(
                "Consider using more dynamic visual elements for entertainment content"
            ]
    
    def _validate_file(self, file_path: str) -> None:
        """Validate actual thumbnail file."""
        import os
        import mimetypes
        
        # Check file exists
        if not os.path.exists(file_path):
            self.errors.append(f"File not found: {file_path}")
            return
        
        # Check file size
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            self.errors.append(
                f"File size {file_size_mb:.2f}MB exceeds maximum {self.MAX_FILE_SIZE_MB}MB."
            )
            self.suggestions.append(
                f"Compress the image to under {self.MAX_FILE_SIZE_MB}MB"
            ]
        
        # Check file extension matches format
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        if ext != metadata.file_format.lower():
            self.warnings.append(
                f"File extension '{ext}' doesn't match specified format '{metadata.file_format}'."
            ]
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if 'jpeg' in mime_type and metadata.file_format.lower() not in ['jpg', 'jpeg']:
                self.warnings.append(
                    "File appears to be JPEG but format is specified differently."
                ]
            elif 'png' in mime_type and metadata.file_format.lower() != 'png':
                self.warnings.append(
                    "File appears to be PNG but format is specified differently."
                ]
    
    def _calculate_score(self, metadata: 'ThumbnailMetadata') -> float:
        """
        Calculate overall validation score.
        
        Args:
            metadata: Thumbnail metadata to score
            
        Returns:
            Score between 0.0 and 1.0
        """
        score = 1.0
        
        # Deduct points for errors
        score -= len(self.errors) * 0.2
        
        # Deduct points for warnings
        score -= len(self.warnings) * 0.05
        
        # Bonus for proper dimensions
        if metadata.recommended_dimensions == (self.RECOMMENDED_WIDTH, self.RECOMMENDED_HEIGHT):
            score += 0.1
        
        # Bonus for text overlay
        if metadata.text_overlay and self.MIN_TEXT_OVERLAY_CHARS <= len(metadata.text_overlay) <= self.MAX_TEXT_OVERLAY_CHARS:
            score += 0.1
        
        # Bonus for appropriate elements
        if metadata.elements and len(metadata.elements) > 0:
            score += 0.05
        
        # Bonus for high contrast
        if metadata.color_scheme == 'high_contrast':
            score += 0.05
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def get_improvement_suggestions(self, metadata: 'ThumbnailMetadata') -> List[str]:
        """
        Get specific improvement suggestions for a thumbnail.
        
        Args:
            metadata: Thumbnail metadata to improve
            
        Returns:
            List of improvement suggestions
        """
        result = self.validate_thumbnail(metadata)
        return result.suggestions
    
    def compare_thumbnails(
        self,
        metadata1: 'ThumbnailMetadata',
        metadata2: 'ThumbnailMetadata'
    ) -> Dict[str, any]:
        """
        Compare two thumbnail concepts and return which is better.
        
        Args:
            metadata1: First thumbnail metadata to compare
            metadata2: Second thumbnail metadata to compare
            
        Returns:
            Dictionary with comparison results
        """
        result1 = self.validate_thumbnail(metadata1)
        result2 = self.validate_thumbnail(metadata2)
        
        return {
            'thumbnail1_score': result1.score,
            'thumbnail2_score': result2.score,
            'better_thumbnail': 'thumbnail1' if result1.score > result2.score else 'thumbnail2',
            'thumbnail1_errors': len(result1.errors),
            'thumbnail2_errors': len(result2.errors),
            'thumbnail1_warnings': len(result1.warnings),
            'thumbnail2_warnings': len(result2.warnings),
            'thumbnail1_suggestions': result1.suggestions,
            'thumbnail2_suggestions': result2.suggestions,
        }
