"""CLI entry point for book_researcher."""

from __future__ import annotations

import argparse
import json
import sys

from book_researcher.pipeline import BookResearcherPipeline


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="book-researcher",
        description="Find underserved book niches by analyzing reviews of top-selling information books",
    )
    parser.add_argument(
        "--book-title",
        type=str,
        default="The Underserved Book",
        help="Title for the generated book (default: 'The Underserved Book')",
    )
    parser.add_argument(
        "--max-chapters",
        type=int,
        default=12,
        help="Maximum number of TOC chapters (default: 12)",
    )
    parser.add_argument(
        "--target-audience",
        type=str,
        default="Practitioners seeking comprehensive coverage",
        help="Target audience description",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    pipeline = BookResearcherPipeline(
        book_title=args.book_title,
        max_chapters=args.max_chapters,
        target_audience=args.target_audience,
    )

    result = pipeline.run()

    if args.json:
        output = _result_to_json(result)
    else:
        output = result.summary()

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Results written to {args.output}", file=sys.stderr)
    else:
        print(output)


def _result_to_json(result) -> str:
    """Convert PipelineResult to JSON string."""
    data = {
        "book_title": result.toc.book_title,
        "target_audience": result.toc.target_audience,
        "reviews_count": len(result.reviews),
        "gaps_count": len(result.gaps),
        "niches_count": len(result.niches),
        "toc": {
            "book_title": result.toc.book_title,
            "total_chapters": result.toc.total_chapters,
            "estimated_total_pages": result.toc.estimated_total_pages,
            "chapters": [
                {
                    "chapter_number": c.chapter_number,
                    "title": c.title,
                    "key_topics": c.key_topics,
                    "priority_score": c.priority_score,
                    "estimated_pages": c.estimated_pages,
                }
                for c in result.toc.chapters
            ],
        },
        "niches": [
            {
                "topic": n.topic,
                "score": n.score,
                "gap_count": n.gap_count,
                "gap_statements": n.gap_statements,
                "avg_rating": n.avg_rating,
            }
            for n in result.niches
        ],
    }
    return json.dumps(data, indent=2)


if __name__ == "__main__":
    main()
