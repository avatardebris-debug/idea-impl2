"""CLI for see_bs — process articles and print BS reports.

Usage:
    see-bs              Run demo on built-in sample articles
    see-bs --stdin      Read a JSON article from stdin
    see-bs --json FILE  Read a JSON article from a file
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from typing import Optional

from see_bs import filter_news, NewsArticle


def _sample_articles() -> list[NewsArticle]:
    """Return a few built-in sample articles for demo purposes."""
    return [
        NewsArticle(
            title="Everyone Knows the Economy Is Collapsing — No One Disputes It",
            content="The economy is obviously in freefall. No one disputes the facts. "
                    "Markets are crashing, jobs are vanishing, and the numbers are "
                    "undeniable. Critics have no valid counterargument.",
            source="Patriot Daily",
            author="John Hawk",
            date=datetime(2025, 1, 15),
            outlet_bias="right",
            claim_type="factual",
            evidence_level="weak",
            author_track_record="mixed",
            incentives=["ad revenue from outrage clicks"],
        ),
        NewsArticle(
            title="New Study Shows Moderate Benefits of Remote Work",
            content="A peer-reviewed study of 5,000 workers found modest productivity gains "
                    "from remote work. Critics say the sample was skewed, but the core "
                    "findings hold. However, some argue the long-term effects are unclear.",
            source="National Science Review",
            author="Dr. Sarah Chen",
            date=datetime(2025, 3, 1),
            outlet_bias="center",
            claim_type="analysis",
            evidence_level="moderate",
            author_track_record="reliable",
            incentives=[],
        ),
        NewsArticle(
            title="Shocking Truth About Tech Giants — They're All Corrupt!",
            content="It is absolutely certain that every major tech company is corrupt. "
                    "Beyond doubt, they manipulate everything. Obviously, the media won't "
                    "tell you this. Undoubtedly, they are hiding the truth from you.",
            source="TruthWire",
            author="Mike Thunder",
            date=datetime(2025, 2, 20),
            outlet_bias="extreme",
            claim_type="rumor",
            evidence_level="none",
            author_track_record="unreliable",
            incentives=["selling conspiracy course", "donor pressure"],
        ),
    ]


def _article_from_dict(d: dict) -> NewsArticle:
    """Build a NewsArticle from a dict (e.g. parsed from JSON)."""
    date_val = d.get("date")
    if isinstance(date_val, str):
        date_val = datetime.fromisoformat(date_val)
    return NewsArticle(
        title=d["title"],
        content=d["content"],
        source=d["source"],
        author=d["author"],
        date=date_val,
        outlet_bias=d.get("outlet_bias", "unknown"),
        claim_type=d.get("claim_type", "factual"),
        evidence_level=d.get("evidence_level", "unknown"),
        author_track_record=d.get("author_track_record", "unknown"),
        incentives=d.get("incentives", []),
    )


def _process_article(article: NewsArticle) -> None:
    """Analyze and print a single article's BS report."""
    result = filter_news(article)
    print(f"\n{'#' * 60}")
    print(f"  Title:    {article.title}")
    print(f"  Source:   {article.source}")
    print(f"  Author:   {article.author}")
    print(f"{'#' * 60}")
    print(f"  BS Score: {result.bs_score:.1f} / 100")
    print(f"  Verdict:  {result.verdict}")
    print()
    for fb in result.breakdown:
        print(f"  [{fb.name}] score={fb.score:.1f}  —  {fb.explanation}")
    print()


def main(argv: Optional[list[str]] = None) -> None:
    """Entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="see-bs",
        description="News BS detection based on Scott Adams techniques",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--demo", action="store_true", help="Run on built-in sample articles")
    group.add_argument("--stdin", action="store_true", help="Read a JSON article from stdin")
    group.add_argument("--json", dest="json_file", type=str, help="Read a JSON article from a file")
    args = parser.parse_args(argv)

    if args.demo:
        articles = _sample_articles()
        for i, article in enumerate(articles, 1):
            print(f"\n{'=' * 60}")
            print(f"  Demo Article {i}/{len(articles)}")
            print(f"{'=' * 60}")
            _process_article(article)
    elif args.stdin:
        raw = sys.stdin.read()
        if not raw.strip():
            print("Error: no input on stdin", file=sys.stderr)
            sys.exit(1)
        article = _article_from_dict(json.loads(raw))
        _process_article(article)
    elif args.json_file:
        with open(args.json_file, "r") as f:
            article = _article_from_dict(json.load(f))
        _process_article(article)


if __name__ == "__main__":
    main()
