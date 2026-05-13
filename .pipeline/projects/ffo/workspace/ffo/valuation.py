"""Player valuation model for FFO."""

from __future__ import annotations

from typing import Optional

from ffo.models.player import Player


def value_player(player: Player, age_weight: float = 1.0, contract_weight: float = 1.0) -> float:
    """Compute a player's financial value score.

    The score reflects cost-effectiveness: higher rating, lower salary,
    younger age, and longer contract all improve the score.

    Formula:
        score = (overall_rating / salary) * age_factor * contract_factor

    Where:
        age_factor: Younger players get a boost. At age 30, factor is 1.0.
                    For each year younger, add 0.01. For each year older, subtract 0.01.
                    Clamped to [0.5, 1.5].
        contract_factor: Longer contracts get a boost. At 1 year, factor is 1.0.
                         For each additional year, add 0.05.
                         Clamped to [0.5, 2.0].

    Args:
        player: The player to evaluate.
        age_weight: Weight to apply to the age factor (0.0 to disable).
        contract_weight: Weight to apply to the contract factor (0.0 to disable).

    Returns:
        The player's value score. Returns infinity if salary is 0.

    Raises:
        ValueError: If player is None.
    """
    if player is None:
        raise ValueError("Player cannot be None")

    if player.salary == 0:
        return float("inf")

    base_score = player.overall_rating / player.salary

    # Age factor: younger is better
    age_diff = 30 - player.age
    age_factor = 1.0 + age_diff * 0.01
    age_factor = max(0.5, min(1.5, age_factor))

    # Contract factor: longer is better
    contract_factor = 1.0 + (player.contract_length - 1) * 0.05
    contract_factor = max(0.5, min(2.0, contract_factor))

    # Apply weights
    # If weight is 0, the factor should not affect the score (multiply by 1.0)
    # If weight is > 0, apply the factor raised to the weight power
    if age_weight == 0:
        age_factor = 1.0
    else:
        age_factor = age_factor ** age_weight

    if contract_weight == 0:
        contract_factor = 1.0
    else:
        contract_factor = contract_factor ** contract_weight

    score = base_score * age_factor * contract_factor

    # Ensure score is positive
    if score <= 0:
        score = abs(score)

    return score


def rank_by_efficiency(
    players: list[Player],
    age_weight: float = 1.0,
    contract_weight: float = 1.0,
) -> list[Player]:
    """Rank players by their financial value score.

    Args:
        players: List of players to rank.
        age_weight: Weight to apply to the age factor.
        contract_weight: Weight to apply to the contract factor.

    Returns:
        List of players sorted by value score in descending order.
    """
    if not players:
        return []

    scored_players = [
        (value_player(p, age_weight, contract_weight), p)
        for p in players
    ]

    # Sort by score descending
    scored_players.sort(key=lambda x: x[0], reverse=True)

    # Return just the players
    return [p for _, p in scored_players]
