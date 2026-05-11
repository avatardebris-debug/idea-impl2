"""Column name resolver — finds a DataFrame column matching one of several candidate keys.

Prioritizes exact matches over partial matches.
"""

import pandas as pd


def _normalize_key(key: str) -> str:
    """Normalize a column/metric key to lowercase with underscores."""
    return key.strip().lower().replace(" ", "_").replace("-", "_")


def find_column(df: pd.DataFrame, keys: list) -> str:
    """Find a column in the DataFrame matching one of the given keys.

    Prioritizes exact matches over partial matches.

    Args:
        df: The DataFrame to search.
        keys: List of candidate column name keys.

    Returns:
        The matching column name, or empty string if none found.
    """
    # Exact match first
    for col in df.columns:
        norm = _normalize_key(col)
        if norm in keys:
            return col
    # Partial match — only match if the key is a substring of the column name
    # (not the other way around, to avoid "cost of revenue" matching "Revenue")
    for col in df.columns:
        norm = _normalize_key(col)
        for key in keys:
            if key in norm:
                return col
    return ""
