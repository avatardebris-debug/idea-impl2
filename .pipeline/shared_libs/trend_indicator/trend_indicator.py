"""Trend indicator utility — compares current to previous value and returns a formatted arrow string."""


def trend_indicator(current: float, previous: float) -> str:
    """Return a trend indicator comparing current to previous value.

    Args:
        current: The current period value.
        previous: The previous period value.

    Returns:
        A string like "▲ +12.3%", "▼ -5.0%", or "— 0.0%".
    """
    if previous == 0:
        return "—"
    pct_change = ((current - previous) / abs(previous)) * 100
    if pct_change > 0:
        return f"▲ {pct_change:+.1f}%"
    elif pct_change < 0:
        return f"▼ {pct_change:+.1f}%"
    else:
        return "— 0.0%"
