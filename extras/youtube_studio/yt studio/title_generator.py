"""Title generator for YouTube Studio."""

import random
from typing import List, Optional


class TitleGenerator:
    """Generates optimized video titles."""
    
    POWER_WORDS = [
        'Ultimate', 'Complete', 'Essential', 'Proven', 'Effective',
        'Easy', 'Quick', 'Fast', 'Simple', 'Beginner', 'Advanced',
        'Master', 'Guide', 'Tutorial', 'Tips', 'Tricks', 'Secrets'
    ]
    
    def generate_titles(self, content: str, count: int = 5) -> List[str]:
        """Generate multiple title options."""
        titles = []
        keywords = self._extract_keywords(content)
        
        for i in range(count):
            title = self._create_title(keywords, content)
            titles.append(title)
        
        return titles
    
    def generate_single_title(self, content: str) -> str:
        """Generate a single optimized title."""
        titles = self.generate_titles(content, 1)
        return titles[0]
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content."""
        words = content.lower().split()
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                      'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                      'would', 'could', 'should', 'may', 'might', 'shall', 'can',
                      'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
                      'as', 'into', 'through', 'during', 'before', 'after', 'and',
                      'but', 'or', 'nor', 'not', 'so', 'yet', 'both', 'either',
                      'neither', 'each', 'every', 'all', 'any', 'few', 'more',
                      'most', 'other', 'some', 'such', 'no', 'only', 'own', 'same',
                      'than', 'too', 'very', 'just', 'because', 'if', 'when',
                      'where', 'how', 'what', 'which', 'who', 'whom', 'this',
                      'that', 'these', 'those', 'i', 'me', 'my', 'myself', 'we',
                      'our', 'ours', 'you', 'your', 'he', 'him', 'his', 'she',
                      'her', 'it', 'its', 'they', 'them', 'their'}
        
        keywords = [w for w in words if len(w) > 3 and w not in stop_words]
        return list(set(keywords))[:10]
    
    def _create_title(self, keywords: List[str], content: str) -> str:
        """Create a title from keywords."""
        if not keywords:
            words = content.split()[:3]
            keywords = [w.capitalize() for w in words if len(w) > 2]
        
        title_parts = []
        
        if random.random() > 0.5:
            power_word = random.choice(self.POWER_WORDS)
            title_parts.append(power_word)
        
        title_parts.extend(keywords[:3])
        
        title = ' '.join(title_parts)
        return title.capitalize()
