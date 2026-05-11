"""Currency formatting utility — scales numbers to K/M/B notation."""


def format_currency(value: float) -> str:
    """Format a number as currency string.

    Args:
        value: The numeric value to format.

    Returns:
        A string like "$1.23M", "$45.67K", etc.
    """
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"
    elif abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    elif abs(value) >= 1_000:
        return f"${value / 1_000:,.2f}K"
    else:
        return f"${value:,.2f}"
