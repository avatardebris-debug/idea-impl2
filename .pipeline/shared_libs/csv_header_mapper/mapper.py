"""CSV header normalization and canonical mapping.

Provides a configurable alias system for mapping common CSV header
variations to canonical column names.
"""

from typing import Dict, Optional


def normalise_header(header: str) -> str:
    """Lowercase and strip whitespace from a header name."""
    return header.strip().lower()


def map_header(raw_header: str, aliases: Dict[str, str]) -> Optional[str]:
    """Map a raw header to a canonical column name using the given alias map.

    Args:
        raw_header: The original CSV header string.
        aliases: A dict mapping normalised header strings to canonical names.

    Returns:
        The canonical column name, or None if no alias matches.
    """
    key = normalise_header(raw_header)
    return aliases.get(key)
