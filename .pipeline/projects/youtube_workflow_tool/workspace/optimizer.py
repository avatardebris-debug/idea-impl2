"""Optimizer module — scoring, keyword density, CTR prediction.

Evaluates metadata quality: title CTR potential, keyword density,
tag relevance, description completeness.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .config import Config
from .metadata_generator import Metadata, _extract_keywords


# ── Score result ────────────────────────────────────────────────────

@dataclass
class ScoreResult:
    """Result of metadata scoring."""

    overall_score: float = 0.0
    title_score: float = 0.0
    description_score: float = 0.0
    tag_score: float = 0.0
    hashtag_score: float = 0.0
    breakdown: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "title_score": self.title_score,
            "description_score": self.description_score,
            "tag_score": self.tag_score,
            "hashtag_score": self.hashtag_score,
            "breakdown": self.breakdown,
            "recommendations": self.recommendations,
        }


# ── CTR prediction patterns ──────────────────────────────────────────

CTR_PATTERNS: List[Tuple[str, float]] = [
    (r"(?i)how\s+to", 0.15),
    (r"(?i)ultimate\s+guide", 0.12),
    (r"(?i)top\s+\d+", 0.10),
    (r"(?i)best\s+\d*\s*\w*", 0.10),
    (r"(?i)secret(s)?", 0.08),
    (r"(?i)review", 0.07),
    (r"(?i)vs\s+|versus", 0.09),
    (r"(?i)beginner", 0.06),
    (r"(?i)advanced", 0.05),
    (r"(?i)pro\s+tips?", 0.08),
    (r"(?i)mistakes?", 0.07),
    (r"(?i)tried", 0.06),
    (r"(?i)changed\s+my\s+life", 0.05),
    (r"(?i)what\s+no\s+one\s+tells?\s+you", 0.09),
    (r"(?i)everything\s+you\s+need\s+to\s+know", 0.08),
    (r"(?i)complete\s+guide", 0.07),
    (r"(?i)step\s*[- ]?\s*by\s*[- ]?\s*step", 0.06),
    (r"(?i)in\s+\d+\s+minutes?", 0.07),
    (r"(?i)is\s+it\s+worth\s+it", 0.06),
    (r"(?i)unboxing", 0.05),
    (r"(?i)introducing", 0.04),
    (r"(?i)update", 0.03),
    (r"(?i)tutorial", 0.06),
    (r"(?i)explained", 0.05),
    (r"(?i)tips?", 0.06),
    (r"(?i)hack(s)?", 0.07),
    (r"(?i)trick(s)?", 0.06),
    (r"(?i)fast\s+|quick\s+|easy", 0.05),
    (r"(?i)free", 0.04),
    (r"(?i)new\s+in\s+\d{4}", 0.04),
]


# ── Keyword density ────────────────────────────────────────────────────

@dataclass
class KeywordDensityReport:
    """Report on keyword density in text."""

    text: str = ""
    total_words: int = 0
    unique_words: int = 0
    keyword_density: Dict[str, float] = field(default_factory=dict)
    top_keywords: List[Tuple[str, float]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "total_words": self.total_words,
            "unique_words": self.unique_words,
            "keyword_density": self.keyword_density,
            "top_keywords": self.top_keywords,
        }


def keyword_density_report(text: str) -> KeywordDensityReport:
    """Analyze keyword density in the given text."""
    words = re.findall(r"[a-zA-Z\u00C0-\u024F]+", text.lower())
    total_words = len(words)
    if total_words == 0:
        return KeywordDensityReport(text=text, total_words=0, unique_words=0)

    word_counts: Dict[str, int] = {}
    for w in words:
        word_counts[w] = word_counts.get(w, 0) + 1

    unique_words = len(word_counts)
    density = {w: round(count / total_words * 100, 2) for w, count in word_counts.items()}
    top_keywords = sorted(density.items(), key=lambda x: x[1], reverse=True)[:20]

    return KeywordDensityReport(
        text=text,
        total_words=total_words,
        unique_words=unique_words,
        keyword_density=density,
        top_keywords=top_keywords,
    )


# ── CTR prediction ────────────────────────────────────────────────────

def ctr_prediction(title: str) -> float:
    """Predict CTR probability (0-1) based on title patterns.

    Scores the title by matching against known high-CTR patterns.
    Returns a probability between 0 and 1.
    """
    if not title or not title.strip():
        return 0.0

    score = 0.0
    for pattern, weight in CTR_PATTERNS:
        if re.search(pattern, title):
            score += weight

    # Length bonus: optimal title length is 50-70 chars
    title_len = len(title)
    if 50 <= title_len <= 70:
        score += 0.05
    elif 40 <= title_len <= 80:
        score += 0.02

    # Capitalization bonus: title case or ALL CAPS keywords
    if re.search(r"[A-Z]{2,}", title):
        score += 0.02

    # Number bonus
    if re.search(r"\d+", title):
        score += 0.03

    # Cap at 1.0
    return min(score, 1.0)


# ── Title scoring ────────────────────────────────────────────────────

def _score_title(title: str, config: Config) -> float:
    """Score a single title (0-100)."""
    if not title or not title.strip():
        return 0.0

    score = 0.0

    # Length score (optimal 50-70 chars)
    length = len(title)
    if 50 <= length <= 70:
        score += 25
    elif 40 <= length <= 80:
        score += 15
    elif 30 <= length <= 90:
        score += 8
    else:
        score += 3

    # CTR pattern score (normalized to 0-30)
    ctr = ctr_prediction(title)
    score += ctr * 30

    # Keyword presence score (0-20)
    keywords = _extract_keywords(title)
    if len(keywords) >= 2:
        score += 20
    elif len(keywords) == 1:
        score += 10
    else:
        score += 5

    # Uniqueness bonus (0-10)
    if len(set(keywords)) >= 3:
        score += 10
    elif len(set(keywords)) >= 2:
        score += 5

    return min(score, 100.0)


# ── Description scoring ────────────────────────────────────────────────────

def _score_description(description: str, config: Config) -> float:
    """Score a description (0-100)."""
    if not description or not description.strip():
        return 0.0

    score = 0.0
    desc_lower = description.lower()

    # Length score
    length = len(description)
    if length >= config.min_description_length:
        score += 20
    if length >= 300:
        score += 15
    if length >= 500:
        score += 10

    # Structure score (0-30)
    sections = ["intro", "what you'll learn", "content", "cta", "links",
                "subscribe", "like", "comment", "resources", "links"]
    found_sections = sum(1 for s in sections if s in desc_lower)
    score += min(found_sections * 5, 30)

    # Call-to-action score (0-20)
    cta_patterns = ["subscribe", "like", "comment", "share", "hit the bell",
                    "don't forget", "follow", "join"]
    found_cta = sum(1 for c in cta_patterns if c in desc_lower)
    score += min(found_cta * 5, 20)

    # Hashtag presence (0-15)
    hashtag_count = desc_lower.count("#")
    if hashtag_count >= 3:
        score += 15
    elif hashtag_count >= 1:
        score += 8

    # Emoji presence (0-15)
    emoji_count = sum(1 for c in description if ord(c) > 127)
    if emoji_count >= 3:
        score += 15
    elif emoji_count >= 1:
        score += 8

    return min(score, 100.0)


# ── Tag scoring ────────────────────────────────────────────────────

def _score_tags(tags: List[str], topic: str) -> float:
    """Score tags (0-100)."""
    if not tags:
        return 0.0

    score = 0.0

    # Count score (0-25)
    count = len(tags)
    if count >= 10:
        score += 25
    elif count >= 5:
        score += 18
    elif count >= 3:
        score += 10
    else:
        score += 3

    # Topic relevance (0-40)
    topic_words = _extract_keywords(topic)
    if topic_words:
        relevant = sum(1 for tag in tags if any(tw in tag.lower() for tw in topic_words))
        score += min(relevant / max(len(tags), 1) * 40, 40)
    else:
        score += 20

    # Diversity score (0-20)
    if len(set(tags)) == len(tags):
        score += 20
    elif len(set(tags)) >= len(tags) * 0.7:
        score += 12
    else:
        score += 5

    # Length diversity (0-15)
    lengths = [len(t) for t in tags]
    if max(lengths) - min(lengths) >= 5:
        score += 15
    elif max(lengths) - min(lengths) >= 2:
        score += 8
    else:
        score += 3

    return min(score, 100.0)


# ── Hashtag scoring ────────────────────────────────────────────────────

def _score_hashtags(hashtags: List[str], topic: str) -> float:
    """Score hashtags (0-100)."""
    if not hashtags:
        return 0.0

    score = 0.0

    # Count score (0-25)
    count = len(hashtags)
    if count >= 8:
        score += 25
    elif count >= 5:
        score += 18
    elif count >= 3:
        score += 10
    else:
        score += 3

    # Format score (0-25) — all should start with #
    formatted = sum(1 for h in hashtags if h.startswith("#"))
    score += (formatted / max(count, 1)) * 25

    # Topic relevance (0-30)
    topic_words = _extract_keywords(topic)
    if topic_words:
        relevant = sum(1 for h in hashtags if any(tw in h.lower() for tw in topic_words))
        score += min(relevant / max(count, 1) * 30, 30)
    else:
        score += 15

    # Uniqueness (0-20)
    cleaned = [h.lstrip("#").lower() for h in hashtags]
    if len(set(cleaned)) == len(cleaned):
        score += 20
    elif len(set(cleaned)) >= len(cleaned) * 0.7:
        score += 12
    else:
        score += 5

    return min(score, 100.0)


# ── Main evaluate function ────────────────────────────────────────────────────

def evaluate_metadata(
    metadata: Metadata,
    config: Optional[Config] = None,
) -> ScoreResult:
    """Score a complete metadata dict/object.

    Returns a ScoreResult with overall_score (0-100) and breakdown.
    """
    if config is None:
        config = Config()

    weights = config.score_weights

    # Title score (average of all titles)
    title_scores = [_score_title(t, config) for t in metadata.titles]
    title_score = sum(title_scores) / max(len(title_scores), 1)

    # Description score
    description_score = _score_description(metadata.description, config)

    # Tag score
    tag_score = _score_tags(metadata.tags, metadata.topic)

    # Hashtag score
    hashtag_score = _score_hashtags(metadata.hashtags, metadata.topic)

    # Weighted overall
    overall = (
        title_score * weights["title"]
        + description_score * weights["description"]
        + tag_score * weights["tags"]
        + hashtag_score * weights["hashtags"]
    )

    # Generate recommendations
    recommendations: List[str] = []
    if title_score < 60:
        recommendations.append("Improve title: use power words, numbers, or 'how to' patterns")
    if description_score < 60:
        recommendations.append("Add more structure to description: intro, content, CTA, links")
    if tag_score < 60:
        recommendations.append("Add more relevant tags (aim for 10-15)")
    if hashtag_score < 60:
        recommendations.append("Add more hashtags (aim for 8-15)")
    if len(metadata.titles) < 5:
        recommendations.append("Generate more title variants (aim for 10+)")
    if len(metadata.tags) < config.min_tags:
        recommendations.append(f"Add more tags (minimum {config.min_tags})")
    if len(metadata.hashtags) < config.min_hashtags:
        recommendations.append(f"Add more hashtags (minimum {config.min_hashtags})")

    # Add CTR predictions for top titles
    for i, t in enumerate(metadata.titles[:3]):
        recommendations.append(f"Title {i+1} CTR prediction: {ctr_prediction(t):.2%}")

    return ScoreResult(
        overall_score=round(overall, 2),
        title_score=round(title_score, 2),
        description_score=round(description_score, 2),
        tag_score=round(tag_score, 2),
        hashtag_score=round(hashtag_score, 2),
        breakdown={
            "title": round(title_score, 2),
            "description": round(description_score, 2),
            "tags": round(tag_score, 2),
            "hashtags": round(hashtag_score, 2),
        },
        recommendations=recommendations,
    )
