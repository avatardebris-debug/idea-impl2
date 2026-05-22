"""
Summary generator module for transcript extraction.

Provides the SummaryGenerator class for generating summaries from transcripts.
"""

from typing import Optional, List


class SummaryGenerator:
    """Generates summaries from transcript text."""
    
    def __init__(self, strategy: str = "extractive", length: str = "medium"):
        """
        Initialize the summary generator.
        
        Args:
            strategy: Summary strategy ('extractive', 'abstractive', 'simple').
            length: Summary length ('short', 'medium', 'long').
        """
        self.strategy = strategy
        self.length = length
    
    def generate(self, text: str, language: Optional[str] = None) -> dict:
        """
        Generate a summary from the given text.
        
        Args:
            text: The text to summarize.
            language: Language of the text (optional).
            
        Returns:
            Dictionary containing the summary.
        """
        if not text:
            return {"summary": "", "key_points": []}
        
        # Simple extractive summary based on text length
        words = text.split()
        
        if self.length == "short":
            num_sentences = max(1, len(words) // 10)
        elif self.length == "long":
            num_sentences = max(1, len(words) // 3)
        else:  # medium
            num_sentences = max(1, len(words) // 5)
        
        # Take first few sentences as summary
        sentences = text.split('. ')
        summary_sentences = sentences[:num_sentences]
        summary = '. '.join(summary_sentences)
        
        return {
            "summary": summary,
            "key_points": self.get_key_points(text, num_points=min(3, num_sentences))
        }
    
    def get_key_points(self, text: str, num_points: int = 3) -> List[str]:
        """
        Extract key points from the text.
        
        Args:
            text: The text to extract key points from.
            num_points: Number of key points to extract.
            
        Returns:
            List of key point strings.
        """
        if not text:
            return []
        
        sentences = [s.strip() for s in text.split('. ') if s.strip()]
        return sentences[:num_points]
    
    def update_strategy(self, strategy: str) -> None:
        """
        Update the summary strategy.
        
        Args:
            strategy: New strategy ('extractive', 'abstractive', 'simple').
        """
        self.strategy = strategy
    
    def update_length(self, length: str) -> None:
        """
        Update the summary length.
        
        Args:
            length: New length ('short', 'medium', 'long').
        """
        self.length = length
