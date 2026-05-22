"""
Summarizer module for transcript summarization.

Provides the SummaryGenerator class for generating summaries from transcripts.
"""

from .summarizers.summary_strategies import (
    SummaryStrategy,
    ExtractiveSummarizer,
    AbstractiveSummarizer,
    SimpleLengthBasedSummarizer,
    get_summarizer,
)

__all__ = [
    "SummaryGenerator",
    "SummaryStrategy",
    "ExtractiveSummarizer",
    "AbstractiveSummarizer",
    "SimpleLengthBasedSummarizer",
    "get_summarizer",
]


class SummaryGenerator:
    """
    Main summarization class for generating summaries from transcripts.
    
    This class provides a unified API for generating summaries using different
    strategies (extractive, abstractive, length-based).
    """
    
    def __init__(
        self,
        length: str = "medium",
        strategy: str = "extractive",
    ):
        """
        Initialize the summary generator.
        
        Args:
            length: Summary length (short, medium, long)
            strategy: Summarization strategy (extractive, abstractive, simple)
        """
        self.length = length
        self.strategy = strategy
        self._summarizer = get_summarizer(strategy, length=length)
    
    def generate(
        self,
        text: str,
        language: str = "en",
    ) -> dict:
        """
        Generate a summary from text.
        
        Args:
            text: Input text to summarize
            language: Language code for the text
            
        Returns:
            Dictionary with summary content and metadata
        """
        return self._summarizer.summarize(text, language=language)
    
    def get_key_points(
        self,
        text: str,
        num_points: int = 5,
    ) -> list:
        """
        Extract key points from text.
        
        Args:
            text: Input text
            num_points: Number of key points to extract
            
        Returns:
            List of key point strings
        """
        return self._summarizer.get_key_points(text, num_points=num_points)
    
    def update_strategy(self, strategy: str) -> None:
        """
        Update the summarization strategy.
        
        Args:
            strategy: New strategy name (extractive, abstractive, simple)
        """
        self.strategy = strategy
        self._summarizer = get_summarizer(strategy, length=self.length)
    
    def update_length(self, length: str) -> None:
        """
        Update the summary length.
        
        Args:
            length: New length (short, medium, long)
        """
        self.length = length
        self._summarizer = get_summarizer(self.strategy, length=length)
