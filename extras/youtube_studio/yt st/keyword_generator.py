"""Keyword generator for YouTube Studio.

This module provides keyword generation and optimization functionality
for YouTube video metadata.
"""

import re
import random
from typing import List, Dict, Optional
from collections import Counter


class KeywordGenerator:
    """Generates and optimizes keywords for YouTube videos."""
    
    def __init__(self):
        """Initialize keyword generator."""
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'shall', 'it', 'its',
            'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
    
    def generate_keywords(self, content: str, category: str = 'general', count: int = 10) -> List[Dict[str, object]]:
        """Generate keywords from content.
        
        Args:
            content: The content to generate keywords from
            category: The category of the content
            count: Number of keywords to generate
            
        Returns:
            List of keyword dictionaries with 'keyword' and 'score' keys
        """
        if not content or not content.strip():
            # Return generic keywords for empty content
            return self._get_generic_keywords(count, category)
        
        # Extract meaningful words
        words = self._extract_meaningful_words(content)
        
        # Generate keyword phrases
        keywords = self._generate_keyword_phrases(words, count)
        
        # Calculate relevance scores
        scored_keywords = self._score_keywords(keywords, content)
        
        # Sort by score and return top results
        scored_keywords.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_keywords[:count]
    
    def _extract_meaningful_words(self, content: str) -> List[str]:
        """Extract meaningful words from content."""
        # Convert to lowercase and remove punctuation
        text = content.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split into words and filter
        words = text.split()
        meaningful_words = [
            word for word in words 
            if word not in self.stop_words and len(word) > 2
        ]
        
        return meaningful_words
    
    def _generate_keyword_phrases(self, words: List[str], count: int) -> List[str]:
        """Generate keyword phrases from words."""
        if not words:
            return []
        
        # Create single-word keywords
        keywords = list(set(words))
        
        # Create two-word phrases
        for i in range(len(words)):
            for j in range(i + 1, min(i + 3, len(words))):
                phrase = f"{words[i]} {words[j]}"
                if phrase not in keywords:
                    keywords.append(phrase)
        
        # Create three-word phrases
        for i in range(len(words)):
            for j in range(i + 1, min(i + 2, len(words))):
                for k in range(j + 1, min(j + 2, len(words))):
                    phrase = f"{words[i]} {words[j]} {words[k]}"
                    if phrase not in keywords:
                        keywords.append(phrase)
        
        # Remove duplicates and limit count
        keywords = list(set(keywords))
        
        # If we don't have enough keywords, add variations
        while len(keywords) < count:
            # Add common prefixes/suffixes
            for word in words[:5]:
                variations = [
                    f"best {word}",
                    f"top {word}",
                    f"{word} tutorial",
                    f"{word} guide",
                    f"{word} tips",
                    f"{word} review",
                    f"{word} 2024",
                    f"{word} for beginners"
                ]
                for var in variations:
                    if var not in keywords:
                        keywords.append(var)
                        if len(keywords) >= count:
                            break
                if len(keywords) >= count:
                    break
        
        return keywords[:count * 2]  # Return more than needed for scoring
    
    def _score_keywords(self, keywords: List[str], content: str) -> List[Dict[str, object]]:
        """Score keywords based on relevance to content."""
        scored_keywords = []
        
        # Count word frequencies in content
        words = re.findall(r'\b[a-zA-Z0-9]+\b', content.lower())
        word_counts = Counter(words)
        
        for keyword in keywords:
            score = 0
            keyword_words = keyword.lower().split()
            
            # Score based on word frequency in content
            for word in keyword_words:
                if word in word_counts:
                    score += word_counts[word]
            
            # Bonus for exact matches
            if keyword.lower() in content.lower():
                score += 10
            
            # Normalize score
            score = min(score, 100)
            
            scored_keywords.append({
                'keyword': keyword,
                'score': score
            })
        
        return scored_keywords
    
    def _get_generic_keywords(self, count: int, category: str) -> List[Dict[str, object]]:
        """Get generic keywords for empty content."""
        generic_keywords = {
            'general': ['video', 'content', 'youtube', 'channel', 'subscriber'],
            'education': ['learn', 'tutorial', 'course', 'lesson', 'teaching'],
            'entertainment': ['fun', 'comedy', 'music', 'movie', 'game'],
            'technology': ['tech', 'software', 'hardware', 'gadget', 'review'],
            'lifestyle': ['life', 'daily', 'routine', 'tips', 'advice'],
            'gaming': ['game', 'gamer', 'play', 'stream', 'esports'],
            'fitness': ['workout', 'exercise', 'health', 'training', 'muscle'],
            'food': ['recipe', 'cooking', 'food', 'meal', 'kitchen'],
            'travel': ['travel', 'trip', 'destination', 'adventure', 'tourism'],
            'beauty': ['makeup', 'skincare', 'fashion', 'style', 'beauty']
        }
        
        keywords = generic_keywords.get(category, generic_keywords['general'])
        
        # Add some variations
        variations = [
            f"{kw} tips",
            f"{kw} guide",
            f"{kw} tutorial",
            f"best {kw}",
            f"{kw} 2024"
        ]
        
        all_keywords = keywords + variations
        all_keywords = list(set(all_keywords))
        
        # Score all keywords equally
        return [{'keyword': kw, 'score': 50} for kw in all_keywords[:count]]
    
    def optimize_tags(self, tags: List[str], keywords: List[Dict[str, object]]) -> List[str]:
        """Optimize tags using generated keywords.
        
        Args:
            tags: Current tags
            keywords: Generated keywords
            
        Returns:
            Optimized list of tags
        """
        if not keywords:
            return tags
        
        # Get top keywords
        top_keywords = [kw['keyword'] for kw in keywords[:10]]
        
        # Combine with existing tags, removing duplicates
        optimized_tags = list(set(tags + top_keywords))
        
        # Limit to 15 tags
        optimized_tags = optimized_tags[:15]
        
        return optimized_tags
    
    def get_keyword_suggestions(self, title: str, description: str) -> List[str]:
        """Get keyword suggestions based on title and description.
        
        Args:
            title: Video title
            description: Video description
            
        Returns:
            List of keyword suggestions
        """
        content = f"{title} {description}"
        keywords = self.generate_keywords(content, count=20)
        
        return [kw['keyword'] for kw in keywords]
