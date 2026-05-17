"""
Odds conversion and normalization engine.

Provides functions to convert between American, decimal, and fractional odds,
compute implied probabilities, and normalize all inputs to a common format.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from dfs_arb.core.models import OddsEntry, OddsFormat


def american_to_decimal(american_odds: float) -> float:
    """Convert American odds to decimal odds.

    Args:
        american_odds: American odds (e.g., -110, +150).

    Returns:
        Decimal odds.
    """
    if american_odds == 0:
        return 2.0
    elif american_odds > 0:
        return (american_odds / 100.0) + 1.0
    else:
        return (abs(american_odds) + 100.0) / abs(american_odds)


def decimal_to_american(decimal_odds: float) -> float:
    """Convert decimal odds to American odds.

    Args:
        decimal_odds: Decimal odds (e.g., 1.91, 2.50).

    Returns:
        American odds.
    """
    if decimal_odds >= 2.0:
        return round((decimal_odds - 1.0) * 100.0)
    else:
        return round(-100.0 / (decimal_odds - 1.0))


def american_to_fractional(american_odds: float) -> Tuple[int, int]:
    """Convert American odds to fractional odds.

    Args:
        american_odds: American odds (e.g., -110, +150).

    Returns:
        Tuple of (numerator, denominator) representing the fractional odds.
    """
    if american_odds > 0:
        # Positive American: odds/100
        numerator = int(american_odds)
        denominator = 100
        g = _gcd(numerator, denominator)
        return (numerator // g, denominator // g)
    else:
        # Negative American: 100/abs(odds)
        numerator = 100
        denominator = int(abs(american_odds))
        g = _gcd(numerator, denominator)
        return (numerator // g, denominator // g)


def fractional_to_american(numerator: int, denominator: int) -> float:
    """Convert fractional odds to American odds.

    Args:
        numerator: Numerator of fractional odds.
        denominator: Denominator of fractional odds.

    Returns:
        American odds.
    """
    if numerator >= denominator:
        # Underdog (positive American)
        return round((numerator / denominator) * 100.0)
    else:
        # Favorite (negative American)
        return round(-100.0 * (denominator / numerator))


def decimal_to_fractional(decimal_odds: float) -> Tuple[int, int]:
    """Convert decimal odds to fractional odds.

    Args:
        decimal_odds: Decimal odds.

    Returns:
        Tuple of (numerator, denominator).
    """
    # Subtract 1 to get the odds portion
    odds = decimal_odds - 1.0
    # Convert to fraction
    numerator = int(round(odds * 1000))
    denominator = 1000
    g = _gcd(numerator, denominator)
    return (numerator // g, denominator // g)


def fractional_to_decimal(numerator: int, denominator: int) -> float:
    """Convert fractional odds to decimal odds.

    Args:
        numerator: Numerator of fractional odds.
        denominator: Denominator of fractional odds.

    Returns:
        Decimal odds.
    """
    return (numerator / denominator) + 1.0


def implied_probability(decimal_odds: float, format: str = "decimal") -> float:
    """Compute implied probability from odds.

    Args:
        decimal_odds: Decimal odds (or American odds if format='american').
        format: The format of the input odds ('decimal' or 'american').

    Returns:
        Implied probability as a decimal (e.g., 0.526 for 52.6%).

    Raises:
        ValueError: If the format is not 'decimal' or 'american'.
    """
    if format not in ("decimal", "american"):
        raise ValueError(f"Unsupported odds format: {format}")
    if format == "american":
        decimal_odds = american_to_decimal(decimal_odds)
    if decimal_odds <= 1.0:
        raise ValueError("Decimal odds must be greater than 1.0")
    return 1.0 / decimal_odds


def _gcd(a: int, b: int) -> int:
    """Compute greatest common divisor."""
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def normalize_odds(
    odds_value: float,
    odds_format: OddsFormat,
    target_format: OddsFormat = OddsFormat.DECIMAL,
) -> float:
    """Normalize odds to a target format.

    Args:
        odds_value: The numeric odds value.
        odds_format: The current format of the odds.
        target_format: The desired output format.

    Returns:
        Odds value in the target format.
    """
    if odds_format == target_format:
        return odds_value

    # First convert to decimal
    if odds_format == OddsFormat.AMERICAN:
        decimal_odds = american_to_decimal(odds_value)
    elif odds_format == OddsFormat.FRACTIONAL:
        # Fractional odds_value is stored as numerator/denominator
        # We handle this by passing numerator and denominator separately
        raise ValueError(
            "Fractional odds must be passed as a tuple (numerator, denominator) "
            "or pre-converted to decimal"
        )
    else:
        decimal_odds = odds_value

    # Then convert from decimal to target
    if target_format == OddsFormat.AMERICAN:
        return decimal_to_american(decimal_odds)
    elif target_format == OddsFormat.FRACTIONAL:
        return decimal_to_fractional(decimal_odds)
    else:
        return decimal_odds


def odds_entry_to_decimal(entry: OddsEntry) -> float:
    """Convert an OddsEntry's odds to decimal format.

    Args:
        entry: An OddsEntry with odds in any format.

    Returns:
        The odds value in decimal format.

    Raises:
        ValueError: If the entry's odds_format is not recognized.
    """
    # Handle the case where odds_format might be a string (e.g., from type: ignore)
    odds_format = entry.odds_format
    if isinstance(odds_format, str):
        try:
            odds_format = OddsFormat(odds_format)
        except ValueError:
            raise ValueError(f"Unsupported odds format: {odds_format}")
    
    if odds_format == OddsFormat.AMERICAN:
        return american_to_decimal(entry.odds_value)
    elif odds_format == OddsFormat.DECIMAL:
        return entry.odds_value
    elif odds_format == OddsFormat.FRACTIONAL:
        # For fractional, odds_value stores numerator/denominator as a float
        # We need to reconstruct the fraction
        # This is a simplification; in practice, fractional odds should be stored differently
        return entry.odds_value
    else:
        raise ValueError(f"Unsupported odds format: {odds_format}")


def compute_implied_probabilities(entries: List[OddsEntry]) -> List[float]:
    """Compute implied probabilities for a list of odds entries.

    Args:
        entries: List of OddsEntry objects.

    Returns:
        List of implied probabilities (as decimals).
    """
    probs = []
    for entry in entries:
        decimal_odds = odds_entry_to_decimal(entry)
        prob = implied_probability(decimal_odds)
        probs.append(prob)
    return probs


def check_overround(entries: List[OddsEntry]) -> float:
    """Check the overround (vig) for a set of odds entries.

    The overround is the percentage by which the sum of implied probabilities
    exceeds 1.0. For a fair market, it should equal 0.0. Values > 0 indicate
    the bookmaker's margin. Values < 0 indicate an arbitrage opportunity.

    Args:
        entries: List of OddsEntry objects representing all outcomes of a market.

    Returns:
        The overround as a percentage (e.g., 5.26 for 5.26% vig).
    """
    probs = compute_implied_probabilities(entries)
    return (sum(probs) - 1.0) * 100.0


def find_best_odds(
    entries: List[OddsEntry],
    side: str,
) -> Tuple[Optional[OddsEntry], float]:
    """Find the best odds for a given side across multiple bookmakers.

    Args:
        entries: List of OddsEntry objects from different bookmakers.
        side: The side to filter by (e.g., 'over', 'under').

    Returns:
        Tuple of (best entry, best decimal odds).
        Returns (None, 0.0) if no entries are found for the side.
    """
    matching = [e for e in entries if e.side == side]
    if not matching:
        return None, 0.0

    best_entry = None
    best_decimal = -1.0

    for entry in matching:
        decimal = odds_entry_to_decimal(entry)
        if decimal is not None and decimal > best_decimal:
            best_decimal = decimal
            best_entry = entry

    return best_entry, best_decimal
