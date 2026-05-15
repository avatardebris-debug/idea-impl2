"""Analytics engine for manuscript sales data."""

from __future__ import annotations

import csv
import os
from collections import defaultdict
from typing import Any

from manuscriptdata_analyzer.database import Database


# ──────────────────────────────────────────────
# TrendAnalyzer
# ──────────────────────────────────────────────


class TrendAnalyzer:
    """Detect spikes and drops in daily sales using rolling averages."""

    def __init__(self, db: Database):
        self.db = db

    def analyze_book_trend(
        self, book_title: str, window: int = 3
    ) -> dict[str, Any]:
        """Analyse sales trend for *book_title*.

        Returns a dict with keys ``book_title``, ``daily_sales``, ``spikes``, ``drops``.
        """
        series = self.db.get_book_sales_series(book_title)
        if not series:
            return {"daily_series": [], "spikes": [], "drops": []}

        values = [entry["units_sold"] for entry in series]
        n = len(values)

        spikes: list[dict[str, Any]] = []
        drops: list[dict[str, Any]] = []

        for i in range(n):
            start = max(0, i - window)
            end = min(n, i + window + 1)
            window_vals = [v for j, v in enumerate(values) if start <= j < end and j != i]
            if not window_vals:
                continue
            avg = sum(window_vals) / len(window_vals)
            if avg == 0:
                continue
            deviation = (values[i] - avg) / avg * 100
            if deviation > 20:
                spikes.append({
                    "index": i,
                    "value": values[i],
                    "rolling_avg": round(avg, 2),
                    "deviation_pct": round(deviation, 1),
                })
            elif deviation < -20:
                drops.append({
                    "index": i,
                    "value": values[i],
                    "rolling_avg": round(avg, 2),
                    "deviation_pct": round(deviation, 1),
                })

        return {
            "book_title": book_title,
            "daily_sales": series,
            "rolling_avg": round(sum(values) / len(values), 2) if values else 0,
            "spikes": spikes,
            "drops": drops,
        }

    def analyze_all_books(self, window: int = 3) -> list[dict[str, Any]]:
        """Analyse trends for every book in the database."""
        books = self.db.get_unique_books()
        return [self.analyze_book_trend(b, window) for b in books]

    # Alias for test compatibility
    analyze_book = analyze_book_trend


# ──────────────────────────────────────────────
# BookComparator
# ──────────────────────────────────────────────


class BookComparator:
    """Compare books across multiple metrics."""

    def __init__(self, db: Database):
        self.db = db

    def get_book_rankings(self, metric: str = "revenue") -> list[dict[str, Any]]:
        """Return books ranked by *metric* (``'revenue'``, ``'units_sold'``, or ``'engagement'``)."""
        if metric == "engagement":
            return self.db.get_book_engagement()
        return self.db.get_book_ranking(metric)

    def compare_books(self, book_titles: tuple[str, ...]) -> dict[str, dict[str, Any]]:
        """Compare the given books and return a dict keyed by book title."""
        result: dict[str, dict[str, Any]] = {}
        for title in book_titles:
            sales = self.db.get_book_sales_series(title)
            if not sales:
                continue
            total_rev = sum(s["revenue"] for s in sales)
            total_units = sum(s["units_sold"] for s in sales)
            result[title] = {
                "Revenue": total_rev,
                "Units Sold": total_units,
                "Days": len(sales),
            }
        return result


# ──────────────────────────────────────────────
# ReportGenerator
# ──────────────────────────────────────────────


class ReportGenerator:
    """Generate text reports and CSV exports."""

    def __init__(self, db: Database):
        self.db = db

    def generate_text_report(self, window: int = 3) -> dict[str, Any]:
        """Generate a full analytics report and return it as a dict."""
        lines: list[str] = []
        sep = "=" * 60

        lines.append(sep)
        lines.append("  ManuscriptData Analyzer — Full Analytics Report")
        lines.append(sep)
        lines.append("")

        # ── Sales Summary ──
        sales = self.db.get_sales_summary()
        lines.append("── Sales Summary ──")
        if sales:
            lines.append(f"  Total Units Sold : {sales['total_units']}")
            lines.append(f"  Total Revenue    : ${sales['total_revenue']:,.2f}")
            lines.append(f"  Avg Revenue      : ${sales['avg_revenue']:,.2f}")
            lines.append(f"  Avg Units Sold   : {sales['avg_units']:.1f}")
            lines.append(f"  Records          : {sales['record_count']}")
            if sales.get("platform_breakdown"):
                lines.append("  Platform Breakdown:")
                for platform, info in sales["platform_breakdown"].items():
                    lines.append(
                        f"    {platform}: {info['count']} records, "
                        f"{info['units']} units, ${info['revenue']:,.2f}"
                    )
        else:
            lines.append("  (no sales data)")
        lines.append("")

        # ── Demographics ──
        demo = self.db.get_demographics_summary()
        lines.append("── Demographics ──")
        if demo:
            lines.append(f"  Total Records : {demo['total_records']}")
            lines.append("  Age Group Breakdown:")
            for ag, cnt in demo["age_breakdown"].items():
                lines.append(f"    {ag}: {cnt['count']}")
            lines.append("  Gender Breakdown:")
            for g, cnt in demo["gender_breakdown"].items():
                lines.append(f"    {g}: {cnt['count']}")
            lines.append("  Country Breakdown:")
            for c, cnt in demo["country_breakdown"].items():
                lines.append(f"    {c}: {cnt['count']}")
        else:
            lines.append("  (no demographics data)")
        lines.append("")

        # ── Content Metrics ──
        content = self.db.get_content_metrics_summary()
        lines.append("── Content Metrics ──")
        if content:
            lines.append(f"  Total Chapters    : {content['total_chapters']}")
            lines.append(f"  Total Word Count  : {content['total_words']}")
            lines.append(f"  Avg Words/Chapter : {content['avg_words']:,.0f}")
            lines.append("  Chapter Details:")
            for ch in content["chapter_details"]:
                lines.append(
                    f"    Ch {ch['chapter']:>3}: {ch['word_count']:>6,} words, "
                    f"read-through {ch['read_through']:.0%}, "
                    f"completion {ch['completion']:.0%}"
                )
        else:
            lines.append("  (no content metrics data)")
        lines.append("")

        # ── Trend Analysis ──
        analyzer = TrendAnalyzer(self.db)
        trends = analyzer.analyze_all_books(window)
        lines.append("── Trend Analysis ──")
        if trends:
            for t in trends:
                lines.append(f"  Book: {t['book_title']}")
                if t["daily_sales"]:
                    lines.append(f"    Daily Series:")
                    for entry in t["daily_sales"]:
                        lines.append(
                            f"      {entry['date']}: {entry['units_sold']} units"
                        )
                if t["spikes"]:
                    lines.append("    Spikes:")
                    for s in t["spikes"]:
                        lines.append(
                            f"      Day {s['index'] + 1}: {s['value']} units "
                            f"({s['deviation_pct']:+.1f}% vs avg {s['rolling_avg']})"
                        )
                if t["drops"]:
                    lines.append("    Drops:")
                    for d in t["drops"]:
                        lines.append(
                            f"      Day {d['index'] + 1}: {d['value']} units "
                            f"({d['deviation_pct']:+.1f}% vs avg {d['rolling_avg']})"
                        )
                lines.append("")
        else:
            lines.append("  (no trend data)")
        lines.append("")

        # ── Book Rankings ──
        comparator = BookComparator(self.db)
        lines.append("── Book Rankings ──")
        for metric in ("revenue", "units_sold", "engagement"):
            ranked = comparator.get_book_rankings(metric)
            if ranked:
                lines.append(f"  By {metric}:")
                for rank, entry in enumerate(ranked, 1):
                    val = entry.get(metric, 0)
                    if metric == "engagement":
                        val_str = f"{val:.2f}"
                    elif metric == "revenue":
                        val_str = f"${val:,.2f}"
                    else:
                        val_str = str(val)
                    lines.append(f"    {rank}. {entry['book_title']}: {val_str}")
                lines.append("")
        lines.append(sep)

        # Return as dict for test compatibility
        return {
            "report": "\n".join(lines),
            "demographics": demo,
            "sales": sales,
            "content": content,
            "trends": trends,
        }

    def export_csv(
        self,
        output_path: str,
        data_type: str = "sales",
    ) -> list[dict[str, Any]]:
        """Export analytics data to a CSV file.

        Parameters
        ----------
        output_path : str
            Destination file path.
        data_type : str
            One of ``'sales'``, ``'demographics'``, ``'content_metrics'``.

        Returns
        -------
        list[dict]
            The rows that were written.
        """
        if data_type == "sales":
            summary = self.db.get_sales_summary()
            if not summary:
                raise ValueError("No sales data to export.")
            rows = [
                {"metric": "total_units", "value": summary["total_units"]},
                {"metric": "total_revenue", "value": summary["total_revenue"]},
                {"metric": "avg_revenue", "value": summary["avg_revenue"]},
                {"metric": "record_count", "value": summary["record_count"]},
            ]
            for plat, cnt in summary["platform_breakdown"].items():
                rows.append({"metric": f"platform_{plat}", "value": cnt})

        elif data_type == "demographics":
            summary = self.db.get_demographics_summary()
            if not summary:
                raise ValueError("No demographics data to export.")
            rows = [
                {"metric": "total_records", "value": summary["total_records"]},
            ]
            for ag, cnt in summary["age_breakdown"].items():
                rows.append({"metric": f"age_{ag}", "value": cnt["count"]})
            for g, cnt in summary["gender_breakdown"].items():
                rows.append({"metric": f"gender_{g}", "value": cnt["count"]})
            for c, cnt in summary["country_breakdown"].items():
                rows.append({"metric": f"country_{c}", "value": cnt["count"]})

        elif data_type == "content_metrics":
            summary = self.db.get_content_metrics_summary()
            if not summary:
                raise ValueError("No content metrics data to export.")
            rows = [
                {"metric": "total_chapters", "value": summary["total_chapters"]},
                {"metric": "total_words", "value": summary["total_words"]},
                {"metric": "avg_words", "value": summary["avg_words"]},
            ]
            for ch in summary["chapter_details"]:
                rows.append({
                    "metric": f"chapter_{ch['chapter']}",
                    "value": ch["word_count"],
                })
        else:
            raise ValueError(f"Unknown data_type: {data_type}")

        with open(output_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=["metric", "value"])
            writer.writeheader()
            writer.writerows(rows)

        return rows


# ──────────────────────────────────────────────
# Convenience
# ──────────────────────────────────────────────

def run_full_analysis(db: Database, output: str | None = None) -> str:
    """Run the full analytics pipeline and return the report string.

    If *output* is given, the report is also written to that file.
    """
    generator = ReportGenerator(db)
    report_dict = generator.generate_text_report()
    report = report_dict["report"]
    if output:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(report)
    return report
