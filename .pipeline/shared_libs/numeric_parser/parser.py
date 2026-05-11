"""Robust numeric string parsing utilities.

Strips currency symbols, commas, whitespace, and percentage signs
before parsing strings to float or int.
"""


def parse_numeric(value: str) -> float | None:
    """Try to parse a numeric value from a string.

    Strips '$', ',', '%', and whitespace before parsing.

    Args:
        value: The string to parse.

    Returns:
        Parsed float, or None if parsing fails.
    """
    if value is None or value.strip() == "":
        return None
    cleaned = value.strip().replace(",", "").replace("$", "").replace("%", "").replace(" ", "")
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def parse_int(value: str) -> int | None:
    """Try to parse an integer value from a string.

    Strips '$', ',', '%', and whitespace before parsing.

    Args:
        value: The string to parse.

    Returns:
        Parsed int, or None if parsing fails.
    """
    if value is None or value.strip() == "":
        return None
    cleaned = value.strip().replace(",", "").replace("$", "").replace("%", "").replace(" ", "")
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return None
