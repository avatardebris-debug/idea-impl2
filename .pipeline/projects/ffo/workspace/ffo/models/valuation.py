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
        age_factor: Younger players get a boost. At age 30, factor=1.0.
                    Below 30: factor = 1 + (30 - age) * 0.01
                    Above 30: factor = 1 - (age - 30) * 0.01
        contract_factor: Longer contracts get a boost.
                         factor = 1 + (contract_length - 1) * 0.05

    Args:
        player: The player to value.
        age_weight: Multiplier for the age factor (default 1.0).
        contract_weight: Multiplier for the contract factor (default 1.0).

    Returns:
        A numeric score reflecting cost-effectiveness.
    """
    if player.salary <= 0:
        return float("inf")

    # Base value-per-salary
    base = player.overall_rating / player.salary

    # Age factor: peak around age 27-30
    if player.age <= 30:
        age_factor = 1.0 + (30 - player.age) * 0.01
    else:
        age_factor = max(0.5, 1.0 - (player.age - 30) * 0.01)

    # Contract factor: longer contracts are more valuable
    contract_factor = 1.0 + (player.contract_length - 1) * 0.05

    score = base * age_factor * contract_factor
    return score * age_weight * contract_weight


def rank_by_efficiency(
    players: list[Player],
    age_weight: float = 1.0,
    contract_weight: float = 1.0,
) -> list[Player]:
    """Rank players by value efficiency (descending).

    Args:
        players: List of players to rank.
        age_weight: Weight for age factor.
        contract_weight: Weight for contract factor.

    Returns:
        List of players sorted by score descending.
    """
    scored = [(p, value_player(p, age_weight, contract_weight)) for p in players]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [p for p, _ in scored]
