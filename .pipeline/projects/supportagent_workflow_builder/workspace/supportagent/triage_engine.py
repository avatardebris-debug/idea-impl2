"""Enhanced triage engine with sentiment analysis, priority scoring, and ML classification."""

from __future__ import annotations

import math
import os
from typing import Any, Dict, List, Optional

import yaml

from supportagent.models import Ticket, Sentiment


class TriageEngine:
    """Enhanced triage engine with sentiment analysis, priority scoring, and ML classification."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the triage engine.

        Args:
            config_path: Path to the triage config YAML file.
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "triage_config.yaml"
            )
        self.config = self._load_config(config_path)
        self.sentiment_lexicon = self._load_sentiment_lexicon()
        self.category_prototypes = self._load_category_prototypes()

    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load triage configuration."""
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def _load_sentiment_lexicon(self) -> Dict[str, List[str]]:
        """Load sentiment lexicon from YAML."""
        lexicon_path = os.path.join(
            os.path.dirname(__file__), "config", "sentiment_lexicon.yaml"
        )
        with open(lexicon_path, "r") as f:
            return yaml.safe_load(f)

    def _load_category_prototypes(self) -> Dict[str, Any]:
        """Load ML category prototypes from YAML."""
        proto_path = os.path.join(
            os.path.dirname(__file__), "config", "ml_category_prototypes.yaml"
        )
        with open(proto_path, "r") as f:
            return yaml.safe_load(f)

    def analyze_sentiment(self, ticket: Ticket) -> Sentiment:
        """Analyze the sentiment of a ticket.

        Args:
            ticket: The ticket to analyze.

        Returns:
            The sentiment classification.
        """
        text = f"{ticket.subject} {ticket.body}".lower()
        words = text.split()

        positive_count = 0
        negative_count = 0
        angry_count = 0

        for word in words:
            # Clean punctuation
            clean_word = word.strip(".,!?;:'\"()[]{}")
            if clean_word in self.sentiment_lexicon.get("positive", []):
                positive_count += 1
            if clean_word in self.sentiment_lexicon.get("negative", []):
                negative_count += 1
            if clean_word in self.sentiment_lexicon.get("angry", []):
                angry_count += 1

        # Check for exclamation marks as anger indicator
        exclamation_count = ticket.body.count("!")
        angry_count += exclamation_count

        # Check for ALL CAPS words as anger indicator
        caps_words = [w for w in words if w.isupper() and len(w) > 1]
        angry_count += len(caps_words)

        # Determine sentiment
        if angry_count > negative_count and angry_count > positive_count:
            return Sentiment.ANGRY
        elif positive_count > negative_count and positive_count > 0:
            return Sentiment.POSITIVE
        elif negative_count > positive_count and negative_count > 0:
            return Sentiment.NEGATIVE
        else:
            return Sentiment.NEUTRAL

    def calculate_priority(self, ticket: Ticket) -> int:
        """Calculate priority score (1-10) for a ticket.

        Args:
            ticket: The ticket to score.

        Returns:
            Priority score as an integer (1-10).
        """
        score = 1  # Base score

        # Urgency contribution
        urgency_scores = {
            "low": 1,
            "medium": 3,
            "high": 5,
            "critical": 8,
        }
        if ticket.urgency:
            score += urgency_scores.get(ticket.urgency.value, 0)

        # Sentiment contribution
        if ticket.sentiment == Sentiment.ANGRY:
            score += 3
        elif ticket.sentiment == Sentiment.NEGATIVE:
            score += 1

        # Category contribution
        category_scores = {
            "urgent": 5,
            "billing": 3,
            "technical": 3,
            "account": 1,
            "general": 0,
        }
        if ticket.category:
            score += category_scores.get(ticket.category, 0)

        # Length contribution (longer tickets may be more complex)
        text_length = len(f"{ticket.subject} {ticket.body}")
        if text_length > 500:
            score += 1
        elif text_length > 1000:
            score += 2

        # Clamp score
        score = max(1, min(10, score))

        return score

    def classify_with_ml(self, ticket: Ticket) -> Optional[str]:
        """Classify ticket using ML prototypes (cosine similarity).

        Args:
            ticket: The ticket to classify.

        Returns:
            The predicted category, or None if no match found.
        """
        text = f"{ticket.subject} {ticket.body}".lower()
        words = set(text.split())

        best_category = None
        best_similarity = -1

        for category, prototype in self.category_prototypes.items():
            prototype_words = set(prototype.get("keywords", []))
            if not prototype_words:
                continue

            # Cosine similarity
            intersection = len(words & prototype_words)
            if intersection == 0:
                continue

            magnitude_words = math.sqrt(len(words))
            magnitude_proto = math.sqrt(len(prototype_words))

            if magnitude_words == 0 or magnitude_proto == 0:
                continue

            similarity = intersection / (magnitude_words * magnitude_proto)

            if similarity > best_similarity:
                best_similarity = similarity
                best_category = category

        # Only return if similarity is above threshold
        if best_similarity >= 0.3:
            return best_category

        return None

    def triage(self, ticket: Ticket) -> Dict[str, Any]:
        """Perform full triage on a ticket.

        Args:
            ticket: The ticket to triage.

        Returns:
            Dict with keys: category, urgency, priority_score, sentiment, ml_category
        """
        # Analyze sentiment
        sentiment = self.analyze_sentiment(ticket)
        ticket.sentiment = sentiment

        # Calculate priority
        priority_score = self.calculate_priority(ticket)
        ticket.priority_score = priority_score

        # Classify with ML
        ml_category = self.classify_with_ml(ticket)

        # Determine final category
        if ml_category:
            category = ml_category
        elif ticket.category:
            category = ticket.category
        else:
            category = "general"

        return {
            "category": category,
            "urgency": ticket.urgency,
            "priority_score": priority_score,
            "sentiment": sentiment,
            "ml_category": ml_category,
        }

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update the triage configuration.

        Args:
            new_config: New configuration dictionary.
        """
        self.config = new_config

    def get_config(self) -> Dict[str, Any]:
        """Return the current configuration."""
        return self.config
