"""
Summary strategies for transcript summarization.

Provides different approaches for generating summaries: extractive, abstractive, and length-based.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod


class SummaryStrategy(ABC):
    """Abstract base class for summarization strategies."""
    
    @abstractmethod
    def summarize(
        self,
        text: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Generate a summary from text.
        
        Args:
            text: Input text to summarize
            language: Language code for the text
            
        Returns:
            Dictionary with summary content and metadata
        """
        pass
    
    @abstractmethod
    def get_key_points(
        self,
        text: str,
        num_points: int = 5,
    ) -> List[str]:
        """
        Extract key points from text.
        
        Args:
            text: Input text
            num_points: Number of key points to extract
            
        Returns:
            List of key point strings
        """
        pass


class ExtractiveSummarizer(SummaryStrategy):
    """Extractive summarization - selects existing sentences from the text."""
    
    LENGTHS = {
        "short": 3,
        "medium": 5,
        "long": 10,
    }
    
    def __init__(self, max_sentences: Optional[int] = None, length: str = "medium"):
        """
        Initialize extractive summarizer.
        
        Args:
            max_sentences: Maximum number of sentences in summary
            length: Summary length category (short, medium, long)
        """
        if max_sentences is not None:
            self.max_sentences = max_sentences
        else:
            if length not in self.LENGTHS:
                raise ValueError(f"Invalid length: {length}. Must be one of: {list(self.LENGTHS.keys())}")
            self.max_sentences = self.LENGTHS[length]
    
    def _split_sentences(self, text: str) -> List[Tuple[str, int]]:
        """Split text into sentences with their positions."""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        positions = []
        current_pos = 0
        
        for i, sentence in enumerate(sentences):
            pos = text.find(sentence, current_pos)
            if pos != -1:
                positions.append((sentence, pos))
                current_pos = pos + len(sentence)
        
        return positions
    
    def _score_sentence(self, sentence: str, text: str) -> float:
        """Score a sentence based on its position and content."""
        # Position bias - earlier sentences often more important
        pos_score = 1.0 - (text.find(sentence) / len(text))
        
        # Length score - prefer medium-length sentences
        words = sentence.split()
        length_score = 1.0 / (1 + abs(len(words) - 15) * 0.05)
        
        # Keywords - prefer sentences with common important words
        keywords = ["important", "key", "main", "significant", "crucial"]
        keyword_score = sum(1 for kw in keywords if kw in sentence.lower()) * 0.1
        
        return pos_score * 0.5 + length_score * 0.3 + keyword_score * 0.2
    
    def summarize(
        self,
        text: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Generate extractive summary."""
        if not text or len(text.strip()) < 50:
            return {
                "summary": text if text else "",
                "key_points": [],
                "method": "extractive",
            }
        
        sentences_with_pos = self._split_sentences(text)
        if not sentences_with_pos:
            return {"summary": "", "key_points": [], "method": "extractive"}
        
        # Score and select sentences
        scored = [(self._score_sentence(sent, text), sent, pos) 
                  for sent, pos in sentences_with_pos]
        scored.sort(reverse=True, key=lambda x: x[0])
        
        # Select top sentences and sort by position
        selected = sorted(scored[:self.max_sentences], key=lambda x: x[2])
        summary = " ".join([s[1] for s in selected])
        
        # Extract key points
        key_points = [s[1].strip() for s in selected[:5]]
        
        return {
            "summary": summary,
            "key_points": key_points,
            "method": "extractive",
            "original_length": len(text),
            "summary_length": len(summary),
        }
    
    def get_key_points(
        self,
        text: str,
        num_points: int = 5,
    ) -> List[str]:
        """Extract key points using extractive method."""
        result = self.summarize(text)
        return result.get("key_points", [])[:num_points]


class AbstractiveSummarizer(SummaryStrategy):
    """
    Abstractive summarization - generates new sentences.
    
    Note: This is a simplified implementation. For production, 
    consider using transformer-based models like BART or T5.
    """
    
    LENGTHS = {
        "short": 100,
        "medium": 250,
        "long": 500,
    }
    
    def __init__(self, target_length: Optional[int] = None, length: str = "medium"):
        """
        Initialize abstractive summarizer.
        
        Args:
            target_length: Target summary length in characters
            length: Summary length category (short, medium, long)
        """
        if target_length is not None:
            self.target_length = target_length
        else:
            if length not in self.LENGTHS:
                raise ValueError(f"Invalid length: {length}. Must be one of: {list(self.LENGTHS.keys())}")
            self.target_length = self.LENGTHS[length]
    
    def summarize(
        self,
        text: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Generate abstractive summary using simplified approach."""
        if not text or len(text.strip()) < 50:
            return {
                "summary": text if text else "",
                "key_points": [],
                "method": "abstractive",
            }
        
        # For now, use a simplified approach
        # In production, use transformer models
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        if len(sentences) <= 3:
            return {
                "summary": text,
                "key_points": sentences,
                "method": "abstractive",
            }
        
        # Select representative sentences from different parts
        step = max(1, len(sentences) // 5)
        selected = sentences[::step][:5]
        
        # Create a pseudo-abstractive summary
        words = " ".join(selected).split()
        if len(words) > self.target_length // 10:
            words = words[:self.target_length // 10]
        
        summary = " ".join(words)
        
        # Extract key points
        key_points = [s.strip() for s in selected[:5]]
        
        return {
            "summary": summary,
            "key_points": key_points,
            "method": "abstractive",
            "original_length": len(text),
            "summary_length": len(summary),
        }
    
    def get_key_points(
        self,
        text: str,
        num_points: int = 5,
    ) -> List[str]:
        """Extract key points using abstractive method."""
        result = self.summarize(text)
        return result.get("key_points", [])[:num_points]


class SimpleLengthBasedSummarizer(SummaryStrategy):
    """Simple summarization based on text length."""
    
    LENGTHS = {
        "short": 100,
        "medium": 250,
        "long": 500,
    }
    
    def __init__(self, length: str = "medium"):
        """
        Initialize summarizer with target length.
        
        Args:
            length: Summary length category (short, medium, long)
        """
        if length not in self.LENGTHS:
            raise ValueError(f"Invalid length: {length}. Must be one of: {list(self.LENGTHS.keys())}")
        self.target_length = self.LENGTHS[length]
    
    def summarize(
        self,
        text: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """Generate summary based on target length."""
        if not text:
            return {"summary": "", "key_points": [], "method": "length_based"}
        
        # Get first N words that fit target length
        words = text.split()
        summary_words = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > self.target_length:
                break
            summary_words.append(word)
            current_length += len(word) + 1
        
        summary = " ".join(summary_words)
        
        # Extract key points (first few sentences)
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        key_points = sentences[:5]
        
        return {
            "summary": summary,
            "key_points": key_points,
            "method": "length_based",
            "target_length": self.target_length,
        }
    
    def get_key_points(
        self,
        text: str,
        num_points: int = 5,
    ) -> List[str]:
        """Extract key points."""
        result = self.summarize(text)
        return result.get("key_points", [])[:num_points]


def get_summarizer(strategy: str = "extractive", **kwargs) -> SummaryStrategy:
    """
    Factory function to get a summarizer instance.
    
    Args:
        strategy: Summarization strategy ('extractive', 'abstractive', 'simple')
        **kwargs: Additional arguments for the summarizer
        
    Returns:
        SummaryStrategy instance
    """
    if strategy == "extractive":
        return ExtractiveSummarizer(**kwargs)
    elif strategy == "abstractive":
        return AbstractiveSummarizer(**kwargs)
    elif strategy == "simple":
        return SimpleLengthBasedSummarizer(**kwargs)
    else:
        raise ValueError(f"Unknown summarization strategy: {strategy}")
