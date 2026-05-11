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
        "Top {number} {keyword} {type}",
        "{keyword} for Beginners: {description}",
    ]
    
    # Engagement-boosting words
    ENGAGEMENT_WORDS = [
        "Ultimate", "Essential", "Complete", "Proven", "Easy",
        "Quick", "Simple", "Powerful", "Effective", "Step-by-Step",
        "Beginner", "Advanced", "Expert", "Master", "Guide",
        "Tutorial", "Tips", "Tricks", "Secrets", "Revealed",
    ]
    
    # Stop words to exclude from keywords
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
        'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are',
        'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'can', 'shall', 'it', 'its', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'we', 'they',
        'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
        'our', 'their', 'what', 'which', 'who', 'whom', 'where',
        'when', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
        'more', 'most', 'other', 'some', 'such', 'no', 'not', 'only',
        'own', 'same', 'so', 'than', 'too', 'very', 'just', 'because',
        'as', 'until', 'while', 'about', 'between', 'through', 'during',
        'before', 'after', 'above', 'below', 'up', 'down', 'out', 'off',
        'over', 'under', 'again', 'further', 'then', 'once', 'here',
        'there', 'any', 'if', 'then', 'else', 'also', 'yet', 'even',
        'still', 'already', 'never', 'always', 'often', 'sometimes',
        'usually', 'generally', 'commonly', 'typically', 'normally',
    }
    
    def __init__(self, max_length: int = MAX_TITLE_LENGTH, min_length: int = MIN_TITLE_LENGTH):
        """
        Initialize the title generator.
        
        Args:
            max_length: Maximum allowed title length (default: 100)
            min_length: Minimum recommended title length (default: 30)
        """
        self.max_length = max_length
        self.min_length = min_length
        self.keywords: List[str] = []
        self.engagement_score: float = 0.0
    
    def generate_title(
        self,
        content: str,
        keywords: Optional[List[str]] = None,
        use_engagement_words: bool = True,
        style: str = 'informative'
    ) -> TitleGenerationResult:
        """
        Generate an optimized title from content.
        
        Args:
            content: Input text describing the video
            keywords: Optional list of keywords to include
            use_engagement_words: Whether to include engagement-boosting words
            style: Title style ('informative', 'question', 'listicle', 'howto')
            
        Returns:
            TitleGenerationResult with the generated title
        """
        # Extract keywords from content if not provided
        if keywords is None:
            keywords = self._extract_keywords(content)
        
        self.keywords = keywords
        
        # Generate base title
        base_title = self._generate_base_title(content, keywords, style)
        
        # Add engagement words if requested
        if use_engagement_words:
            base_title = self._add_engagement_words(base_title, keywords)
        
        # Optimize title length
        optimized_title = self._optimize_title_length(base_title)
        
        # Calculate engagement score
        self.engagement_score = self._calculate_engagement_score(optimized_title)
        
        # Create result
        result = TitleGenerationResult(
            title=optimized_title,
            original_length=len(base_title),
            adjusted_length=len(optimized_title),
            keywords_used=keywords[:5],  # Top 5 keywords
            is_optimized=len(optimized_title) <= self.max_length,
            character_count=len(optimized_title)
        )
        
        return result
    
    def _extract_keywords(self, content: str) -> List[str]:
        """
        Extract relevant keywords from content.
        
        Args:
            content: Input text
            
        Returns:
            List of extracted keywords
        """
        # Remove punctuation and convert to lowercase
        content = re.sub(r'[^\w\s]', '', content.lower())
        
        # Split into words
        words = content.split()
        
        # Filter out stop words and short words
        keywords = [
            word for word in words
            if word not in self.STOP_WORDS and len(word) > 2
        ]
        
        # Count word frequencies
        word_counts = {}
        for word in keywords:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # Sort by frequency and return top keywords
        sorted_keywords = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Return unique keywords, prioritizing longer ones for specificity
        unique_keywords = []
        seen = set()
        for word, count in sorted_keywords:
            if word not in seen and len(word) > 3:
                unique_keywords.append(word)
                seen.add(word)
            if len(unique_keywords) >= 10:
                break
        
        return unique_keywords
    
    def _generate_base_title(self, content: str, keywords: List[str], style: str) -> str:
        """
        Generate a base title using the specified style.
        
        Args:
            content: Input content
            keywords: List of keywords
            style: Title style
            
        Returns:
            Base title string
        """
        if not keywords:
            return content[:self.max_length]
        
        primary_keyword = keywords[0] if keywords else "video"
        
        # Generate title based on style
        if style == 'question':
            return f"What is {primary_keyword}? Complete Guide"
        elif style == 'listicle':
            return f"Top 10 {primary_keyword} Tips You Need to Know"
        elif style == 'howto':
            return f"How to Master {primary_keyword} in 5 Steps"
        else:  # informative
            return f"{primary_keyword}: The Complete Guide"
    
    def _add_engagement_words(self, title: str, keywords: List[str]) -> str:
        """
        Add engagement-boosting words to the title.
        
        Args:
            title: Base title
            keywords: List of keywords
            
        Returns:
            Title with engagement words added
        """
        # Select engagement words based on keywords
        engagement_word = None
        for word in self.ENGAGEMENT_WORDS:
            if word.lower() not in title.lower():
                engagement_word = word
                break
        
        if engagement_word:
            # Add engagement word to the beginning
            return f"{engagement_word} {title}"
        
        return title
    
    def _optimize_title_length(self, title: str) -> str:
        """
        Optimize title to fit within character limits.
        
        Args:
            title: Input title
            
        Returns:
            Optimized title within character limits
        """
        # If title is within limits, return as is
        if self.min_length <= len(title) <= self.max_length:
            return title
        
        # If title is too long, truncate intelligently
        if len(title) > self.max_length:
            # Try to break at word boundaries
            words = title.split()
            optimized = []
            current_length = 0
            
            for word in words:
                if current_length + len(word) + 1 <= self.max_length:
                    optimized.append(word)
                    current_length += len(word) + 1
                else:
                    break
            
            # Add ellipsis if truncated
            if len(optimized) < len(words):
                optimized.append("...")
            
            return ' '.join(optimized)
        
        # If title is too short, pad with relevant keywords
        if len(title) < self.min_length:
            # Add more keywords
            additional_keywords = [
                kw for kw in self.keywords
                if kw.lower() not in title.lower()
            ]
            
            for keyword in additional_keywords:
                if len(title) + len(keyword) + 3 <= self.max_length:
                    title = f"{title} | {keyword}"
                else:
                    break
        
        return title
    
    def _calculate_engagement_score(self, title: str) -> float:
        """
        Calculate engagement score for a title.
        
        Args:
            title: Title to evaluate
            
        Returns:
            Engagement score between 0.0 and 1.0
        """
        score = 0.0
        
        # Check for engagement words
        engagement_words_in_title = [
            word for word in self.ENGAGEMENT_WORDS
            if word.lower() in title.lower()
        ]
        score += len(engagement_words_in_title) * 0.1
        
        # Check for keywords
        if self.keywords:
            keywords_in_title = [
                kw for kw in self.keywords
                if kw.lower() in title.lower()
            ]
            score += len(keywords_in_title) * 0.15
        
        # Check for numbers (listicles perform well)
        if re.search(r'\d+', title):
            score += 0.1
        
        # Check for question marks
        if '?' in title:
            score += 0.1
        
        # Normalize to 0-1 range
        return min(score, 1.0)
    
    def generate_multiple_titles(
        self,
        content: str,
        num_titles: int = 5,
        styles: Optional[List[str]] = None
    ) -> List[TitleGenerationResult]:
        """
        Generate multiple title variations.
        
        Args:
            content: Input content
            num_titles: Number of titles to generate
            styles: List of styles to use (if None, uses all styles)
            
        Returns:
            List of TitleGenerationResult objects
        """
        if styles is None:
            styles = ['informative', 'question', 'listicle', 'howto']
        
        titles = []
        for i in range(num_titles):
            style = styles[i % len(styles)]
            title_result = self.generate_title(content, style=style)
            titles.append(title_result)
        
        return titles
    
    def get_title_stats(self, title: str) -> Dict:
        """
        Get statistics for a title.
        
        Args:
            title: Title to analyze
            
        Returns:
            Dictionary with title statistics
        """
        return {
            'length': len(title),
            'character_count': len(title),
            'word_count': len(title.split()),
            'contains_numbers': bool(re.search(r'\d+', title)),
            'contains_question': '?' in title,
            'contains_engagement_word': any(
                word.lower() in title.lower()
                for word in self.ENGAGEMENT_WORDS
            ),
            'engagement_score': self._calculate_engagement_score(title),
            'within_limits': self.min_length <= len(title) <= self.max_length,
        }
