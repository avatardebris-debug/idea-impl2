"""Report generator for financial document analyzer."""

from typing import Dict, Any, Optional


def _format_currency(value: float) -> str:
    """Format a number as currency string."""
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.2f}B"
    elif abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"
    elif abs(value) >= 1_000:
        return f"${value / 1_000:,.2f}K"
    else:
        return f"${value:,.2f}"


def _trend_indicator(current: float, previous: float) -> str:
    """Return a trend indicator comparing current to previous value."""
    if previous == 0:
        return "—"
    pct_change = ((current - previous) / abs(previous)) * 100
    if pct_change > 0:
        return f"▲ {pct_change:+.1f}%"
    elif pct_change < 0:
        return f"▼ {pct_change:+.1f}%"
    else:
        return "— 0.0%"


def generate_report(
    metrics_dict: Dict[str, Any],
    previous_metrics: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a structured text summary report from parsed metrics.

    Args:
        metrics_dict: The parsed metrics dict from parse_csv or parse_pdf.
        previous_metrics: Optional previous period metrics for trend comparison.

    Returns:
        A formatted string report.
    """
    filename = metrics_dict.get("filename", "Unknown")
    metrics = metrics_dict.get("metrics", {})
    margins = metrics_dict.get("margins", {})
    raw_rows = metrics_dict.get("raw_rows", 0)

    lines = []
    lines.append("=" * 60)
    lines.append("  FINANCIAL DOCUMENT ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append(f"  Source file: {filename}")
    lines.append(f"  Raw rows parsed: {raw_rows}")
    lines.append("")

    # Key metrics
    lines.append("-" * 60)
    lines.append("  KEY METRICS")
    lines.append("-" * 60)

    metric_labels = {
        "revenue": "Revenue",
        "cogs": "Cost of Goods Sold",
        "gross_profit": "Gross Profit",
        "operating_income": "Operating Income",
        "net_income": "Net Income",
    }

    for key, label in metric_labels.items():
        value = metrics.get(key, 0)
        trend = ""
        if previous_metrics and key in previous_metrics.get("metrics", {}):
            prev_val = previous_metrics["metrics"][key]
            trend = f"  {_trend_indicator(value, prev_val)}"
        lines.append(f"  {label:<25s} {_format_currency(value):>15s}  {trend}")

    lines.append("")

    # Margins
    lines.append("-" * 60)
    lines.append("  MARGINS")
    lines.append("-" * 60)

    margin_labels = {
        "gross_margin": "Gross Margin",
        "operating_margin": "Operating Margin",
        "net_margin": "Net Margin",
    }

    for key, label in margin_labels.items():
        value = margins.get(key, 0)
        trend = ""
        if previous_metrics and key in previous_metrics.get("margins", {}):
            prev_val = previous_metrics["margins"][key]
            trend = f"  {_trend_indicator(value, prev_val)}"
        lines.append(f"  {label:<25s} {value:>12.2f}%  {trend}")

    lines.append("")
    lines.append("=" * 60)
    lines.append("  END OF REPORT")
    lines.append("=" * 60)

    return "\n".join(lines)
