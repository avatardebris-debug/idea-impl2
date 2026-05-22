"""CLI entry point for the SEO analysis tool."""

from __future__ import annotations

import json
import sys
from typing import Optional

import click

from seo_tool.analyzer import Analyzer, AnalyzerError
from seo_tool.models import SEOReport
from seo_tool.scorer import Scorer


def _format_report(report: SEOReport, score_result: dict) -> str:
    """Format an SEOReport and its score into a human-readable string."""
    total = score_result["total_score"]
    categories = score_result["category_scores"]

    lines: list[str] = []
    lines.append("=" * 60)
    lines.append(f"  SEO Analysis Report for: {report.url}")
    lines.append("=" * 60)
    lines.append("")

    # Overall score
    if report.fetch_error:
        lines.append(f"  ⚠ Fetch Error: {report.fetch_error}")
        lines.append("")
    else:
        score_bar = "█" * (total // 5) + "░" * (20 - total // 5)
        lines.append(f"  Overall Score: [{score_bar}] {total}/100")
        lines.append("")

    # Category breakdown
    lines.append("  Category Breakdown:")
    lines.append("  " + "-" * 40)
    for name in ["title", "meta_description", "h1_count", "canonical",
                  "content_length", "og_tags", "headings", "images", "links"]:
        cat = categories.get(name, {})
        score = cat.get("score", 0)
        max_w = cat.get("max", 0)
        reason = cat.get("reason", "N/A")
        status = "✓" if score == max_w else "✗" if score == 0 else "⚠"
        lines.append(f"    {status} {name.replace('_', ' ').title():<20} {score:>3}/{max_w}")
        lines.append(f"      → {reason}")
    lines.append("")

    # Issues / Warnings
    issues = []
    for name, cat in categories.items():
        score = cat.get("score", 0)
        max_w = cat.get("max", 0)
        if score < max_w:
            issues.append(cat.get("reason", "Issue detected"))
    if issues:
        lines.append("  Issues / Warnings:")
        lines.append("  " + "-" * 40)
        for i, issue in enumerate(issues, 1):
            lines.append(f"    {i}. {issue}")
        lines.append("")

    # Summary stats
    lines.append("  Summary:")
    lines.append("  " + "-" * 40)
    lines.append(f"    Word count:      {report.word_count}")
    lines.append(f"    Total links:     {report.link_count}")
    lines.append(f"    Internal links:  {len(report.internal_links)}")
    lines.append(f"    External links:  {len(report.external_links)}")
    lines.append(f"    Images:          {len(report.images)}")
    lines.append(f"    Headings:        {len(report.headings)}")
    lines.append(f"    OG tags:         {len(report.og_tags)}")
    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def _report_to_dict(report: SEOReport, score_result: dict) -> dict:
    """Convert report + score to a serializable dict."""
    return {
        "url": report.url,
        "fetch_error": report.fetch_error,
        "http_status": report.http_status,
        "total_score": score_result["total_score"],
        "category_scores": {
            name: {
                "score": cat["score"],
                "max": cat["max"],
                "reason": cat["reason"],
            }
            for name, cat in score_result["category_scores"].items()
        },
        "summary": {
            "word_count": report.word_count,
            "link_count": report.link_count,
            "internal_links": len(report.internal_links),
            "external_links": len(report.external_links),
            "images": len(report.images),
            "headings": len(report.headings),
            "og_tags": len(report.og_tags),
        },
    }


@click.command()
@click.argument("url")
@click.option("--json", "as_json", is_flag=True, help="Output in JSON format.")
@click.option("--output", "-o", "output_file", type=click.Path(), help="Write report to file.")
def cli(url: str, as_json: bool, output_file: Optional[str]) -> None:
    """Analyze the SEO of a URL and print a scored report.

    URL is the website to analyze (e.g. https://example.com).
    """
    analyzer = Analyzer()
    scorer = Scorer()

    try:
        report = analyzer.fetch_and_parse(url)
    except AnalyzerError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    score_result = scorer.score(report)

    if as_json:
        output = json.dumps(_report_to_dict(report, score_result), indent=2)
    else:
        output = _format_report(report, score_result)

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output)
        click.echo(f"Report written to {output_file}")
    else:
        click.echo(output)


if __name__ == "__main__":
    cli()
