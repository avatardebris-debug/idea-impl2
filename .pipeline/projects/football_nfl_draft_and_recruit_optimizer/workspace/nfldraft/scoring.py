"""Player scoring engine for NFL draft and recruit optimizer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from nfldraft.models import Player, Position


@dataclass
class ScoringConfig:
    """Configuration for player scoring weights."""
    # Position-specific base weights (how much each position's rating matters)
    position_weights: dict[Position, float] = field(default_factory=lambda: {
        Position.QB: 1.2,
        Position.RB: 0.9,
        Position.WR: 1.0,
        Position.TE: 0.95,
        Position.OL: 0.85,
        Position.DL: 0.9,
        Position.LB: 0.95,
        Position.CB: 1.0,
        Position.S: 0.95,
        Position.K: 0.5,
        Position.P: 0.5,
        Position.EDGE: 1.0,
        Position.ILB: 0.95,
        Position.OLB: 1.0,
        Position.T: 0.9,
        Position.G: 0.85,
        Position.C: 0.9,
        Position.FS: 0.95,
        Position.SS: 1.0,
        Position.UNKNOWN: 0.8,
    })

    # Age factor weights
    age_peak: int = 27
    age_boost_per_year_below_peak: float = 0.02
    age_penalty_per_year_above_peak: float = 0.015

    # Value efficiency weights
    salary_weight: float = 0.3
    contract_length_weight: float = 0.1

    # Stats weights (multipliers for specific stats)
    stats_weights: dict[str, float] = field(default_factory=lambda: {
        "passing_yards": 0.0001,
        "passing_tds": 0.005,
        "rushing_yards": 0.0002,
        "rushing_tds": 0.008,
        "receiving_yards": 0.00015,
        "receiving_tds": 0.006,
        "tackles": 0.001,
        "sacks": 0.003,
        "interceptions": 0.005,
        "forced_fumbles": 0.004,
        "fumble_recoveries": 0.003,
    })

    # Strength/weakness impact
    strength_weight: float = 0.5
    weakness_weight: float = -0.3


class PlayerScorer:
    """Scores and ranks players based on configurable criteria."""

    def __init__(self, config: Optional[ScoringConfig] = None):
        self.config = config or ScoringConfig()

    def score_player(self, player: Player) -> dict:
        """Compute a comprehensive score for a player.

        Returns a dict with:
            - total_score: overall score (0-100+)
            - rating_score: base rating component
            - age_score: age factor component
            - value_score: cost-effectiveness component
            - stats_score: stats-based component
            - breakdown: detailed sub-scores
        """
        # 1. Base rating with position weight
        pos_weight = self.config.position_weights.get(player.position, 0.8)
        rating_score = player.overall_rating * pos_weight

        # 2. Age factor
        age_score = self._compute_age_score(player.age)

        # 3. Value efficiency (rating per dollar)
        value_score = self._compute_value_score(player)

        # 4. Stats contribution
        stats_score = self._compute_stats_score(player)

        # 5. Strengths/weaknesses adjustment
        adjustment = self._compute_adjustment(player)

        # Total score (normalized to roughly 0-100 range)
        total_score = rating_score + age_score + value_score + stats_score + adjustment
        total_score = max(0.0, total_score)

        return {
            "total_score": round(total_score, 2),
            "rating_score": round(rating_score, 2),
            "age_score": round(age_score, 2),
            "value_score": round(value_score, 2),
            "stats_score": round(stats_score, 2),
            "adjustment": round(adjustment, 2),
            "breakdown": {
                "position_weight": pos_weight,
                "overall_rating": player.overall_rating,
                "age": player.age,
                "salary": player.salary,
                "contract_length": player.contract_length,
            },
        }

    def _compute_age_score(self, age: int) -> float:
        """Compute age factor score."""
        if age is None or age <= 0:
            return 0.0
        peak = self.config.age_peak
        if age <= peak:
            years_below = peak - age
            return years_below * self.config.age_boost_per_year_below_peak * 10
        else:
            years_above = age - peak
            return -years_above * self.config.age_penalty_per_year_above_peak * 10

    def _compute_value_score(self, player: Player) -> float:
        """Compute value efficiency score."""
        salary = player.salary if player.salary is not None else 0.0
        if salary <= 0:
            return 0.0
        # Rating per million dollars
        rating_per_million = player.overall_rating / salary
        # Normalize: a player rated 80 for $2M = 40 rating/million
        # Scale to roughly 0-20 range
        value = rating_per_million * 10
        # Contract length bonus
        contract_length = player.contract_length if player.contract_length is not None else 0
        contract_bonus = (contract_length - 1) * self.config.contract_length_weight * 5
        return value + contract_bonus

    def _compute_stats_score(self, player: Player) -> float:
        """Compute stats-based score."""
        total = 0.0
        stats = player.stats if player.stats is not None else {}
        for stat_name, stat_value in stats.items():
            weight = self.config.stats_weights.get(stat_name, 0)
            total += stat_value * weight
        return total

    def _compute_adjustment(self, player: Player) -> float:
        """Compute strengths/weaknesses adjustment."""
        total = 0.0
        strengths = player.strengths if player.strengths is not None else []
        weaknesses = player.weaknesses if player.weaknesses is not None else []
        for strength in strengths:
            total += self.config.strength_weight
        for weakness in weaknesses:
            total += self.config.weakness_weight
        return total

    def rank_players(self, players: list[Player]) -> list[tuple[Player, dict]]:
        """Rank players by score (descending)."""
        scored = [(p, self.score_player(p)) for p in players]
        scored.sort(key=lambda x: x[1]["total_score"], reverse=True)
        return scored


def score_player(player: Player, config: Optional[ScoringConfig] = None) -> dict:
    """Convenience function to score a single player."""
    scorer = PlayerScorer(config)
    return scorer.score_player(player)


def rank_players(
    players: list[Player],
    config: Optional[ScoringConfig] = None,
) -> list[tuple[Player, dict]]:
    """Convenience function to rank players by score."""
    scorer = PlayerScorer(config)
    return scorer.rank_players(players)
