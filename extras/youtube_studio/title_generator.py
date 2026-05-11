"""Title generator for YouTube Studio.

This module provides functionality for generating optimized video titles
based on content analysis and proven title patterns.
"""

import re
from dataclasses import dataclass
from typing import List, Optional
from .config import get_config


@dataclass
class TitleGenerationResult:
    """Result of title generation.
    
    Attributes:
        title: The generated title.
        confidence: Quality score (0.0 to 1.0).
        style: The style category of the title.
        description: Description of why this title was chosen.
    """
    title: str
    confidence: float
    style: str
    description: str


class TitleGenerator:
    """Generator for optimized YouTube video titles.
    
    This class generates titles based on content analysis using
    proven patterns and styles that perform well on YouTube.
    """
    
    # Title patterns by style
    TITLE_PATTERNS = {
        'clickworthy': [
            'I Tried {topic} and Here\'s What Happened',
            'The Truth About {topic}',
            '{topic}: What Nobody Tells You',
            'Why {topic} is Changing Everything',
            'I Can\'t Believe {topic} Actually Works',
            'The Shocking Reality of {topic}',
            '{topic}: The Untold Story',
            'How {topic} Changed My Life Forever',
        ],
        'descriptive': [
            'Complete Guide to {topic}',
            '{topic} Explained Simply',
            'Everything About {topic} You Need to Know',
            '{topic}: A Comprehensive Overview',
            'Understanding {topic} - Full Breakdown',
            '{topic} Tutorial for Beginners',
            'The Ultimate {topic} Guide',
            '{topic} - Complete Walkthrough',
        ],
        'question': [
            'Is {topic} Worth It in 2024?',
            'What Exactly is {topic}? (Explained)',
            'Why Does {topic} Matter?',
            'How Does {topic} Actually Work?',
            'Can {topic} Really Help You?',
            'What Happens When You Try {topic}?',
            'Is {topic} the Future?',
            'Should You Learn {topic}?',
        ],
        'howto': [
            'How to Master {topic} in 10 Minutes',
            'How I Learned {topic} (Step by Step)',
            'How to Get Started with {topic}',
            'How to Use {topic} Like a Pro',
            'How to Fix {topic} (Easy Method)',
            'How to Choose the Best {topic}',
            'How to Improve Your {topic} Skills',
            'How to Start {topic} Today',
        ],
    }
    
    # Power words for titles
    POWER_WORDS = [
        'ultimate', 'essential', 'proven', 'secret', 'powerful',
        'amazing', 'incredible', 'revolutionary', 'game-changing',
        'must-know', 'life-changing', 'unbelievable', 'surprising',
        'shocking', 'brilliant', 'effective', 'complete', 'definitive',
    ]
    
    def __init__(self, max_length: int = 100):
        """Initialize title generator.
        
        Args:
            max_length: Maximum title length in characters.
        """
        self.max_length = max_length
        self.config = get_config()
    
    def generate_single_title(self, content: str) -> TitleGenerationResult:
        """Generate a single optimized title from content.
        
        Args:
            content: Input text describing the video content.
            
        Returns:
            TitleGenerationResult with the best title.
        """
        topics = self._extract_topics(content)
        style = self._select_style(content)
        title = self._generate_title(topics, style)
        score = self._score_title(title, content)
        
        return TitleGenerationResult(
            title=title,
            confidence=score,
            style=style,
            description=f"Generated {style} title based on content analysis"
        )
    
    def generate_multiple_titles(self, content: str, count: int = 5) -> List[TitleGenerationResult]:
        """Generate multiple title options.
        
        Args:
            content: Input text describing the video content.
            count: Number of titles to generate.
            
        Returns:
            List of TitleGenerationResult objects.
        """
        topics = self._extract_topics(content)
        results = []
        
        # Generate titles for each style
        styles = list(self.TITLE_PATTERNS.keys())
        for i in range(count):
            style = styles[i % len(styles)]
            title = self._generate_title(topics, style)
            score = self._score_title(title, content)
            
            results.append(TitleGenerationResult(
                title=title,
                score=score,
                style=style,
                description=f"Generated {style} title option {i+1}"
            ))
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results[:count]
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract key topics from content.
        
        Args:
            content: Input text.
            
        Returns:
            List of extracted topics.
        """
        # Simple topic extraction - in production, use NLP
        words = content.lower().split()
        
        # Filter common words
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
            word = re.sub(r'[^a-z0-9]', '', word)
            if word and word not in stop_words and len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top topics
        topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [topic[0] for topic in topics[:5]]
    
    def _select_style(self, content: str) -> str:
        """Select the best title style for the content.
        
        Args:
            content: Input text.
            
        Returns:
            Selected style name.
        """
        content_lower = content.lower()
        
        # Check for question indicators
        if any(word in content_lower for word in ['how', 'what', 'why', 'when', 'where', 'can', 'should', 'is', 'does']):
            return 'question'
        
        # Check for tutorial indicators
        if any(word in content_lower for word in ['tutorial', 'guide', 'how to', 'learn', 'step', 'process', 'method']):
            return 'howto'
        
        # Check for listicle indicators
        if any(word in content_lower for word in ['top', 'best', 'list', 'number', 'rank', 'review']):
            return 'descriptive'
        
        # Default to clickworthy
        return 'clickworthy'
    
    def _generate_title(self, topics: List[str], style: str) -> str:
        """Generate a title based on topics and style.
        
        Args:
            topics: List of extracted topics.
            style: Title style to use.
            
        Returns:
            Generated title string.
        """
        if not topics:
            return 'Amazing Video Content'
        
        # Get the main topic
        main_topic = topics[0].capitalize()
        
        # Get a pattern for the style
        patterns = self.TITLE_PATTERNS.get(style, self.TITLE_PATTERNS['clickworthy'])
        pattern = patterns[hash(main_topic) % len(patterns)]
        
        # Replace placeholder
        title = pattern.replace('{topic}', main_topic)
        
        # Add power word if title is short
        if len(title) < 40:
            power_word = self.POWER_WORDS[hash(main_topic) % len(self.POWER_WORDS)]
            title = f'{power_word.title()} {title}'
        
        # Enforce max length
        if len(title) > self.max_length:
            title = title[:self.max_length-3] + '...'
        
        return title
    
    def _score_title(self, title: str, content: str) -> float:
        """Score a title based on quality metrics.
        
        Args:
            title: Title to score.
            content: Original content.
            
        Returns:
            Score between 0.0 and 1.0.
        """
        score = 0.0
        
        # Length score (optimal is 50-70 characters)
        length = len(title)
        if 50 <= length <= 70:
            score += 0.3
        elif 40 <= length <= 80:
            score += 0.2
        else:
            score += 0.1
        
        # Power word score
        title_lower = title.lower()
        if any(word in title_lower for word in self.POWER_WORDS):
            score += 0.2
        
        # Topic relevance score
        topics = self._extract_topics(content)
        if topics:
            main_topic = topics[0].lower()
            if main_topic in title_lower:
                score += 0.3
        
        # Style-specific bonuses
        if '?' in title:
            score += 0.1  # Questions engage viewers
        
        if 'how' in title_lower or 'guide' in title_lower:
            score += 0.1  # How-to and guides are popular
        
        # Uniqueness bonus (avoid common patterns)
        common_patterns = ['the truth about', 'what nobody tells you', 'shocking reality']
        if not any(pattern in title_lower for pattern in common_patterns):
            score += 0.1
        
        return min(score, 1.0)
