"""
reporter.py — Monthly budget reports and anomaly detection.
"""
from __future__ import annotations
import re
import statistics
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from finance_tracker.categorizer import Transaction


@dataclass
class MonthSummary:
    month:      str                    # "YYYY-MM"
    income:     float
    expenses:   float
    net:        float
    by_category: dict[str, float]
    transaction_count: int


def _parse_month(date_str: str) -> str:
    """Extract YYYY-MM from various date formats."""
    if not date_str:
        return "0000-00"
    m = re.search(r"(\d{4})[/-](\d{2})", date_str)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    # Try MM/DD/YYYY
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", date_str)
    if m:
        return f"{m.group(3)}-{m.group(1).zfill(2)}"
    return date_str[:7]


def summarize_by_month(
    transactions: list[Transaction],
    month: str | None = None,
) -> list[MonthSummary]:
    """Summarise transactions by month (optionally filtered to one month)."""
    grouped: dict[str, list[Transaction]] = defaultdict(list)
    for t in transactions:
        key = _parse_month(t.date)
        if month and key != month:
            continue
        grouped[key].append(t)

    summaries = []
    for m, txns in sorted(grouped.items()):
        income   = sum(t.amount for t in txns if t.amount > 0)
        expenses = sum(abs(t.amount) for t in txns if t.amount < 0)
        by_cat: dict[str, float] = defaultdict(float)
        for t in txns:
            if t.amount < 0:
                by_cat[t.category] += abs(t.amount)

        summaries.append(MonthSummary(
            month=m,
            income=income,
            expenses=expenses,
            net=income - expenses,
            by_category=dict(sorted(by_cat.items(), key=lambda x: -x[1])),
            transaction_count=len(txns),
        ))
    return summaries


def detect_anomalies(
    transactions: list[Transaction],
    z_threshold: float = 2.5,
) -> list[dict[str, Any]]:
    """Flag transactions with amounts that are statistical outliers per category.

    Uses z-score within each category. Transactions more than z_threshold
    standard deviations above the category mean are flagged.

    Returns list of anomaly dicts.
    """
    by_cat: dict[str, list[Transaction]] = defaultdict(list)
    for t in transactions:
        if t.amount < 0:
            by_cat[t.category].append(t)

    anomalies = []
    for cat, txns in by_cat.items():
        amounts = [abs(t.amount) for t in txns]
        if len(amounts) < 3:
            continue
        mean = statistics.mean(amounts)
        stdev = statistics.stdev(amounts)
        if stdev == 0:
            continue
        for t, amt in zip(txns, amounts):
            z = (amt - mean) / stdev
            if z >= z_threshold:
                anomalies.append({
                    "date":        t.date,
                    "description": t.description,
                    "category":    cat,
                    "amount":      abs(t.amount),
                    "category_mean": round(mean, 2),
                    "z_score":     round(z, 2),
                    "severity":    "high" if z >= z_threshold * 1.5 else "medium",
                })

    return sorted(anomalies, key=lambda a: -a["z_score"])


def format_report(summaries: list[MonthSummary], anomalies: list[dict] | None = None) -> str:
    """Render budget report as Markdown."""
    lines = ["# 💰 Personal Finance Report", ""]

    for s in summaries:
        lines += [
            f"## {s.month}",
            "",
            f"| Metric | Amount |",
            "|---|---|",
            f"| 📥 Income    | ${s.income:>10,.2f} |",
            f"| 📤 Expenses  | ${s.expenses:>10,.2f} |",
            f"| 📊 Net       | ${s.net:>10,.2f} |",
            f"| 🧾 Transactions | {s.transaction_count} |",
            "",
            "**Spending by Category:**",
            "",
        ]
        if s.by_category:
            lines += ["| Category | Amount | % of Expenses |", "|---|---|---|"]
            for cat, amt in list(s.by_category.items())[:15]:
                pct = (amt / s.expenses * 100) if s.expenses else 0
                lines.append(f"| {cat} | ${amt:,.2f} | {pct:.1f}% |")
        lines.append("")

    if anomalies:
        lines += ["---", "", "## ⚠️ Spending Anomalies", ""]
        lines += ["| Date | Description | Category | Amount | Z-Score | Severity |",
                  "|---|---|---|---|---|---|"]
        for a in anomalies[:20]:
            lines.append(
                f"| {a['date']} | {a['description'][:30]} | {a['category']} | "
                f"${a['amount']:,.2f} | {a['z_score']} | {a['severity']} |"
            )
        lines.append("")

    return "\n".join(lines)
