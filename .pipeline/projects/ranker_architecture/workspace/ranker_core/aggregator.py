"""Aggregator — computes per-item and per-user preference scores from signals."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .signals import Signal
from .profile import TasteProfile


class Aggregator:
    """Aggregates preference signals into scores and taste profiles.

    Supports multiple aggregation strategies:
    - Weighted average for explicit ratings
    - Count-based for implicit signals
    - Combined scores for mixed signal types
    """

    def __init__(self, default_weight: float = 1.0) -> None:
        self.default_weight = default_weight

    def aggregate_item_scores(
        self,
        signals: List[Signal],
        strategy: str = "weighted_average",
    ) -> Dict[str, float]:
        """Aggregate signals into per-item scores.

        Args:
            signals: List of Signal objects to aggregate.
            strategy: Aggregation strategy. One of:
                - "weighted_average": Weighted average of values
                - "count": Count of signals per item
                - "max": Maximum value per item
                - "sum": Sum of values per item

        Returns:
            Dictionary mapping item_id to aggregated score.
        """
        item_scores: Dict[str, float] = {}

        if strategy == "weighted_average":
            item_weighted_sums: Dict[str, float] = {}
            item_weights: Dict[str, float] = {}
            for s in signals:
                item_id = s.item_id
                weight = s.weight if s.weight is not None else self.default_weight
                item_weighted_sums[item_id] = item_weighted_sums.get(item_id, 0.0) + s.value * weight
                item_weights[item_id] = item_weights.get(item_id, 0.0) + weight
            for item_id in item_weighted_sums:
                if item_weights[item_id] > 0:
                    item_scores[item_id] = item_weighted_sums[item_id] / item_weights[item_id]
                else:
                    item_scores[item_id] = 0.0

        elif strategy == "count":
            for s in signals:
                item_id = s.item_id
                item_scores[item_id] = item_scores.get(item_id, 0) + 1

        elif strategy == "max":
            for s in signals:
                item_id = s.item_id
                item_scores[item_id] = max(item_scores.get(item_id, float("-inf")), s.value)

        elif strategy == "sum":
            for s in signals:
                item_id = s.item_id
                item_scores[item_id] = item_scores.get(item_id, 0.0) + s.value

        else:
            raise ValueError(f"Unknown aggregation strategy: {strategy}")

        return item_scores

    def aggregate_user_taste(
        self,
        signals: List[Signal],
        user_id: str,
        strategy: str = "weighted_average",
    ) -> TasteProfile:
        """Aggregate signals into a taste profile for a user.

        Args:
            signals: List of Signal objects.
            user_id: User identifier.
            strategy: Aggregation strategy (same as aggregate_item_scores).

        Returns:
            TasteProfile with aggregated taste vector.
        """
        user_signals = [s for s in signals if s.user_id == user_id]
        item_scores = self.aggregate_item_scores(user_signals, strategy)
        return TasteProfile(user_id=user_id, taste_vector=item_scores)

    def compute_preference_score(
        self,
        signals: List[Signal],
        item_id: str,
        strategy: str = "weighted_average",
    ) -> float:
        """Compute a single preference score for a specific item.

        Args:
            signals: List of Signal objects.
            item_id: Item to compute score for.
            strategy: Aggregation strategy.

        Returns:
            Aggregated preference score for the item.
        """
        item_scores = self.aggregate_item_scores(signals, strategy)
        return item_scores.get(item_id, 0.0)

    def get_top_items(
        self,
        signals: List[Signal],
        n: int = 10,
        strategy: str = "weighted_average",
    ) -> List[Tuple[str, float]]:
        """Get top N items by aggregated score.

        Args:
            signals: List of Signal objects.
            n: Number of top items to return.
            strategy: Aggregation strategy.

        Returns:
            List of (item_id, score) tuples sorted by score descending.
        """
        item_scores = self.aggregate_item_scores(signals, strategy)
        sorted_items = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_items[:n]

    def compute_similarity(
        self,
        profile1: TasteProfile,
        profile2: TasteProfile,
        method: str = "cosine",
    ) -> float:
        """Compute similarity between two taste profiles.

        Args:
            profile1: First taste profile.
            profile2: Second taste profile.
            method: Similarity method. One of:
                - "cosine": Cosine similarity
                - "jaccard": Jaccard similarity of non-zero items

        Returns:
            Similarity score between 0 and 1.
        """
        tv1 = profile1.taste_vector
        tv2 = profile2.taste_vector

        if method == "cosine":
            # Get common items
            common_items = set(tv1.keys()) & set(tv2.keys())
            if not common_items:
                return 0.0

            dot_product = sum(tv1[item] * tv2[item] for item in common_items)
            norm1 = sum(v ** 2 for v in tv1.values()) ** 0.5
            norm2 = sum(v ** 2 for v in tv2.values()) ** 0.5

            if norm1 == 0 or norm2 == 0:
                return 0.0

            return dot_product / (norm1 * norm2)

        elif method == "jaccard":
            items1 = set(tv1.keys())
            items2 = set(tv2.keys())
            intersection = len(items1 & items2)
            union = len(items1 | items2)
            return intersection / union if union > 0 else 0.0

        else:
            raise ValueError(f"Unknown similarity method: {method}")

    def normalize_scores(self, scores: Dict[str, float]) -> Dict[str, float]:
        """Normalize scores to [0, 1] range.

        Args:
            scores: Dictionary mapping item_id to score.

        Returns:
            Normalized scores dictionary.
        """
        if not scores:
            return {}

        min_score = min(scores.values())
        max_score = max(scores.values())

        if max_score == min_score:
            return {item: 0.5 for item in scores}

        return {
            item: (score - min_score) / (max_score - min_score)
            for item, score in scores.items()
        }
