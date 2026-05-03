"""Topic research module — aggregates topics from current events and Adams' canonical subjects."""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Canonical topics loaded from sacbot/topics.json
_TOPICS_PATH = Path(__file__).parent / "topics.json"


@dataclass
class TopicSuggestion:
    """A single topic suggestion with metadata."""
    topic: str
    relevance_score: float  # 0-1
    source: str  # "canonical" or "trending"
    category: str  # "core" or "extended"
    content_type: str  # "blog", "tweet", or "linkedin"
    description: str = ""

    def __lt__(self, other: "TopicSuggestion") -> bool:
        return self.relevance_score > other.relevance_score  # descending


def _load_canonical_topics() -> List[Dict[str, Any]]:
    """Load canonical topics from topics.json."""
    if _TOPICS_PATH.exists():
        return json.loads(_TOPICS_PATH.read_text(encoding="utf-8")).get("canonical_topics", [])
    return []


def _load_content_type_weights() -> Dict[str, float]:
    """Load content type weights from topics.json."""
    if _TOPICS_PATH.exists():
        return json.loads(_TOPICS_PATH.read_text(encoding="utf-8")).get("content_type_weights", {})
    return {"blog": 0.4, "tweet": 0.35, "linkedin": 0.25}


def _weighted_choice(weights: Dict[str, float]) -> str:
    """Pick a key from weights dict using weighted random selection."""
    items = list(weights.items())
    total = sum(w for _, w in items)
    r = random.uniform(0, total)
    cumulative = 0.0
    for key, weight in items:
        cumulative += weight
        if r <= cumulative:
            return key
    return items[-1][0]


def fetch_trending_topics(
    n: int = 5,
    mock_data: Optional[List[str]] = None,
) -> List[str]:
    """Fetch trending topics (mockable for testing).

    In production, this would call news RSS feeds or Google Trends API.
    For testing, pass mock_data to simulate responses.

    Args:
        n: Number of trending topics to return
        mock_data: Optional list of mock topic strings for testing

    Returns:
        List of trending topic strings
    """
    if mock_data:
        return mock_data[:n]

    # Default mock data for when no mock_data is provided
    default_trending = [
        "remote work productivity",
        "AI in management",
        "habit stacking techniques",
        "probability in investing",
        "systems thinking in business",
        "decision making under uncertainty",
        "work-life balance strategies",
        "behavioral economics insights",
        "leadership development programs",
        "financial independence planning",
    ]
    return default_trending[:n]


def suggest_topics(
    n: int = 10,
    source_filter: Optional[str] = None,
    mock_trending: Optional[List[str]] = None,
) -> List[TopicSuggestion]:
    """Generate ranked topic suggestions combining canonical and trending topics.

    Args:
        n: Number of suggestions to return
        source_filter: If "canonical" or "trending", filter to that source
        mock_trending: Optional mock trending topics for testing

    Returns:
        List of TopicSuggestion objects sorted by relevance_score descending
    """
    canonical = _load_canonical_topics()
    weights = _load_content_type_weights()
    trending = fetch_trending_topics(n=n, mock_data=mock_trending)

    suggestions: List[TopicSuggestion] = []

    # Add canonical topics with weighted scores
    for item in canonical:
        topic = item["topic"]
        weight = item.get("weight", 0.5)
        # Add some randomness to make it dynamic
        relevance = weight * random.uniform(0.8, 1.0)
        suggestions.append(TopicSuggestion(
            topic=topic,
            relevance_score=relevance,
            source="canonical",
            category=item.get("category", "core"),
            content_type=_weighted_choice(weights),
            description=item.get("description", ""),
        ))

    # Add trending topics
    for i, topic in enumerate(trending):
        # Higher relevance for earlier trending items
        relevance = max(0.3, 1.0 - (i * 0.15))
        suggestions.append(TopicSuggestion(
            topic=topic,
            relevance_score=relevance,
            source="trending",
            category="trending",
            content_type=_weighted_choice(weights),
            description=f"Trending topic #{i + 1}",
        ))

    # Filter by source if specified
    if source_filter:
        suggestions = [s for s in suggestions if s.source == source_filter]

    # Sort by relevance descending and return top n
    suggestions.sort(key=lambda x: x.relevance_score, reverse=True)
    return suggestions[:n]


class TopicPipeline:
    """Orchestrates topic research for the content pipeline."""

    def __init__(
        self,
        n_topics: int = 10,
        source_filter: Optional[str] = None,
        mock_trending: Optional[List[str]] = None,
    ):
        self.n_topics = n_topics
        self.source_filter = source_filter
        self.mock_trending = mock_trending

    def run(self) -> List[TopicSuggestion]:
        """Run the topic pipeline and return suggestions."""
        return suggest_topics(
            n=self.n_topics,
            source_filter=self.source_filter,
            mock_trending=self.mock_trending,
        )

    def get_trending(self, n: int = 5) -> List[str]:
        """Get just the trending topics."""
        return fetch_trending_topics(n=n, mock_data=self.mock_trending)

    def get_canonical(self) -> List[TopicSuggestion]:
        """Get just the canonical topics."""
        return suggest_topics(n=20, source_filter="canonical", mock_trending=[])


# Module-level convenience function
def get_topics(n: int = 10) -> List[TopicSuggestion]:
    """Convenience function to get topic suggestions."""
    return suggest_topics(n=n)
