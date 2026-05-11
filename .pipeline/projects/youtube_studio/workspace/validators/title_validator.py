"""
Title Validator Module

This module provides the TitleValidator class for validating YouTube video titles
against best practices, SEO requirements, and platform constraints.
"""

from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
import re


@dataclass
class ValidationResult:
    """Result of title validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    score: float  # 0.0 to 1.0
    suggestions: List[str]


class TitleValidator:
    """
    Validator for YouTube video titles.
    
    This class validates titles against YouTube's requirements,
    SEO best practices, and engagement optimization criteria.
    """
    
    # YouTube title constraints
    MAX_LENGTH = 100
    MIN_LENGTH = 10
    MAX_KEYWORDS = 3
    
    # SEO requirements
    MIN_RELEVANCE_SCORE = 0.3
    MAX_KEYWORD_STUFFING = 0.3  # Max ratio of keyword words to total words
    
    # Engagement requirements
    MIN_ENGAGEMENT_SCORE = 0.5
    RECOMMENDED_LENGTH = 50  # Optimal title length
    
    # Characters that might cause issues
    PROBLEMATIC_CHARS = ['|', '»', '«', '→', '←', '↑', '↓']
    
    def __init__(self):
        """Initialize the title validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
    
    def validate_title(
        self,
        title: str,
        target_keywords: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate a YouTube video title.
        
        Args:
            title: Title to validate
            target_keywords: Optional list of target keywords
            
        Returns:
            ValidationResult with validation results
        """
        self.errors = []
        self.warnings = []
        self.suggestions = []
        
        # Run all validation checks
        self._check_length(title)
        self._check_characters(title)
        self._check_capitalization(title)
        self._check_special_characters(title)
        self._check_keyword_usage(title, target_keywords)
        self._check_engagement(title)
        self._check_clarity(title)
        
        # Calculate overall score
        score = self._calculate_score(title, target_keywords)
        
        # Determine validity
        is_valid = len(self.errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=self.errors,
            warnings=self.warnings,
            score=score,
            suggestions=self.suggestions
        )
    
    def _check_length(self, title: str) -> None:
        """Check title length constraints."""
        length = len(title)
        
        if length < self.MIN_LENGTH:
            self.errors.append(
                f"Title is too short ({length} characters). "
                f"Minimum recommended length is {self.MIN_LENGTH} characters."
            )
            self.suggestions.append(
                f"Expand the title to at least {self.MIN_LENGTH} characters"
            )
        
        if length > self.MAX_LENGTH:
            self.errors.append(
                f"Title is too long ({length} characters). "
                f"Maximum allowed length is {self.MAX_LENGTH} characters."
            )
            self.suggestions.append(
                f"Shorten the title to {self.MAX_LENGTH} characters or less"
            )
        
        # Warning for non-optimal length
        if self.MIN_LENGTH <= length <= self.MAX_LENGTH:
            if length < self.RECOMMENDED_LENGTH - 10:
                self.warnings.append(
                    f"Title is shorter than recommended ({length} chars). "
                    f"Consider expanding to ~{self.RECOMMENDED_LENGTH} characters."
                )
            elif length > self.RECOMMENDED_LENGTH + 10:
                self.warnings.append(
                    f"Title is longer than recommended ({length} chars). "
                    f"Consider shortening to ~{self.RECOMMENDED_LENGTH} characters."
                )
    
    def _check_characters(self, title: str) -> None:
        """Check for problematic characters."""
        for char in self.PROBLEMATIC_CHARS:
            if char in title:
                self.warnings.append(
                    f"Title contains '{char}' which may not display correctly on all devices."
                )
                self.suggestions.append(
                    f"Replace '{char}' with a standard character like ':' or '-'"
                )
    
    def _check_capitalization(self, title: str) -> None:
        """Check title capitalization."""
        # Check for ALL CAPS (more than 3 consecutive words)
        words = title.split()
        all_caps_words = [word for word in words if word.isupper() and len(word) > 1]
        
        if len(all_caps_words) > 3:
            self.warnings.append(
                f"Too many words in ALL CAPS ({len(all_caps_words)} words). "
                f"This may appear spammy to viewers."
            )
            self.suggestions.append(
                "Use ALL CAPS sparingly for emphasis only"
            )
        
        # Check for proper capitalization
        if title != title.title() and title != title.upper():
            # Check if first letter of each word is capitalized
            words = title.split()
            proper_words = [word[0].isupper() for word in words if word]
            if proper_words and all(proper_words):
                pass  # Title case is good
            else:
                self.warnings.append(
                    "Title capitalization may be inconsistent. "
                    "Consider using title case for better readability."
                )
    
    def _check_special_characters(self, title: str) -> None:
        """Check for excessive special characters."""
        special_chars = sum(1 for char in title if not char.isalnum() and not char.isspace())
        
        if special_chars > 5:
            self.warnings.append(
                f"Title contains {special_chars} special characters. "
                f"Consider simplifying the title."
            )
            self.suggestions.append(
                "Use fewer special characters for cleaner appearance"
            )
        
        # Check for multiple consecutive punctuation
        if re.search(r'[.,;:!?]{2,}', title):
            self.warnings.append(
                "Title contains consecutive punctuation marks."
            )
            self.suggestions.append(
                "Remove consecutive punctuation marks"
            )
    
    def _check_keyword_usage(
        self,
        title: str,
        target_keywords: Optional[List[str]] = None
    ) -> None:
        """Check keyword usage in title."""
        if not target_keywords:
            return
        
        title_lower = title.lower()
        words = title.split()
        total_words = len(words)
        
        if total_words == 0:
            return
        
        # Check if target keywords are in title
        keywords_in_title = []
        for keyword in target_keywords:
            if keyword.lower() in title_lower:
                keywords_in_title.append(keyword)
        
        if len(keywords_in_title) < 1:
            self.warnings.append(
                "None of the target keywords appear in the title."
            )
            self.suggestions.append(
                "Include at least one target keyword in the title"
            )
        
        # Check for keyword stuffing
        keyword_word_count = 0
        for keyword in target_keywords:
            keyword_words = keyword.lower().split()
            for word in keyword_words:
                if word in title_lower:
                    keyword_word_count += 1
        
        keyword_ratio = keyword_word_count / total_words if total_words > 0 else 0
        
        if keyword_ratio > self.MAX_KEYWORD_STUFFING:
            self.errors.append(
                f"Title appears to have keyword stuffing ({keyword_ratio:.1%} keyword ratio)."
            )
            self.suggestions.append(
                "Reduce keyword density for more natural language"
            )
        
        # Check keyword position (first 3 words are most important)
        first_three_words = set(words[:3].lower())
        keyword_positions = []
        for keyword in target_keywords:
            keyword_words = keyword.lower().split()
            for word in keyword_words:
                if word in first_three_words:
                    keyword_positions.append(keyword)
                    break
        
        if len(keyword_positions) == 0 and len(target_keywords) > 0:
            self.warnings.append(
                "Target keywords don't appear in the first 3 words of the title."
            )
            self.suggestions.append(
                "Place important keywords near the beginning of the title"
            )
    
    def _check_engagement(self, title: str) -> None:
        """Check title engagement factors."""
        title_lower = title.lower()
        
        # Check for engagement-boosting elements
        engagement_elements = {
            'numbers': r'\d+',
            'questions': r'\?',
            'power_words': r'\b(ultimate|essential|complete|proven|easy|quick|simple|powerful|effective)\b',
            'brackets': r'\[.*?\]',
            'parentheses': r'\(.*?\)',
        }
        
        engagement_count = 0
        for element_type, pattern in engagement_elements.items():
            if re.search(pattern, title):
                engagement_count += 1
        
        if engagement_count == 0:
            self.warnings.append(
                "Title lacks common engagement-boosting elements."
            )
            self.suggestions.append(
                "Consider adding numbers, questions, or power words to increase engagement"
            )
        
        # Check for curiosity gap
        if not re.search(r'\?|how|why|what|secret|trick|tip|guide|tutorial', title_lower):
            self.warnings.append(
                "Title doesn't create a strong curiosity gap."
            )
            self.suggestions.append(
                "Consider adding 'how', 'why', 'what', or similar words to create curiosity"
            )
    
    def _check_clarity(self, title: str) -> None:
        """Check title clarity and readability."""
        # Check for vague language
        vague_words = ['thing', 'stuff', 'item', 'object', 'element']
        if any(word in title.lower() for word in vague_words):
            self.warnings.append(
                "Title contains vague language that may not clearly describe the content."
            )
            self.suggestions.append(
                "Use specific, descriptive language instead of vague terms"
            )
        
        # Check for clarity (simple language)
        words = title.split()
        complex_words = [
            word for word in words
            if len(word) > 8 and word.isalpha()
        ]
        
        if len(complex_words) > len(words) * 0.3:
            self.warnings.append(
                "Title contains many complex words that may reduce clarity."
            )
            self.suggestions.append(
                "Use simpler language for better accessibility"
            )
    
    def _calculate_score(
        self,
        title: str,
        target_keywords: Optional[List[str]] = None
    ) -> float:
        """
        Calculate overall validation score.
        
        Args:
            title: Title to score
            target_keywords: Optional target keywords
            
        Returns:
            Score between 0.0 and 1.0
        """
        score = 1.0
        
        # Deduct points for errors
        score -= len(self.errors) * 0.2
        
        # Deduct points for warnings
        score -= len(self.warnings) * 0.05
        
        # Bonus for engagement elements
        engagement_elements = {
            'numbers': r'\d+',
            'questions': r'\?',
            'power_words': r'\b(ultimate|essential|complete|proven|easy|quick|simple|powerful|effective)\b',
            'brackets': r'\[.*?\]',
            'parentheses': r'\(.*?\)',
        }
        
        engagement_count = sum(
            1 for pattern in engagement_elements.values()
            if re.search(pattern, title)
        )
        score += min(engagement_count * 0.05, 0.2)
        
        # Bonus for keyword inclusion
        if target_keywords:
            title_lower = title.lower()
            keywords_in_title = sum(
                1 for keyword in target_keywords
                if keyword.lower() in title_lower
            )
            score += min(keywords_in_title * 0.05, 0.15)
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def get_improvement_suggestions(self, title: str, target_keywords: Optional[List[str]] = None) -> List[str]:
        """
        Get specific improvement suggestions for a title.
        
        Args:
            title: Title to improve
            target_keywords: Optional target keywords
            
        Returns:
            List of improvement suggestions
        """
        result = self.validate_title(title, target_keywords)
        return result.suggestions
    
    def compare_titles(
        self,
        title1: str,
        title2: str,
        target_keywords: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Compare two titles and return which is better.
        
        Args:
            title1: First title to compare
            title2: Second title to compare
            target_keywords: Optional target keywords
            
        Returns:
            Dictionary with comparison results
        """
        result1 = self.validate_title(title1, target_keywords)
        result2 = self.validate_title(title2, target_keywords)
        
        return {
            'title1_score': result1.score,
            'title2_score': result2.score,
            'better_title': title1 if result1.score > result2.score else title2,
            'title1_errors': len(result1.errors),
            'title2_errors': len(result2.errors),
            'title1_warnings': len(result1.warnings),
            'title2_warnings': len(result2.warnings),
            'title1_suggestions': result1.suggestions,
            'title2_suggestions': result2.suggestions,
        }
