"""Utility functions for the quant_developing_program.

Provides:
    - trend_indicator: Compares current to previous value and returns a formatted arrow string.
    - format_probability: Formats a probability as a percentage string.
    - format_odds: Converts probability to decimal odds and formats it.
    - clamp: Clamps a value to a range.
    - safe_divide: Safe division that returns a default on zero denominator.
"""

from __future__ import annotations


def trend_indicator(current: float, previous: float) -> str:
    """Return a trend indicator comparing current to previous value.

    Args:
        current: The current period value.
        previous: The previous period value.

    Returns:
        A string like "▲ +12.3%", "▼ -5.0%", or "● 0.0%".
    """
    if previous == 0:
        return "● 0.0%"
    pct_change = ((current - previous) / abs(previous)) * 100
    if pct_change > 0:
        return f"▲ +{pct_change:.1f}%"
    elif pct_change < 0:
        return f"▼ {pct_change:.1f}%"
    else:
        return "● 0.0%"


def format_probability(prob: float) -> str:
    """Format a probability as a percentage string.

    Args:
        prob: Probability value (0 to 1).

    Returns:
        Formatted percentage string (e.g., "65.00%").
    """
    if prob < 0 or prob > 1:
        raise ValueError("prob must be between 0 and 1")
    return f"{prob * 100:.2f}%"


def format_odds(odds: float) -> str:
    """Convert decimal odds to formatted string.

    Args:
        odds: Decimal odds (e.g., 2.0 for even money).

    Returns:
        Formatted odds string (decimal, fractional, or American).
    """
    if odds <= 1:
        raise ValueError("odds must be greater than 1")
    if odds == 2.0:
        return "2.00"
    elif odds < 2.0:
        # Fractional odds
        fractional = odds - 1
        from fractions import Fraction
        frac = Fraction(fractional).limit_denominator(100)
        return f"{frac.numerator}/{frac.denominator}"
    else:
        # American odds
        american = int((odds - 1) * 100)
        return f"+{american}"


def format_odds_v2(odds: float) -> str:
    """Convert decimal odds to formatted string.

    Args:
        odds: Decimal odds (e.g., 2.0 for even money).

    Returns:
        Formatted odds string.
    """
    if odds <= 1:
        raise ValueError("odds must be greater than 1")
    return f"{odds:.2f}"


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value to a range.

    Args:
        value: Value to clamp.
        min_val: Minimum value.
        max_val: Maximum value.

    Returns:
        Clamped value.
    """
    if min_val > max_val:
        raise ValueError("min_val must be less than or equal to max_val")
    return max(min_val, min(max_val, value))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division that returns a default on zero denominator.

    Args:
        numerator: Numerator.
        denominator: Denominator.
        default: Default value if denominator is zero.

    Returns:
        Result of division or default.
    """
    if denominator == 0:
        return default
    return numerator / denominator


def expected_value(probability: float, odds: float, cost: float = 1.0) -> float:
    """Calculate expected value of a bet.

    Args:
        probability: Probability of winning.
        odds: Decimal odds for the outcome.
        cost: Cost (stake) of the bet.

    Returns:
        Expected value.
    """
    if probability < 0 or probability > 1:
        raise ValueError("probability must be between 0 and 1")
    if odds <= 1:
        raise ValueError("odds must be greater than 1")
    if cost <= 0:
        raise ValueError("cost must be positive")
    # Net profit = odds - 1 (you get your stake back plus profit)
    net_profit = odds - 1
    return probability * net_profit - (1 - probability) * cost


def implied_probability(decimal_odds: float) -> float:
    """Convert decimal odds to implied probability.

    Args:
        decimal_odds: Decimal odds (e.g., 2.0 for even money).

    Returns:
        Implied probability.
    """
    if decimal_odds <= 1:
        raise ValueError("decimal_odds must be greater than 1")
    return 1.0 / decimal_odds


def decimal_odds_from_probability(prob: float) -> float:
    """Convert probability to decimal odds.

    Args:
        prob: Probability (0 to 1).

    Returns:
        Decimal odds.
    """
    if prob <= 0 or prob >= 1:
        raise ValueError("prob must be between 0 and 1 (exclusive)")
    return 1.0 / prob
