"""HTML character escaping utility — escapes &, <, >, and " for safe HTML output."""


def escape_html(text: str) -> str:
    """Escape HTML special characters in text.

    Args:
        text: Raw string to escape.

    Returns:
        String with &, <, >, and " replaced with their HTML entity equivalents.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
