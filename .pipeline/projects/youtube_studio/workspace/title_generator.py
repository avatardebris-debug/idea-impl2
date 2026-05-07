"""
Title Generator Module

This module provides the TitleGenerator class for creating optimized,
SEO-friendly YouTube video titles from input content.
"""

import re
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
from datetime import datetime

from constants import (
    MAX_TITLE_LENGTH,
    MIN_TITLE_LENGTH,
    SEO_KEYWORD_WEIGHT,
    ENGAGEMENT_KEYWORD_WEIGHT,
)


@dataclass
class TitleGenerationResult:
    """Result of title generation"""
    title: str
    original_length: int
    adjusted_length: int
    keywords_used: List[str]
    is_optimized: bool
    character_count: int


class TitleGenerator:
    """
    Generator for creating optimized YouTube video titles.
    
    This class produces SEO-friendly titles within character limits,
    incorporating relevant keywords and engagement-boosting elements.
    """
    
    # Common YouTube title patterns
    TITLE_PATTERNS = [
        "{keyword}: {description}",
        "How to {action} {keyword}",
        "{keyword} Tutorial: {description}",
        "Best {keyword} for {audience}",
        "{keyword} Tips: {description}",
        "Ultimate {keyword} Guide: {description}",
        "{action} with {keyword}",
        "{keyword} Explained: {description}",
        "Top {number} {keyword} {item}",
        "{keyword} vs {comparison}",
    ]
    
    # Engagement-boosting words
    ENGAGEMENT_WORDS = [
        "Ultimate", "Complete", "Essential", "Proven", "Quick",
        "Easy", "Simple", "Master", "Guide", "Tutorial",
        "Tips", "Tricks", "Secrets", "Revealed", "Exposed"
    ]
    
    # SEO keywords database (can be expanded)
    SEO_KEYWORDS = {
        'tutorial': ['how to', 'tutorial', 'guide', 'beginner', 'step by step'],
        'review': ['review', 'best', 'top', 'comparison', 'versus'],
        'tips': ['tips', 'tricks', 'hacks', 'secrets', 'pro tips'],
        'news': ['news', 'update', 'breaking', 'latest', 'today'],
        'entertainment': ['funny', 'entertainment', 'viral', 'trending', 'popular'],
        'education': ['learn', 'education', 'course', 'class', 'training'],
        'technology': ['tech', 'technology', 'gadget', 'review', 'unboxing'],
        'lifestyle': ['lifestyle', 'daily', 'vlog', 'routine', 'tips'],
    }
    
    def __init__(self, max_length: int = MAX_TITLE_LENGTH, min_length: int = MIN_TITLE_LENGTH):
        """
        Initialize the title generator.
        
        Args:
            max_length: Maximum title length in characters
            min_length: Minimum recommended title length
        """
        self.max_length = max_length
        self.min_length = min_length
        self._keywords_used: List[str] = []
    
    def generate_titles(self, content: str, num_titles: int = 5) -> List[TitleGenerationResult]:
        """
        Generate multiple title options from input content.
        
        Args:
            content: Input text describing the video content
            num_titles: Number of title variations to generate
            
        Returns:
            List of TitleGenerationResult objects
        """
        self._keywords_used = []
        titles = []
        
        # Extract keywords from content
        keywords = self._extract_keywords(content)
        self._keywords_used = keywords[:5]  # Store used keywords
        
        # Generate base title from content
        base_title = self._create_base_title(content, keywords)
        
        # Generate variations
        for i in range(num_titles):
            title = self._generate_variation(base_title, keywords, i)
            title_result = self._process_title(title, keywords)
            titles.append(title_result)
        
        return titles
    
    def generate_single_title(self, content: str) -> TitleGenerationResult:
        """
        Generate a single optimized title from input content.
        
        Args:
            content: Input text describing the video content
            
        Returns:
            TitleGenerationResult with the generated title
        """
        keywords = self._extract_keywords(content)
        base_title = self._create_base_title(content, keywords)
        return self._process_title(base_title, keywords)
    
    def _extract_keywords(self, content: str) -> List[str]:
        """
        Extract relevant keywords from content.
        
        Args:
            content: Input text
            
        Returns:
            List of extracted keywords
        """
        # Convert to lowercase and remove special characters
        clean_text = re.sub(r'[^\w\s]', ' ', content.lower())
        words = clean_text.split()
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
        }
        
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:10]  # Return top 10 keywords
    
    def _create_base_title(self, content: str, keywords: List[str]) -> str:
        """
        Create a base title from content and keywords.
        
        Args:
            content: Input text
            keywords: Extracted keywords
            
        Returns:
            Base title string
        """
        if not keywords:
            # Fallback: use first meaningful phrase from content
            words = content.split()
            meaningful_words = [w for w in words if len(w) > 3]
            if meaningful_words:
                return ' '.join(meaningful_words[:6])
            return content[:50]
        
        # Use first keyword as main keyword
        main_keyword = keywords[0]
        
        # Create title based on content type
        if any(word in content.lower() for word in ['how', 'tutorial', 'guide', 'learn']):
            title = f"How to {main_keyword}: {content[:30]}"
        elif any(word in content.lower() for word in ['best', 'top', 'review']):
            title = f"Best {main_keyword}: {content[:30]}"
        else:
            title = f"{main_keyword}: {content[:30]}"
        
        return title
    
    def _generate_variation(self, base_title: str, keywords: List[str], index: int) -> str:
        """
        Generate a variation of the base title.
        
        Args:
            base_title: Base title to vary
            keywords: Available keywords
            index: Variation index
            
        Returns:
            Variated title string
        """
        if index == 0:
            return base_title
        
        # Add engagement word for some variations
        if index % 2 == 0 and keywords:
            engagement = self.ENGAGEMENT_WORDS[index % len(self.ENGAGEMENT_WORDS)]
            return f"{engagement} {base_title}"
        
        # Add number for some variations
        if index % 3 == 0:
            numbers = ['Ultimate', 'Complete', 'Essential', 'Proven']
            number = numbers[index % len(numbers)]
            return f"{number} {base_title}"
        
        return base_title
    
    def _process_title(self, title: str, keywords: List[str]) -> TitleGenerationResult:
        """
        Process and optimize a title.
        
        Args:
            title: Title to process
            keywords: Keywords used in title
            
        Returns:
            TitleGenerationResult
        """
        original_length = len(title)
        
        # Adjust title length to fit within limits
        adjusted_title = self._adjust_length(title)
        adjusted_length = len(adjusted_title)
        
        # Check if keywords were used
        keywords_used = [kw for kw in keywords if kw in adjusted_title.lower()]
        
        # Determine if title is optimized
        is_optimized = (
            adjusted_length <= self.max_length and
            adjusted_length >= self.min_length and
            len(keywords_used) > 0
        )
        
        return TitleGenerationResult(
            title=adjusted_title,
            original_length=original_length,
            adjusted_length=adjusted_length,
            keywords_used=keywords_used,
            is_optimized=is_optimized,
            character_count=adjusted_length
        )
    
    def _adjust_length(self, title: str) -> str:
        """
        Adjust title length to fit within character limits.
        
        Args:
            title: Title to adjust
            
        Returns:
            Adjusted title
        """
        # Remove trailing punctuation
        title = title.rstrip('.:,;!?')
        
        if len(title) <= self.max_length:
            return title
        
        # Truncate and add ellipsis if too long
        truncated = title[:self.max_length - 3]
        
        # Try to truncate at word boundary
        last_space = truncated.rfind(' ')
        if last_space > self.min_length:
            truncated = truncated[:last_space]
        
        return truncated + '...'
    
    def validate_title(self, title: str) -> Tuple[bool, List[str]]:
        """
        Validate a title against YouTube requirements.
        
        Args:
            title: Title to validate
            
        Returns:
            Tuple of (is_valid, list of issues)
        """
        issues = []
        
        # Check length
        if len(title) > self.max_length:
            issues.append(f"Title exceeds maximum length of {self.max_length} characters")
        
        if len(title) < self.min_length:
            issues.append(f"Title is too short (minimum {self.min_length} characters recommended)")
        
        # Check for special characters that might cause issues
        problematic_chars = ['<', '>', '|', '"', "'"]
        for char in problematic_chars:
            if char in title:
                issues.append(f"Title contains problematic character: '{char}'")
        
        # Check for all caps (excessive use)
        if title.isupper() and len(title) > 10:
            issues.append("Title is in all caps (consider using normal case)")
        
        return len(issues) == 0, issues
    
    def get_keyword_suggestions(self, content: str, num_suggestions: int = 10) -> List[str]:
        """
        Get keyword suggestions for a title.
        
        Args:
            content: Input text to analyze
            num_suggestions: Number of suggestions to return
            
        Returns:
            List of keyword suggestions
        """
        keywords = self._extract_keywords(content)
        
        # Get SEO keywords for detected categories
        all_keywords = []
        content_lower = content.lower()
        
        for category, category_keywords in self.SEO_KEYWORDS.items():
            if any(word in content_lower for word in category_keywords):
                all_keywords.extend(category_keywords)
        
        # Combine with extracted keywords
        all_keywords.extend(keywords)
        
        # Remove duplicates and return top suggestions
        seen = set()
        unique_keywords = []
        for kw in all_keywords:
            if kw not in seen and len(kw) <= 20:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:num_suggestions]
