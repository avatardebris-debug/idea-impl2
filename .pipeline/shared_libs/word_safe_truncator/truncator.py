"""Word-safe text truncation utility.

Truncates text to a maximum length, breaking at the last word boundary
to avoid cutting words in half.
"""


def truncate_word_safe(text: str, max_length: int) -> str:
    """Truncate text to max_length, breaking at the last word boundary.

    Args:
        text: The text to truncate.
        max_length: Maximum allowed length.

    Returns:
        Truncated text. If no space is found past max_length // 2,
        appends '..' to indicate truncation.
    """
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length // 2:
        return truncated[:last_space].strip()
    return truncated.strip() + ".."
