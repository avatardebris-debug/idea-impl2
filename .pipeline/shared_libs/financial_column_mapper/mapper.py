"""Financial column name mappings and column-finding utility for financial document parsing."""

import pandas as pd


def _normalize_key(key: str) -> str:
    """Normalize a column/metric key to lowercase with underscores."""
    return key.strip().lower().replace(" ", "_").replace("-", "_")


# Column name mappings: normalized key -> list of possible column names
REVENUE_KEYS = ["revenue", "total_revenue", "revenues", "total sales", "sales", "turnover", "net sales", "net_revenue"]
COGS_KEYS = ["cost of goods", "cogs", "cost of goods sold", "cost of revenue", "cost_of_goods"]
GROSS_PROFIT_KEYS = ["gross profit", "gross_profit", "gross margin", "gross_margin"]
OPERATING_INCOME_KEYS = [
    "operating income", "operating_income", "operating profit", "operating_profit",
    "ebit", "income from operations", "income_from_operations",
]
NET_INCOME_KEYS = [
    "net income", "net_income", "net profit", "net_profit",
    "profit for the period", "profit_for_the_period", "bottom line",
    "earnings", "net earnings", "net_earnings",
]


def find_column(df: pd.DataFrame, keys: list) -> str:
    """Find a column in the DataFrame matching one of the given keys.

    Prioritizes exact matches over partial matches.

    Args:
        df: DataFrame to search.
        keys: List of normalized key strings to match against.

    Returns:
        The matching column name, or empty string if no match found.
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
