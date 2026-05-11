"""Self-contained HTML-escaping utility.

Extracted from multi_format_export_engine.
"""


def escape_html(text: str) -> str:
    """Escape HTML special characters in text.

    Args:
        text: Raw string to escape.

    Returns:
        String with &, <, >, and " replaced with HTML entities.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
