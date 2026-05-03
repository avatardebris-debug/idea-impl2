"""Content review system — automated style checks and quality filters."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Profanity list (subset for demonstration)
PROFANITY_LIST = frozenset({
    "fuck", "shit", "damn", "hell", "bitch", "ass", "crap", "dick",
    "piss", "bastard", "whore", "slut", "nigger", "faggot", "cunt",
})

# Minimum content length thresholds by content type
MIN_LENGTHS: Dict[str, int] = {
    "blog": 50,
    "tweet": 10,
    "linkedin": 30,
}

# Default threshold for style match (0-1)
DEFAULT_STYLE_THRESHOLD = 0.8


@dataclass
class ReviewResult:
    """Result of a content review."""
    passed: bool
    style_match_score: float = 0.0
    style_match_passed: bool = False
    profanity_found: bool = False
    profanity_words: List[str] = field(default_factory=list)
    coherence_score: float = 0.0
    coherence_passed: bool = False
    length_sufficient: bool = False
    length_actual: int = 0
    length_required: int = 0
    hallucination_risk: float = 0.0
    hallucination_risk_passed: bool = False
    flagged_for_human_review: bool = False
    comments: List[str] = field(default_factory=list)

    @property
    def failure_reasons(self) -> List[str]:
        """Return list of failure reasons if not passed."""
        reasons = []
        if not self.style_match_passed:
            reasons.append(f"Style match score {self.style_match_score:.2f} below threshold {DEFAULT_STYLE_THRESHOLD}")
        if self.profanity_found:
            reasons.append(f"Profanity detected: {', '.join(self.profanity_words)}")
        if not self.coherence_passed:
            reasons.append(f"Coherence score {self.coherence_score:.2f} below threshold")
        if not self.length_sufficient:
            reasons.append(f"Length {self.length_actual} below minimum {self.length_required}")
        if not self.hallucination_risk_passed:
            reasons.append(f"Hallucination risk {self.hallucination_risk:.2f} above threshold")
        return reasons


def _compute_style_match(content: str) -> float:
    """Compute style match score (0-1) based on Scott Adams' style markers.

    Reuses the heuristic from sacbot.eval._compute_style_match.
    """
    score = 0.0
    markers = [
        (r'\b(you|your)\b', 0.2),
        (r'\b(probability|chances|likely)\b', 0.2),
        (r'\b(habits|systems|processes)\b', 0.15),
        (r'\b(success|management|psychology)\b', 0.15),
        (r'\b(I|me|my)\b', 0.1),
        (r'\b(remember|stop|start)\b', 0.1),
        (r'\?', 0.1),
    ]

    for pattern, weight in markers:
        if re.search(pattern, content, re.IGNORECASE):
            score += weight

    return min(score, 1.0)


def check_style_match(content: str, threshold: float = DEFAULT_STYLE_THRESHOLD) -> tuple[float, bool]:
    """Check if content matches Scott Adams' writing style.

    Args:
        content: The content to check
        threshold: Minimum score to pass (0-1)

    Returns:
        Tuple of (score, passed)
    """
    score = _compute_style_match(content)
    return score, score >= threshold


def _check_profanity(content: str) -> tuple[bool, List[str]]:
    """Check content for profanity.

    Args:
        content: The content to check

    Returns:
        Tuple of (has_profanity, list of profanity words found)
    """
    words = re.findall(r'\b\w+\b', content.lower())
    found = [w for w in words if w in PROFANITY_LIST]
    return len(found) > 0, list(set(found))


def check_quality(
    content: str,
    content_type: str = "blog",
) -> tuple[float, bool, int, int]:
    """Check content quality (coherence, length).

    Args:
        content: The content to check
        content_type: Type of content for length threshold

    Returns:
        Tuple of (coherence_score, passed, actual_length, required_length)
    """
    # Coherence: check sentence structure
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    sentence_count = len(sentences)

    # Coherence score based on sentence count and average sentence length
    if sentence_count == 0:
        coherence_score = 0.0
        coherence_passed = False
    else:
        avg_length = len(content.split()) / sentence_count
        # Good coherence: 3-20 sentences, avg length 5-30 words
        sentence_score = min(1.0, sentence_count / 10.0) if sentence_count <= 20 else 0.5
        length_score = min(1.0, avg_length / 15.0) if avg_length <= 30 else 0.5
        coherence_score = (sentence_score * 0.5 + length_score * 0.5)
        coherence_passed = coherence_score >= 0.3

    # Length check
    word_count = len(content.split())
    required = MIN_LENGTHS.get(content_type, MIN_LENGTHS["blog"])
    length_sufficient = word_count >= required

    return coherence_score, coherence_passed, word_count, required


def _check_hallucination_risk(content: str) -> tuple[float, bool]:
    """Estimate hallucination risk in content.

    Checks for common hallucination indicators:
    - Specific statistics without context
    - Named entities used in unlikely contexts
    - Overconfident claims

    Args:
        content: The content to check

    Returns:
        Tuple of (risk_score, passed)
    """
    risk = 0.0

    # Check for specific statistics (potential hallucination)
    stat_patterns = [
        r'\b\d+%\b',       # percentages
        r'\b\d+\.\d+b\b',  # billion figures
        r'\b\d+\.\d+m\b',  # million figures
        r'\b\d+\.\d+t\b',  # trillion figures
    ]
    for pattern in stat_patterns:
        if re.search(pattern, content):
            risk += 0.15

    # Check for overconfident claims
    overconfident_patterns = [
        r'\bwill definitely\b',
        r'\bwill always\b',
        r'\bnever fails\b',
        r'\bguaranteed\b',
        r'\bproven to\b',
    ]
    for pattern in overconfident_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            risk += 0.1

    # Check for specific named entities (potential hallucination)
    named_entity_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
    entities = re.findall(named_entity_pattern, content)
    if len(entities) > 3:
        risk += 0.1

    # Cap at 1.0
    risk = min(risk, 1.0)
    return risk, risk <= 0.4


def review(
    content: str,
    content_type: str = "blog",
    style_threshold: float = DEFAULT_STYLE_THRESHOLD,
) -> ReviewResult:
    """Run full review on content.

    Args:
        content: The content to review
        content_type: Type of content for thresholds
        style_threshold: Minimum style match score to pass

    Returns:
        ReviewResult with all check results
    """
    # Style match
    style_score, style_passed = check_style_match(content, style_threshold)

    # Profanity
    has_profanity, profanity_words = _check_profanity(content)

    # Quality (coherence + length)
    coherence_score, coherence_passed, length_actual, length_required = check_quality(content, content_type)

    # Hallucination risk
    hallucination_risk, hallucination_passed = _check_hallucination_risk(content)

    # Overall pass/fail
    passed = style_passed and not has_profanity and coherence_passed and length_actual >= length_required and hallucination_passed

    # Flag for human review if close to threshold
    flagged = False
    comments: List[str] = []

    if 0.7 <= style_score < style_threshold:
        flagged = True
        comments.append(f"Style match score ({style_score:.2f}) close to threshold — consider human review")

    if 0.3 <= hallucination_risk <= 0.4:
        flagged = True
        comments.append(f"Hallucination risk ({hallucination_risk:.2f}) elevated — verify facts")

    if not coherence_passed:
        comments.append(f"Coherence score ({coherence_score:.2f}) below threshold — may need rewriting")

    if has_profanity:
        comments.append(f"Profanity detected: {', '.join(profanity_words)}")

    return ReviewResult(
        passed=passed,
        style_match_score=style_score,
        style_match_passed=style_passed,
        profanity_found=has_profanity,
        profanity_words=profanity_words,
        coherence_score=coherence_score,
        coherence_passed=coherence_passed,
        length_sufficient=length_actual >= length_required,
        length_actual=length_actual,
        length_required=length_required,
        hallucination_risk=hallucination_risk,
        hallucination_risk_passed=hallucination_passed,
        flagged_for_human_review=flagged,
        comments=comments,
    )


class ContentReviewer:
    """Orchestrates content review for the pipeline."""

    def __init__(
        self,
        style_threshold: float = DEFAULT_STYLE_THRESHOLD,
    ):
        self.style_threshold = style_threshold

    def review(self, content: str, content_type: str = "blog") -> ReviewResult:
        """Review content using the review system."""
        return review(content, content_type, self.style_threshold)

    def review_batch(
        self,
        contents: List[str],
        content_type: str = "blog",
    ) -> List[ReviewResult]:
        """Review a batch of content."""
        return [self.review(c, content_type) for c in contents]

    def filter_passed(self, results: List[ReviewResult]) -> List[ReviewResult]:
        """Filter to only passed results."""
        return [r for r in results if r.passed]

    def get_flagged(self, results: List[ReviewResult]) -> List[ReviewResult]:
        """Get results flagged for human review."""
        return [r for r in results if r.flagged_for_human_review]
