"""Gap extraction engine that identifies content gaps from reviews."""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from typing import Any, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from book_researcher.models import Gap

logger = logging.getLogger(__name__)

# Gap-indicating phrases and their associated topic hints
GAP_PHRASES = [
    r"\bwish\s+it\s+also\s+\w+",
    r"\bwish\s+for\s+",
    r"\bwant\s+to\s+see\s+",
    r"\bneeded\s+more\s+on\s+",
    r"\bdidn't\s+cover\s+",
    r"\bmissing\s+(?:a\s+)?chapter\s+on\s+",
    r"\blacked\s+(?:a\s+)?section\s+on\s+",
    r"\bcould\s+use\s+more\s+on\s+",
    r"\bshould\s+have\s+included\s+",
    r"\bregret\s+that\s+it\s+didn't\s+",
    r"\bunfortunately\s+didn't\s+cover\s+",
    r"\bwould\s+have\s+been\s+nice\s+if\s+it\s+covered\s+",
]


def _extract_topics(text: str) -> List[str]:
    """Extract potential topics from review text using simple keyword overlap."""
    topics = [
        "beginner", "advanced", "intermediate", "practical", "theoretical",
        "case study", "tutorial", "reference", "fundamentals", "architecture",
        "deployment", "optimization", "security", "testing", "debugging",
        "performance", "scalability", "maintenance", "best practices",
        "real-world", "examples", "exercises", "projects", "assessment",
        "certification", "interview", "career", "management", "leadership",
        "communication", "collaboration", "agile", "scrum", "devops",
        "cloud", "database", "api", "frontend", "backend", "full-stack",
        "mobile", "web", "desktop", "embedded", "iot", "ml", "dl", "nlp",
        "cv", "data science", "analytics", "visualization", "statistics",
        "math", "algorithms", "data structures", "design patterns",
    ]
    found = []
    text_lower = text.lower()
    for topic in topics:
        if topic in text_lower:
            found.append(topic)
    return found


def _extract_gap_text(review_text: str) -> str:
    """Extract the gap-indicating text from a review."""
    for phrase in GAP_PHRASES:
        match = re.search(phrase, review_text, re.IGNORECASE)
        if match:
            # Return the full sentence containing the gap phrase
            sentences = re.split(r'(?<=[.!?])\s+', review_text)
            for sentence in sentences:
                if re.search(phrase, sentence, re.IGNORECASE):
                    return sentence.strip()
    return ""


def extract_gaps(reviews: list[Any], min_gap_length: int = 10) -> list[Gap]:
    """Extract content gaps from a list of reviews.

    Args:
        reviews: List of dicts with 'text' key, or BookReview objects.
        min_gap_length: Minimum length of gap text to include.

    Returns:
        List of Gap objects.
    """
    if not reviews:
        logger.warning("No reviews provided to extract_gaps")
        return []

    gaps: list[Gap] = []
    seen_texts: set[str] = set()

    for review in reviews:
        if isinstance(review, dict):
            text = review.get("text", "")
            source = review.get("source", "unknown")
        else:
            text = getattr(review, "text", "")
            source = getattr(review, "source", "unknown")

        if not text:
            continue

        gap_text = _extract_gap_text(text)
        if not gap_text or len(gap_text) < min_gap_length:
            continue

        # Deduplicate similar gaps
        if gap_text in seen_texts:
            continue
        seen_texts.add(gap_text)

        topics = _extract_topics(text)
        topic = topics[0] if topics else "general"

        gap = Gap(
            text=gap_text,
            source_review=text[:200] + ("..." if len(text) > 200 else ""),
            topic=topic,
        )
        gaps.append(gap)

    logger.info("Extracted %d unique gaps from %d reviews", len(gaps), len(reviews))
    return gaps
