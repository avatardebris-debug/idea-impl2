"""Keyword generator for YouTube Studio."""

from enum import Enum
from typing import List, Optional
from dataclasses import dataclass


class KeywordPriority(Enum):
    """Keyword priority levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class KeywordResult:
    """Result of keyword generation."""
    keywords: List[str]
    priorities: List[KeywordPriority]
    search_volume: List[int]
    competition: List[str]
    relevance_scores: List[float]


class KeywordGenerator:
    """Generates optimized keywords for YouTube videos."""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'shall', 'can',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'as', 'into', 'through', 'during', 'and', 'but', 'or', 'not'
        }
    
    def generate_keywords(self, content: str, count: int = 10) -> KeywordResult:
        """Generate keywords from content."""
        words = self._extract_keywords(content)
        
        # Filter and prioritize
        keywords = []
        priorities = []
        search_volumes = []
        competitions = []
        relevance_scores = []
        
        for i, word in enumerate(words[:count]):
            keywords.append(word)
            if i < count // 3:
                priorities.append(KeywordPriority.HIGH)
                search_volumes.append(1000 + i * 100)
                competitions.append('low')
                relevance_scores.append(0.9 - i * 0.05)
            elif i < 2 * count // 3:
                priorities.append(KeywordPriority.MEDIUM)
                search_volumes.append(500 + i * 50)
                competitions.append('medium')
                relevance_scores.append(0.7 - i * 0.03)
            else:
                priorities.append(KeywordPriority.LOW)
                search_volumes.append(100 + i * 10)
                competitions.append('high')
                relevance_scores.append(0.5 - i * 0.02)
        
        return KeywordResult(
            keywords=keywords,
            priorities=priorities,
            search_volume=search_volumes,
            competition=competitions,
            relevance_scores=relevance_scores
        )
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract meaningful keywords from content."""
        words = content.lower().split()
        keywords = [w for w in words if len(w) > 3 and w not in self.stop_words]
        return list(dict.fromkeys(keywords))  # Remove duplicates, preserve order
