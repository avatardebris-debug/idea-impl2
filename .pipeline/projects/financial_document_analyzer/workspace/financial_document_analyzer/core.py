"""Core data models and shared utilities for the financial document analyzer."""

from typing import Dict, Any, Optional


def _safe_divide(numerator: float, denominator: float) -> float:
    """Divide two numbers safely, returning 0.0 if denominator is zero."""
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _normalize_key(key: str) -> str:
    """Normalize a column/metric key to lowercase with underscores."""
    return key.strip().lower().replace(" ", "_").replace("-", "_")


def _extract_numeric(value: str) -> float:
    """Extract a numeric value from a string, handling commas, parentheses, and currency symbols."""
    if value is None:
        return 0.0
    cleaned = str(value).strip()
    # Remove currency symbols and commas
    cleaned = cleaned.replace("$", "").replace(",", "").replace("(", "").replace(")", "")
    # Handle parenthetical negatives: (1,234) -> -1234
    if "(" in cleaned and ")" in cleaned:
        cleaned = "-" + cleaned.replace("(", "").replace(")", "")
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return 0.0


def build_metrics_dict(
    filename: str,
    revenue: float = 0.0,
    cogs: float = 0.0,
    gross_profit: float = 0.0,
    operating_income: float = 0.0,
    net_income: float = 0.0,
    raw_rows: int = 0,
) -> Dict[str, Any]:
    """Build a standard metrics dict from raw financial values."""
    gross_margin = _safe_divide(gross_profit, revenue) * 100
    operating_margin = _safe_divide(operating_income, revenue) * 100
    net_margin = _safe_divide(net_income, revenue) * 100

    return {
        "filename": filename,
        "metrics": {
            "revenue": revenue,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "operating_income": operating_income,
            "net_income": net_income,
        },
        "margins": {
            "gross_margin": gross_margin,
            "operating_margin": operating_margin,
            "net_margin": net_margin,
        },
        "raw_rows": raw_rows,
    }
