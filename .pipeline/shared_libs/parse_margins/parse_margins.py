"""Reusable margin string parser for CLI tools.

Extracted from multi_format_export_engine.
Parses margin strings like 'top=1in right=1in bottom=1in left=1in' into a dict.
"""

import sys


def parse_margins(margin_str: str) -> dict:
    """Parse a margin string into a dict with top/right/bottom/left keys.

    Args:
        margin_str: String like 'top=1in right=1in bottom=1in left=1in'.

    Returns:
        Dict with margin keys and values. Defaults to '1in' for any missing key.
    """
    margins = {"top": "1in", "right": "1in", "bottom": "1in", "left": "1in"}
    if not margin_str:
        return margins
    for part in margin_str.split():
        if "=" in part:
            key, value = part.split("=", 1)
            if key in margins:
                margins[key] = value
            else:
                print(
                    f"Warning: unrecognized margin key '{key}' ignored "
                    f"(valid keys: top, right, bottom, left)",
                    file=sys.stderr,
                )
    return margins
