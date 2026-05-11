"""
Keyword Generator Module

This module provides the KeywordGenerator class for extracting and generating
relevant YouTube keywords/tags from video content.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import Counter
import re


class KeywordPriority(Enum):
    """Keyword priority levels"""
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'


@dataclass
class KeywordResult:
    """Result of keyword generation"""
    keyword: str
    priority: KeywordPriority
    relevance_score: float
    character_count: int


class KeywordGenerator:
    """
    Generator for creating relevant YouTube keywords and tags.
    
    This class extracts keywords from content, generates variations,
    and prioritizes them based on relevance.
    """
    
    # YouTube tag limits
    MAX_TAG_LENGTH = 50  # Characters per tag
    MAX_TOTAL_KEYWORDS = 500  # Total character limit for all tags
    
    # Stop words to exclude
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'my', 'your', 'his', 'her', 'its', 'our', 'their', 'me', 'him',
        'us', 'them', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
    }
    
    # Keyword categories for different content types
    KEYWORD_CATEGORIES = {
        'tutorial': ['tutorial', 'guide', 'how to', 'learn', 'step by step', 'beginner'],
        'review': ['review', 'best', 'top', 'comparison', 'versus', 'rating'],
        'tips': ['tips', 'tricks', 'hacks', 'secrets', 'pro tips', 'quick tips'],
        'news': ['news', 'update', 'breaking', 'latest', 'today', 'current'],
        'entertainment': ['funny', 'entertainment', 'viral', 'trending', 'popular', 'amazing'],
        'education': ['learn', 'education', 'course', 'class', 'training', 'workshop'],
        'technology': ['tech', 'technology', 'gadget', 'review', 'unboxing', 'setup'],
        'lifestyle': ['lifestyle', 'daily', 'vlog', 'routine', 'tips', 'day in the life'],
    }
    
    def __init__(self, min_keywords: int = 10, max_keywords: int = MAX_TOTAL_KEYWORDS):
        """
        Initialize the keyword generator.
        
        Args:
            min_keywords: Minimum number of keywords to generate
            max_keywords: Maximum total character count for keywords
        """
        self.min_keywords = min_keywords
        self.max_keywords = max_keywords
    
    def generate_keywords(self, content: str, num_keywords: Optional[int] = None) -> List[KeywordResult]:
        """
        Generate keywords from input content.
        
        Args:
            content: Input text describing the video content
            num_keywords: Number of keywords to generate (defaults to min_keywords)
            
        Returns:
            List of KeywordResult objects
        """
        if num_keywords is None:
            num_keywords = self.min_keywords
        
        # Extract words from content
        words = self._extract_words(content)
        
        # Calculate word frequencies
        word_freq = Counter(words)
        
        # Generate candidate keywords
        candidates = self._generate_candidates(words, word_freq, content)
        
        # Score and prioritize keywords
        scored_keywords = self._score_keywords(candidates, content)
        
        # Filter and limit results
        results = self._filter_and_limit(scored_keywords, num_keywords)
        
        return results
    
    def _extract_words(self, content: str) -> List[str]:
        """
        Extract meaningful words from content.
        
        Args:
            content: Input text
            
        Returns:
            List of cleaned words
        """
        # Convert to lowercase and remove punctuation
        content = content.lower()
        content = re.sub(r'[^\w\s]', ' ', content)
        
        # Split into words and filter
        words = content.split()
        words = [w for w in words if len(w) > 2 and w not in self.STOP_WORDS]
        
        return words
    
    def _generate_candidates(self, words: List[str], word_freq: Counter, content: str) -> List[str]:
        """
        Generate candidate keywords from words.
        
        Args:
            words: List of extracted words
            word_freq: Word frequency counter
            content: Original content for phrase matching
            
        Returns:
            List of candidate keywords
        """
        candidates = set()
        
        # Add individual high-frequency words
        for word, freq in word_freq.most_common(20):
            candidates.add(word)
        
        # Add bigrams (pairs of consecutive words)
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if len(bigram) <= self.MAX_TAG_LENGTH:
                candidates.add(bigram)
        
        # Add trigrams (triples of consecutive words)
        for i in range(len(words) - 2):
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            if len(trigram) <= self.MAX_TAG_LENGTH:
                candidates.add(trigram)
        
        # Add common phrases
        common_phrases = [
            'how to', 'best way', 'top 10', 'ultimate guide', 'complete guide',
            'step by step', 'for beginners', 'easy', 'quick', 'simple',
            'tutorial', 'guide', 'review', 'tips', 'tricks', 'hacks'
        ]
        
        for phrase in common_phrases:
            if phrase in content.lower():
                candidates.add(phrase)
        
        return list(candidates)
    
    def _score_keywords(self, candidates: List[str], content: str) -> List[Tuple[str, float]]:
        """
        Score keywords based on relevance.
        
        Args:
            candidates: List of candidate keywords
            content: Original content
            
        Returns:
            List of (keyword, score) tuples
        """
        scored = []
        
        for keyword in candidates:
            score = 0.0
            
            # Score based on frequency in content
            keyword_lower = keyword.lower()
            content_lower = content.lower()
            
            # Count occurrences
            occurrences = content_lower.count(keyword_lower)
            score += occurrences * 2.0
            
            # Bonus for exact matches
            if keyword_lower in content_lower:
                score += 1.0
            
            # Bonus for longer keywords (more specific)
            if len(keyword) > 10:
                score += 0.5
            
            # Check against keyword categories
            for category, keywords in self.KEYWORD_CATEGORIES.items():
                if any(kw in keyword_lower for kw in keywords):
                    score += 1.0
            
            # Normalize score
            score = min(score, 10.0)  # Cap at 10
            
            scored.append((keyword, score))
        
        return scored
    
    def _filter_and_limit(self, scored_keywords: List[Tuple[str, float]], num_keywords: int) -> List[KeywordResult]:
        """
        Filter and limit keyword results.
        
        Args:
            scored_keywords: List of (keyword, score) tuples
            num_keywords: Number of keywords to return
            
        Returns:
            List of KeywordResult objects
        """
        # Sort by score descending
        scored_keywords.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by minimum score
        min_score = scored_keywords[min(num_keywords - 1, len(scored_keywords) - 1)][1] if scored_keywords else 0
        filtered = [(kw, score) for kw, score in scored_keywords if score >= min_score]
        
        # Limit to requested number
        filtered = filtered[:num_keywords]
        
        # Create KeywordResult objects
        results = []
        for keyword, score in filtered:
            # Determine priority based on score
            if score >= 7.0:
                priority = KeywordPriority.HIGH
            elif score >= 4.0:
                priority = KeywordPriority.MEDIUM
            else:
                priority = KeywordPriority.LOW
            
            result = KeywordResult(
                keyword=keyword,
                priority=priority,
                relevance_score=round(score / 10.0, 2),
                character_count=len(keyword)
            )
            results.append(result)
        
        return results
    
    def get_keyword_suggestions(self, topic: str) -> List[str]:
        """
        Get keyword suggestions for a topic.
        
        Args:
            topic: Topic to generate suggestions for
            
        Returns:
            List of keyword suggestions
        """
        suggestions = []
        
        # Generate variations
        base_keywords = topic.lower().split()
        
        for kw in base_keywords:
            suggestions.extend([
                f"{kw} tutorial",
                f"{kw} guide",
                f"best {kw}",
                f"{kw} tips",
                f"{kw} for beginners",
                f"how to {kw}",
                f"{kw} review",
                f"{kw} explained",
            ])
        
        # Remove duplicates and limit
        suggestions = list(set(suggestions))
        return suggestions[:20]
    
    def validate_keywords(self, keywords: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate a list of keywords.
        
        Args:
            keywords: List of keywords to validate
            
        Returns:
            Tuple of (valid_keywords, invalid_keywords)
        """
        valid = []
        invalid = []
        
        for keyword in keywords:
            # Check length
            if len(keyword) > self.MAX_TAG_LENGTH:
                invalid.append(keyword)
                continue
            
            # Check for valid characters
            if not re.match(r'^[\w\s\-]+$', keyword):
                invalid.append(keyword)
                continue
            
            valid.append(keyword)
        
        return valid, invalid
    
    def get_total_keyword_length(self, keywords: List[str]) -> int:
        """
        Get total character count for a list of keywords.
        
        Args:
            keywords: List of keywords
            
        Returns:
            Total character count
        """
        return sum(len(kw) for kw in keywords)
    
    def optimize_for_youtube(self, keywords: List[str]) -> List[str]:
        """
        Optimize keywords for YouTube's tag system.
        
        Args:
            keywords: List of keywords
            
        Returns:
            Optimized list of keywords
        """
        valid, _ = self.validate_keywords(keywords)
        
        # Sort by length (shorter first to fit more tags)
        valid.sort(key=len)
        
        # Ensure we don't exceed YouTube's limit
        total_length = 0
        optimized = []
        
        for kw in valid:
            if total_length + len(kw) + 1 <= self.MAX_TOTAL_KEYWORDS:  # +1 for comma
                optimized.append(kw)
                total_length += len(kw) + 1
            else:
                break
        
        return optimized
