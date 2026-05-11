"""
Keyword Validator Module

This module provides the KeywordValidator class for validating YouTube video
keywords against SEO best practices, relevance criteria, and platform requirements.
"""

from typing import List, Optional, Tuple, Dict, Set
from dataclasses import dataclass
import re


@dataclass
class KeywordValidationResult:
    """Result of keyword validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    score: float  # 0.0 to 1.0
    suggestions: List[str]
    optimized_keywords: List[str]


class KeywordValidator:
    """
    Validator for YouTube video keywords.
    
    This class validates keyword sets against YouTube's requirements,
    SEO best practices, and relevance criteria.
    """
    
    # YouTube keyword constraints
    MAX_KEYWORDS = 500  # Total characters across all keywords
    MAX_KEYWORD_LENGTH = 500  # Per keyword
    MAX_KEYWORDS_PER_SET = 15  # Recommended max keywords
    
    # SEO requirements
    MIN_RELEVANCE_SCORE = 0.3
    MAX_KEYWORD_REPETITION = 0.3  # Max ratio of repeated words
    
    # Keyword quality requirements
    MIN_KEYWORD_LENGTH = 2
    MAX_KEYWORD_LENGTH_CHARS = 100
    
    # Stop words to filter out
    STOP_WORDS = {
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
    
    def __init__(self):
        """Initialize the keyword validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.suggestions: List[str] = []
    
    def validate_keywords(
        self,
        keywords: List[str],
        video_title: Optional[str] = None,
        video_description: Optional[str] = None
    ) -> KeywordValidationResult:
        """
        Validate a set of keywords.
        
        Args:
            keywords: List of keywords to validate
            video_title: Optional video title for relevance checking
            video_description: Optional video description for relevance checking
            
        Returns:
            KeywordValidationResult with validation results
        """
        self.errors = []
        self.warnings = []
        self.suggestions = []
        
        # Run all validation checks
        self._check_keyword_count(keywords)
        self._check_keyword_length(keywords)
        self._check_keyword_format(keywords)
        self._check_relevance(keywords, video_title, video_description)
        self._check_repetition(keywords)
        self._check_quality(keywords)
        self._check_duplicates(keywords)
        
        # Optimize keywords
        optimized = self._optimize_keywords(keywords)
        
        # Calculate score
        score = self._calculate_score(keywords)
        
        # Determine validity
        is_valid = len(self.errors) == 0
        
        return KeywordValidationResult(
            is_valid=is_valid,
            errors=self.errors,
            warnings=self.warnings,
            score=score,
            suggestions=self.suggestions,
            optimized_keywords=optimized
        )
    
    def _check_keyword_count(self, keywords: List[str]) -> None:
        """Check keyword count constraints."""
        if not keywords:
            self.warnings.append("No keywords provided. Keywords help with video discoverability.")
            self.suggestions.append("Add relevant keywords to improve search visibility")
            return
        
        # Check total character count
        total_chars = sum(len(kw) for kw in keywords)
        if total_chars > self.MAX_KEYWORDS:
            self.errors.append(
                f"Total keyword characters ({total_chars}) exceed maximum ({self.MAX_KEYWORDS})."
            )
            self.suggestions.append(
                "Remove less relevant keywords or shorten existing ones"
            ]
        
        # Warning for too many keywords
        if len(keywords) > self.MAX_KEYWORDS_PER_SET:
            self.warnings.append(
                f"Too many keywords ({len(keywords)}). YouTube recommends 5-15 keywords."
            )
            self.suggestions.append(
                f"Reduce to {self.MAX_KEYWORDS_PER_SET} keywords or fewer"
            ]
        
        # Warning for too few keywords
        if len(keywords) < 3:
            self.warnings.append(
                f"Too few keywords ({len(keywords)}). Consider adding more relevant keywords."
            )
            self.suggestions.append(
                "Add at least 3-5 relevant keywords"
            ]
    
    def _check_keyword_length(self, keywords: List[str]) -> None:
        """Check individual keyword length constraints."""
        for i, keyword in enumerate(keywords):
            if len(keyword) > self.MAX_KEYWORD_LENGTH_CHARS:
                self.errors.append(
                    f"Keyword {i+1} is too long ({len(keyword)} characters). "
                    f"Maximum is {self.MAX_KEYWORD_LENGTH_CHARS} characters."
                )
                self.suggestions.append(
                    f"Shorten keyword '{keyword[:20]}...' to under {self.MAX_KEYWORD_LENGTH_CHARS} characters"
                ]
            
            if len(keyword) < self.MIN_KEYWORD_LENGTH:
                self.warnings.append(
                    f"Keyword {i+1} is too short ({len(keyword)} characters)."
                )
                self.suggestions.append(
                    f"Expand keyword '{keyword}' to at least {self.MIN_KEYWORD_LENGTH} characters"
                ]
    
    def _check_keyword_format(self, keywords: List[str]) -> None:
        """Check keyword format requirements."""
        for i, keyword in enumerate(keywords):
            # Check for special characters
            if not re.match(r'^[a-zA-Z0-9\s\-_]+$', keyword):
                self.warnings.append(
                    f"Keyword {i+1} contains special characters: '{keyword}'"
                )
                self.suggestions.append(
                    "Use only letters, numbers, spaces, hyphens, and underscores"
                ]
            
            # Check for excessive capitalization
            words = keyword.split()
            all_caps_words = [w for w in words if w.isupper() and len(w) > 1]
            if len(all_caps_words) > len(words) * 0.5:
                self.warnings.append(
                    f"Keyword {i+1} has excessive capitalization: '{keyword}'"
                )
                self.suggestions.append(
                    "Use normal capitalization for better readability"
                ]
            
            # Check for leading/trailing spaces
            if keyword != keyword.strip():
                self.warnings.append(
                    f"Keyword {i+1} has leading or trailing spaces: '{keyword}'"
                )
                self.suggestions.append(
                    "Remove leading and trailing spaces"
                ]
    
    def _check_relevance(
        self,
        keywords: List[str],
        video_title: Optional[str] = None,
        video_description: Optional[str] = None
    ) -> None:
        """Check keyword relevance to video content."""
        if not video_title and not video_description:
            self.warnings.append(
                "No video title or description provided for relevance checking."
            )
            self.suggestions.append(
                "Provide video title and description for better relevance analysis"
            ]
            return
        
        # Combine title and description for relevance checking
        content = ""
        if video_title:
            content += video_title.lower() + " "
        if video_description:
            content += video_description.lower()
        
        content_words = set(content.split())
        
        # Check each keyword's relevance
        irrelevant_keywords = []
        for i, keyword in enumerate(keywords):
            keyword_words = set(keyword.lower().split())
            
            # Calculate relevance score
            if content_words:
                relevance = len(keyword_words.intersection(content_words)) / len(keyword_words)
            else:
                relevance = 0
            
            if relevance < self.MIN_RELEVANCE_SCORE:
                irrelevant_keywords.append((i+1, keyword, relevance))
        
        if irrelevant_keywords:
            self.warnings.append(
                f"{len(irrelevant_keywords)} keywords appear irrelevant to the video content."
            )
            self.suggestions.append(
                "Remove or replace irrelevant keywords with more relevant ones"
            ]
            for idx, kw, rel in irrelevant_keywords:
                self.suggestions.append(
                    f"Keyword {idx} '{kw}' has low relevance ({rel:.1%})"
                ]
    
    def _check_repetition(self, keywords: List[str]) -> None:
        """Check for keyword repetition."""
        all_words = []
        for keyword in keywords:
            all_words.extend(keyword.lower().split())
        
        if not all_words:
            return
        
        # Count word frequencies
        word_counts = {}
        for word in all_words:
            if word not in self.STOP_WORDS:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Check for excessive repetition
        total_words = len(all_words)
        max_repetition = 0
        repeated_words = []
        
        for word, count in word_counts.items():
            if count > 1:
                repetition_ratio = count / total_words
                if repetition_ratio > self.MAX_KEYWORD_REPETITION:
                    max_repetition = max(max_repetition, repetition_ratio)
                    repeated_words.append((word, count))
        
        if repeated_words:
            self.warnings.append(
                f"Excessive keyword repetition detected. "
                f"Words repeated: {', '.join([f'{w}({c})' for w, c in repeated_words])}"
            )
            self.suggestions.append(
                "Reduce repetition by using synonyms or related terms"
            ]
    
    def _check_quality(self, keywords: List[str]) -> None:
        """Check keyword quality metrics."""
        # Check for generic keywords
        generic_keywords = ['video', 'youtube', 'channel', 'subscribe', 'like', 'comment']
        generic_count = 0
        
        for keyword in keywords:
            if any(generic in keyword.lower() for generic in generic_keywords):
                generic_count += 1
        
        if generic_count > len(keywords) * 0.3:
            self.warnings.append(
                f"Too many generic keywords ({generic_count}). "
                f"Generic keywords are less effective for targeting."
            )
            self.suggestions.append(
                "Use more specific, long-tail keywords for better targeting"
            ]
        
        # Check for keyword stuffing patterns
        for keyword in keywords:
            if len(keyword.split()) > 5:
                self.warnings.append(
                    f"Keyword '{keyword}' is very long. Consider breaking it into shorter phrases."
                )
                self.suggestions.append(
                    "Use shorter, more specific keyword phrases"
                ]
    
    def _check_duplicates(self, keywords: List[str]) -> None:
        """Check for duplicate keywords."""
        seen = set()
        duplicates = []
        
        for i, keyword in enumerate(keywords):
            normalized = keyword.lower().strip()
            if normalized in seen:
                duplicates.append((i+1, keyword))
            seen.add(normalized)
        
        if duplicates:
            self.errors.append(
                f"Found {len(duplicates)} duplicate keywords."
            )
            self.suggestions.append(
                "Remove duplicate keywords to avoid redundancy"
            ]
            for idx, kw in duplicates:
                self.suggestions.append(
                    f"Remove duplicate keyword {idx}: '{kw}'"
                ]
    
    def _optimize_keywords(self, keywords: List[str]) -> List[str]:
        """
        Optimize keywords for better performance.
        
        Args:
            keywords: List of keywords to optimize
            
        Returns:
            Optimized list of keywords
        """
        optimized = []
        
        for keyword in keywords:
            # Clean up keyword
            cleaned = keyword.strip().lower()
            
            # Remove stop words
            words = [w for w in cleaned.split() if w not in self.STOP_WORDS]
            cleaned = ' '.join(words)
            
            # Remove duplicates within the keyword
            words = list(dict.fromkeys(words))
            cleaned = ' '.join(words)
            
            # Skip empty keywords
            if not cleaned:
                continue
            
            # Add to optimized list if not already present
            if cleaned not in [k.lower() for k in optimized]:
                optimized.append(cleaned)
        
        # Sort by length (prefer longer, more specific keywords)
        optimized.sort(key=lambda x: len(x), reverse=True)
        
        return optimized
    
    def _calculate_score(self, keywords: List[str]) -> float:
        """
        Calculate overall validation score.
        
        Args:
            keywords: List of keywords to score
            
        Returns:
            Score between 0.0 and 1.0
        """
        score = 1.0
        
        # Deduct points for errors
        score -= len(self.errors) * 0.2
        
        # Deduct points for warnings
        score -= len(self.warnings) * 0.05
        
        # Bonus for optimal keyword count
        if 5 <= len(keywords) <= 15:
            score += 0.1
        
        # Bonus for relevance (if title/description provided)
        # This is handled in _check_relevance, but we can add a bonus here
        # if no irrelevant keywords were found
        
        # Bonus for quality
        if len(keywords) > 0:
            # Check for mix of short and long tail keywords
            short_tail = [kw for kw in keywords if len(kw.split()) <= 2]
            long_tail = [kw for kw in keywords if len(kw.split()) > 2]
            
            if short_tail and long_tail:
                score += 0.1
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def get_improvement_suggestions(self, keywords: List[str]) -> List[str]:
        """
        Get specific improvement suggestions for keywords.
        
        Args:
            keywords: List of keywords to improve
            
        Returns:
            List of improvement suggestions
        """
        result = self.validate_keywords(keywords)
        return result.suggestions
    
    def compare_keywords(
        self,
        keywords1: List[str],
        keywords2: List[str],
        video_title: Optional[str] = None,
        video_description: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Compare two keyword sets and return which is better.
        
        Args:
            keywords1: First keyword set to compare
            keywords2: Second keyword set to compare
            video_title: Optional video title for relevance checking
            video_description: Optional video description for relevance checking
            
        Returns:
            Dictionary with comparison results
        """
        result1 = self.validate_keywords(keywords1, video_title, video_description)
        result2 = self.validate_keywords(keywords2, video_title, video_description)
        
        return {
            'keywords1_score': result1.score,
            'keywords2_score': result2.score,
            'better_keywords': 'keywords1' if result1.score > result2.score else 'keywords2',
            'keywords1_errors': len(result1.errors),
            'keywords2_errors': len(result2.errors),
            'keywords1_warnings': len(result1.warnings),
            'keywords2_warnings': len(result2.warnings),
            'keywords1_suggestions': result1.suggestions,
            'keywords2_suggestions': result2.suggestions,
            'keywords1_optimized': result1.optimized_keywords,
            'keywords2_optimized': result2.optimized_keywords,
        }
