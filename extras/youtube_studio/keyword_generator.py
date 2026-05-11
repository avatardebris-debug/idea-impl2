"""Keyword generator for YouTube Studio.

This module provides functionality for generating optimized video keywords
and tags based on content analysis.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
from .constants import MIN_NUMBER_OF_KEYWORDS, MAX_NUMBER_OF_KEYWORDS


class KeywordPriority(Enum):
    """Keyword priority levels."""
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


@dataclass
class KeywordResult:
    """Result of keyword generation.
    
    Attributes:
        keyword: The keyword/tag.
        priority: Priority level.
        relevance: Relevance score (0.0 to 1.0).
        search_volume: Estimated search volume category.
        description: Description of why this keyword was chosen.
    """
    keyword: str
    priority: KeywordPriority
    relevance: float
    search_volume: str
    description: str


class KeywordGenerator:
    """Generator for YouTube video keywords and tags.
    
    This class generates optimized keywords based on content analysis,
    keyword relationships, and YouTube SEO best practices.
    """
    
    # Common keyword prefixes and suffixes
    KEYWORD_MODIFIERS = {
        'prefixes': [
            'best', 'top', 'how to', 'what is', 'why', 'guide',
            'tutorial', 'review', 'tips', 'tricks', 'secrets',
            'beginner', 'advanced', 'easy', 'quick', 'fast',
            'complete', 'ultimate', 'essential', 'proven',
        ],
        'suffixes': [
            'tutorial', 'guide', 'tips', 'tricks', 'explained',
            'for beginners', 'step by step', 'full guide',
            'in 2024', 'made easy', 'demystified', 'simplified',
            'review', 'comparison', 'alternatives', 'vs',
        ],
    }
    
    # Keyword relationship types
    RELATIONSHIP_TYPES = [
        'synonym',
        'related',
        'long_tail',
        'broad',
        'specific',
        'question',
    ]
    
    def __init__(self, min_keywords: int = MIN_NUMBER_OF_KEYWORDS,
                 max_keywords: int = MAX_NUMBER_OF_KEYWORDS):
        """Initialize keyword generator.
        
        Args:
            min_keywords: Minimum number of keywords to generate.
            max_keywords: Maximum number of keywords to generate.
        """
        self.min_keywords = min_keywords
        self.max_keywords = max_keywords
    
    def generate_keywords(self, content: str, num_keywords: int = 15) -> List[KeywordResult]:
        """Generate keywords based on content.
        
        Args:
            content: Video content description.
            num_keywords: Number of keywords to generate.
            
        Returns:
            List of KeywordResult objects.
        """
        # Extract base keywords
        base_keywords = self._extract_base_keywords(content)
        
        # Generate variations
        all_keywords = []
        for base in base_keywords:
            all_keywords.extend(self._generate_variations(base, content))
        
        # Remove duplicates and filter
        seen = set()
        unique_keywords = []
        for kw in all_keywords:
            kw_lower = kw.lower().strip()
            if kw_lower and kw_lower not in seen:
                seen.add(kw_lower)
                unique_keywords.append(kw)
        
        # Score and prioritize
        scored_keywords = []
        for kw in unique_keywords:
            result = self._score_keyword(kw, content)
            scored_keywords.append(result)
        
        # Sort by priority and relevance
        priority_order = {KeywordPriority.HIGH: 0, KeywordPriority.MEDIUM: 1, KeywordPriority.LOW: 2}
        scored_keywords.sort(key=lambda x: (priority_order[x.priority], -x.relevance))
        
        # Return requested number
        return scored_keywords[:num_keywords]
    
    def _extract_base_keywords(self, content: str) -> List[str]:
        """Extract base keywords from content.
        
        Args:
            content: Video content description.
            
        Returns:
            List of base keywords.
        """
        # Simple keyword extraction
        words = content.lower().split()
        
        # Common stop words to filter
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
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
            'they', 'them', 'their', 'theirs', 'themselves',
        }
        
        # Count word frequency
        word_freq = {}
        for word in words:
            word = word.strip('.,!?;:()[]{}\'"')
            if word and word not in stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top keywords
        keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [kw[0] for kw in keywords[:10]]
    
    def _generate_variations(self, base_keyword: str, content: str) -> List[str]:
        """Generate keyword variations from a base keyword.
        
        Args:
            base_keyword: Base keyword.
            content: Video content description.
            
        Returns:
            List of keyword variations.
        """
        variations = []
        
        # Add base keyword
        variations.append(base_keyword)
        
        # Add with prefixes
        for prefix in self.KEYWORD_MODIFIERS['prefixes'][:5]:
            variations.append(f'{prefix} {base_keyword}')
        
        # Add with suffixes
        for suffix in self.KEYWORD_MODIFIERS['suffixes'][:5]:
            variations.append(f'{base_keyword} {suffix}')
        
        # Add question form
        variations.append(f'what is {base_keyword}')
        variations.append(f'how to use {base_keyword}')
        variations.append(f'why {base_keyword}')
        
        # Add related terms from content
        related = self._find_related_terms(base_keyword, content)
        for term in related:
            variations.append(f'{base_keyword} {term}')
        
        return variations
    
    def _find_related_terms(self, base_keyword: str, content: str) -> List[str]:
        """Find related terms in content.
        
        Args:
            base_keyword: Base keyword.
            content: Video content description.
            
        Returns:
            List of related terms.
        """
        # Simple related term extraction
        words = content.lower().split()
        base_words = base_keyword.split()
        
        # Find words that appear near the base keyword
        related = []
        for i, word in enumerate(words):
            word = word.strip('.,!?;:()[]{}\'"')
            if word and len(word) > 3:
                # Check if word is within 3 words of base keyword
                for base_word in base_words:
                    for j, base in enumerate(words):
                        base = base.strip('.,!?;:()[]{}\'"')
                        if base == base_word and abs(i - j) <= 3:
                            if word != base_word and word not in related:
                                related.append(word)
        
        return related[:5]
    
    def _score_keyword(self, keyword: str, content: str) -> KeywordResult:
        """Score a keyword based on relevance and priority.
        
        Args:
            keyword: Keyword to score.
            content: Video content description.
            
        Returns:
            KeywordResult with score and priority.
        """
        relevance = 0.0
        priority = KeywordPriority.LOW
        search_volume = 'medium'
        
        # Calculate relevance
        content_lower = content.lower()
        keyword_lower = keyword.lower()
        
        # Exact match in content
        if keyword_lower in content_lower:
            relevance += 0.4
        
        # Word by word match
        keyword_words = keyword_lower.split()
        content_words = content_lower.split()
        word_matches = sum(1 for word in keyword_words if word in content_words)
        relevance += (word_matches / len(keyword_words)) * 0.3 if keyword_words else 0
        
        # Length bonus (longer keywords often more specific)
        if len(keyword) > 10:
            relevance += 0.1
        
        # Priority determination
        if relevance >= 0.7:
            priority = KeywordPriority.HIGH
            search_volume = 'high'
        elif relevance >= 0.4:
            priority = KeywordPriority.MEDIUM
            search_volume = 'medium'
        else:
            priority = KeywordPriority.LOW
            search_volume = 'low'
        
        # Generate description
        description = self._generate_description(keyword, relevance)
        
        return KeywordResult(
            keyword=keyword,
            priority=priority,
            relevance=relevance,
            search_volume=search_volume,
            description=description,
        )
    
    def _generate_description(self, keyword: str, relevance: float) -> str:
        """Generate description for a keyword.
        
        Args:
            keyword: The keyword.
            relevance: Relevance score.
            
        Returns:
            Description string.
        """
        if relevance >= 0.7:
            return f'Highly relevant to video content'
        elif relevance >= 0.4:
            return f'Related to video content'
        else:
            return f'Broadly related to video content'
