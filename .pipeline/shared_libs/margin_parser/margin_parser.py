"""Margin string parser — parses CSS-like margin specifications."""


def parse_margins(margin_str: str) -> dict:
    """Parse margin string like 'top=1in right=1in bottom=1in left=1in'.

    Args:
        margin_str: Space-separated key=value pairs for margins.

    Returns:
        Dict with keys top, right, bottom, left and their parsed values.
        Unrecognized keys are silently ignored. Missing keys default to '1in'.
    """
    margins = {"top": "1in", "right": "1in", "bottom": "1in", "left": "1in"}
    if not margin_str:
        return margins
    for part in margin_str.split():
        if "=" in part:
            key, value = part.split("=", 1)
            if key in margins:
                margins[key] = value
    return margins
