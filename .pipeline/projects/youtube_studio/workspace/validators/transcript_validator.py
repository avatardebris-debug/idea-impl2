"""
Transcript Validator Module

This module provides the TranscriptValidator class for validating YouTube video
transcripts against quality, completeness, and SEO requirements.
"""

from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
import re


@dataclass
class TranscriptValidationResult:
    """Result of transcript validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    score: float  # 0.0 to 1.0
    suggestions: List[str]
    statistics: Dict[str, any]


class TranscriptValidator:
    """
    Validator for YouTube video transcripts.
    
    This class validates transcripts against quality standards,
    completeness requirements, and SEO optimization criteria.
    """
    
    # Transcript requirements
    MIN_WORD_COUNT = 50  # Minimum words for a valid transcript
    MAX_WORD_COUNT = 50000  # Maximum words for practical purposes
    MIN_SENTENCE_LENGTH = 3  # Minimum words per sentence
    
    # Quality requirements
    MIN_UNIQUE_WORD_RATIO = 0.1  # Minimum ratio of unique words
    MAX_REPETITION_RATIO = 0.3  # Maximum ratio of repeated words
    
    # SEO requirements
    MIN_KEYWORD_DENSITY = 0.005  # Minimum keyword density (0.5%)
    MAX_KEYWORD_DENSITY = 0.08  # Maximum keyword density (8%)
    
    # Formatting requirements
    MAX_LINE_LENGTH = 100  # Maximum characters per line
    MIN_LINES = 1  # Minimum number of lines
    
    def __init__(self):
        """Initialize the transcript validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
    
    def validate_transcript(
        self,
        transcript: str,
        target_keywords: Optional[List[str]] = None
    ) -> TranscriptValidationResult:
        """
        Validate a video transcript.
        
        Args:
            transcript: Transcript text to validate
            target_keywords: Optional list of target keywords
            
        Returns:
            TranscriptValidationResult with validation results
        """
        self.errors = []
        self.warnings = []
        self.suggestions = []
        
        # Run all validation checks
        self._check_completeness(transcript)
        self._check_quality(transcript)
        self._check_formatting(transcript)
        self._check_readability(transcript)
        self._check_seo(transcript, target_keywords)
        
        # Calculate statistics
        statistics = self._calculate_statistics(transcript)
        
        # Calculate score
        score = self._calculate_score(transcript, statistics)
        
        # Determine validity
        is_valid = len(self.errors) == 0
        
        return TranscriptValidationResult(
            is_valid=is_valid,
            errors=self.errors,
            warnings=self.warnings,
            score=score,
            suggestions=self.suggestions,
            statistics=statistics
        )
    
    def _check_completeness(self, transcript: str) -> None:
        """Check transcript completeness."""
        if not transcript or len(transcript.strip()) == 0:
            self.errors.append("Transcript is empty.")
            self.suggestions.append("Add a complete transcript for better SEO and accessibility")
            return
        
        # Check word count
        words = transcript.split()
        word_count = len(words)
        
        if word_count < self.MIN_WORD_COUNT:
            self.errors.append(
                f"Transcript is too short ({word_count} words). "
                f"Minimum recommended is {self.MIN_WORD_COUNT} words."
            )
            self.suggestions.append(
                "Add more content to the transcript"
            ]
        
        if word_count > self.MAX_WORD_COUNT:
            self.warnings.append(
                f"Transcript is very long ({word_count} words). "
                f"Consider breaking it into multiple videos."
            )
            self.suggestions.append(
                "Consider splitting into shorter, focused videos"
            ]
        
        # Check for complete sentences
        sentences = re.split(r'[.!?]+', transcript)
        incomplete_sentences = [s for s in sentences if s.strip() and len(s.strip().split()) < self.MIN_SENTENCE_LENGTH]
        
        if incomplete_sentences:
            self.warnings.append(
                f"Found {len(incomplete_sentences)} incomplete sentences."
            )
            self.suggestions.append(
                "Ensure all sentences are complete and grammatically correct"
            ]
    
    def _check_quality(self, transcript: str) -> None:
        """Check transcript quality metrics."""
        words = transcript.split()
        word_count = len(words)
        
        if word_count == 0:
            return
        
        # Check unique word ratio
        unique_words = set(w.lower() for w in words)
        unique_ratio = len(unique_words) / word_count
        
        if unique_ratio < self.MIN_UNIQUE_WORD_RATIO:
            self.warnings.append(
                f"Low unique word ratio ({unique_ratio:.1%}). "
                f"Transcript may be too repetitive."
            )
            self.suggestions.append(
                "Use more varied vocabulary"
            ]
        
        # Check for excessive repetition
        word_counts = {}
        for word in words:
            word_lower = word.lower()
            if word_lower not in self._get_stop_words():
                word_counts[word_lower] = word_counts.get(word_lower, 0) + 1
        
        max_repetition = max(word_counts.values()) / word_count if word_counts else 0
        
        if max_repetition > self.MAX_REPETITION_RATIO:
            most_repeated = max(word_counts, key=word_counts.get)
            self.warnings.append(
                f"Excessive repetition of '{most_repeated}' "
                f"({word_counts[most_repeated]} times)."
            )
            self.suggestions.append(
                "Reduce repetition by using synonyms or rephrasing"
            ]
        
        # Check for proper capitalization
        lines = transcript.split('\n')
        improper_cap = 0
        for line in lines:
            line = line.strip()
            if line and line[0].islower():
                improper_cap += 1
        
        if improper_cap > len(lines) * 0.5:
            self.warnings.append(
                "Many lines start with lowercase letters. "
                "This may indicate poor formatting."
            )
            self.suggestions.append(
                "Ensure each sentence starts with a capital letter"
            ]
    
    def _check_formatting(self, transcript: str) -> None:
        """Check transcript formatting."""
        lines = transcript.split('\n')
        
        # Check line lengths
        long_lines = [i+1 for i, line in enumerate(lines) if len(line) > self.MAX_LINE_LENGTH]
        
        if long_lines:
            self.warnings.append(
                f"Found {len(long_lines)} lines exceeding {self.MAX_LINE_LENGTH} characters."
            )
            self.suggestions.append(
                "Break long lines into shorter paragraphs"
            ]
        
        # Check for excessive whitespace
        excessive_whitespace = [i+1 for i, line in enumerate(lines) if len(line) > 0 and line != line.strip()]
        
        if excessive_whitespace:
            self.warnings.append(
                f"Found {len(excessive_whitespace)} lines with excessive whitespace."
            )
            self.suggestions.append(
                "Remove leading and trailing whitespace from lines"
            ]
        
        # Check for empty lines
        empty_lines = [i+1 for i, line in enumerate(lines) if not line.strip()]
        
        if len(empty_lines) > len(lines) * 0.3:
            self.warnings.append(
                f"Too many empty lines ({len(empty_lines)}). "
                "This may indicate formatting issues."
            )
            self.suggestions.append(
                "Remove unnecessary empty lines"
            ]
    
    def _check_readability(self, transcript: str) -> None:
        """Check transcript readability."""
        words = transcript.split()
        word_count = len(words)
        
        if word_count == 0:
            return
        
        # Calculate average sentence length
        sentences = re.split(r'[.!?]+', transcript)
        valid_sentences = [s for s in sentences if s.strip()]
        
        if not valid_sentences:
            return
        
        avg_sentence_length = sum(len(s.split()) for s in valid_sentences) / len(valid_sentences)
        
        if avg_sentence_length > 25:
            self.warnings.append(
                f"Average sentence length is {avg_sentence_length:.1f} words. "
                "Consider using shorter sentences for better readability."
            )
            self.suggestions.append(
                "Break long sentences into shorter ones"
            ]
        
        # Check for complex words (more than 3 syllables)
        complex_words = 0
        for word in words:
            if self._count_syllables(word) > 3:
                complex_words += 1
        
        complex_ratio = complex_words / word_count
        
        if complex_ratio > 0.15:
            self.warnings.append(
                f"High ratio of complex words ({complex_ratio:.1%}). "
                "Consider using simpler language for broader audience."
            )
            self.suggestions.append(
                "Use simpler words where possible"
            ]
    
    def _check_seo(
        self,
        transcript: str,
        target_keywords: Optional[List[str]] = None
    ) -> None:
        """Check transcript SEO optimization."""
        if not target_keywords:
            self.warnings.append(
                "No target keywords provided for SEO analysis."
            )
            self.suggestions.append(
                "Provide target keywords to optimize transcript for SEO"
            ]
            return
        
        words = transcript.split()
        word_count = len(words)
        
        if word_count == 0:
            return
        
        # Check keyword density
        for keyword in target_keywords:
            keyword_lower = keyword.lower()
            keyword_words = keyword_lower.split()
            
            # Count keyword occurrences
            count = 0
            for i in range(len(words) - len(keyword_words) + 1):
                if words[i:i+len(keyword_words)] == keyword_words:
                    count += 1
            
            density = count / word_count
            
            if density < self.MIN_KEYWORD_DENSITY:
                self.warnings.append(
                    f"Low keyword density for '{keyword}' ({density:.1%}). "
                    f"Recommended minimum is {self.MIN_KEYWORD_DENSITY:.1%}."
                )
                self.suggestions.append(
                    f"Incorporate '{keyword}' more naturally into the transcript"
                ]
            
            if density > self.MAX_KEYWORD_DENSITY:
                self.warnings.append(
                    f"High keyword density for '{keyword}' ({density:.1%}). "
                    f"Recommended maximum is {self.MAX_KEYWORD_DENSITY:.1%}."
                )
                self.suggestions.append(
                    f"Reduce usage of '{keyword}' to avoid keyword stuffing"
                ]
        
        # Check for keyword placement
        first_paragraph = transcript.split('\n')[0] if transcript.split('\n') else ""
        first_paragraph_words = first_paragraph.split()
        
        for keyword in target_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in first_paragraph.lower():
                pass  # Good, keyword in first paragraph
            else:
                self.warnings.append(
                    f"Keyword '{keyword}' not found in the first paragraph."
                )
                self.suggestions.append(
                    f"Include '{keyword}' in the first paragraph for better SEO"
                ]
    
    def _calculate_statistics(self, transcript: str) -> Dict[str, any]:
        """Calculate transcript statistics."""
        words = transcript.split()
        word_count = len(words)
        
        sentences = re.split(r'[.!?]+', transcript)
        valid_sentences = [s for s in sentences if s.strip()]
        sentence_count = len(valid_sentences)
        
        paragraphs = [p for p in transcript.split('\n') if p.strip()]
        paragraph_count = len(paragraphs)
        
        unique_words = set(w.lower() for w in words)
        unique_word_count = len(unique_words)
        
        avg_sentence_length = sum(len(s.split()) for s in valid_sentences) / sentence_count if sentence_count > 0 else 0
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'paragraph_count': paragraph_count,
            'unique_word_count': unique_word_count,
            'avg_sentence_length': avg_sentence_length,
            'readability_score': self._calculate_readability_score(transcript),
        }
    
    def _calculate_readability_score(self, transcript: str) -> float:
        """
        Calculate a simple readability score.
        
        Args:
            transcript: Transcript text
            
        Returns:
            Readability score between 0 and 100
        """
        words = transcript.split()
        word_count = len(words)
        
        if word_count == 0:
            return 0
        
        sentences = re.split(r'[.!?]+', transcript)
        valid_sentences = [s for s in sentences if s.strip()]
        sentence_count = len(valid_sentences)
        
        if sentence_count == 0:
            return 0
        
        # Simple Flesch-Kincaid approximation
        avg_sentence_length = word_count / sentence_count
        avg_syllables_per_word = self._calculate_avg_syllables(words)
        
        # Flesch Reading Ease formula (simplified)
        score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word
        
        # Normalize to 0-100
        score = max(0, min(100, score))
        
        return score
    
    def _calculate_avg_syllables(self, words: List[str]) -> float:
        """Calculate average syllables per word."""
        total_syllables = 0
        count = 0
        
        for word in words:
            syllables = self._count_syllables(word)
            if syllables > 0:
                total_syllables += syllables
                count += 1
        
        return total_syllables / count if count > 0 else 0
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (approximation)."""
        word = word.lower().strip()
        
        if not word:
            return 0
        
        # Count vowel groups
        vowels = 'aeiouy'
        count = 0
        prev_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        
        # Adjust for silent e
        if word.endswith('e') and count > 1:
            count -= 1
        
        # Adjust for le endings
        if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
            count += 1
        
        return max(1, count)
    
    def _get_stop_words(self) -> set:
        """Get list of stop words."""
        return {
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
    
    def _calculate_score(
        self,
        transcript: str,
        statistics: Dict[str, any]
    ) -> float:
        """
        Calculate overall validation score.
        
        Args:
            transcript: Transcript text
            statistics: Transcript statistics
            
        Returns:
            Score between 0.0 and 1.0
        """
        score = 1.0
        
        # Deduct points for errors
        score -= len(self.errors) * 0.2
        
        # Deduct points for warnings
        score -= len(self.warnings) * 0.05
        
        # Bonus for good readability
        readability = statistics.get('readability_score', 0)
        if readability > 60:
            score += 0.1
        
        # Bonus for adequate word count
        word_count = statistics.get('word_count', 0)
        if 100 <= word_count <= 5000:
            score += 0.1
        
        # Bonus for good unique word ratio
        unique_ratio = statistics.get('unique_word_count', 0) / statistics.get('word_count', 1)
        if unique_ratio > 0.3:
            score += 0.05
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def get_improvement_suggestions(self, transcript: str) -> List[str]:
        """
        Get specific improvement suggestions for a transcript.
        
        Args:
            transcript: Transcript text to improve
            
        Returns:
            List of improvement suggestions
        """
        result = self.validate_transcript(transcript)
        return result.suggestions
    
    def compare_transcripts(
        self,
        transcript1: str,
        transcript2: str,
        target_keywords: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Compare two transcripts and return which is better.
        
        Args:
            transcript1: First transcript to compare
            transcript2: Second transcript to compare
            target_keywords: Optional list of target keywords
            
        Returns:
            Dictionary with comparison results
        """
        result1 = self.validate_transcript(transcript1, target_keywords)
        result2 = self.validate_transcript(transcript2, target_keywords)
        
        return {
            'transcript1_score': result1.score,
            'transcript2_score': result2.score,
            'better_transcript': 'transcript1' if result1.score > result2.score else 'transcript2',
            'transcript1_errors': len(result1.errors),
            'transcript2_errors': len(result2.errors),
            'transcript1_warnings': len(result1.warnings),
            'transcript2_warnings': len(result2.warnings),
            'transcript1_suggestions': result1.suggestions,
            'transcript2_suggestions': result2.suggestions,
            'transcript1_statistics': result1.statistics,
            'transcript2_statistics': result2.statistics,
        }
