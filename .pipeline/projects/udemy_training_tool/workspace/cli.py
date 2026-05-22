"""CLI interface for Udemy Training Tool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from udemy_training_tool import __version__
from udemy_training_tool.models import Course
from udemy_training_tool.search import search_courses
from udemy_training_tool.recommender import recommend_courses, compare_courses


def _load_courses(file_path: Optional[str]) -> List[Course]:
    """Load courses from a JSON or JSONL file, or stdin."""
    if file_path is None:
        # Read from stdin
        data = sys.stdin.read()
        return _parse_courses(data)

    path = Path(file_path)
    if not path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        sys.exit(1)

    data = path.read_text(encoding="utf-8")
    return _parse_courses(data)


def _parse_courses(data: str) -> List[Course]:
    """Parse JSON or JSONL data into a list of Course objects."""
    data = data.strip()
    if not data:
        return []

    # Try JSON array first
    try:
        parsed = json.loads(data)
        if isinstance(parsed, list):
            return [Course.from_dict(c) for c in parsed]
        elif isinstance(parsed, dict):
            return [Course.from_dict(parsed)]
    except json.JSONDecodeError:
        pass

    # Try JSONL (one JSON object per line)
    courses = []
    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                courses.append(Course.from_dict(obj))
        except json.JSONDecodeError:
            continue

    return courses


def _format_text_courses(courses: List[Course]) -> str:
    """Format a list of courses as text."""
    if not courses:
        return "No courses found."
    lines = []
    for i, c in enumerate(courses, 1):
        lines.append(f"{i}. {c.title}")
        lines.append(f"   Instructor: {c.instructor}")
        lines.append(f"   Rating: {c.rating}/5 | Students: {c.num_students:,} | Price: ${c.price:.2f}")
        lines.append(f"   Level: {c.level} | Category: {c.category}")
        lines.append(f"   Lectures: {c.num_lectures} | Duration: {c.duration}")
        if c.tags:
            lines.append(f"   Tags: {', '.join(c.tags)}")
        lines.append("")
    return "\n".join(lines)


def _format_text_recommendations(recommendations: List[dict]) -> str:
    """Format recommendations as text."""
    if not recommendations:
        return "No recommendations found."
    lines = ["Top Course Recommendations:"]
    lines.append("=" * 60)
    for i, rec in enumerate(recommendations, 1):
        c = rec["course"]
        lines.append(f"\n{i}. {c.title} (Score: {rec['score']:.1f}/100)")
        lines.append(f"   Instructor: {c.instructor}")
        lines.append(f"   Rating: {c.rating}/5 | Students: {c.num_students:,} | Price: ${c.price:.2f}")
        lines.append(f"   Level: {c.level} | Category: {c.category}")
        lines.append(f"   Lectures: {c.num_lectures} | Duration: {c.duration}")
        bd = rec["breakdown"]
        lines.append(f"   Score Breakdown:")
        lines.append(f"     Rating: {bd['rating']:.1f} | Students: {bd['students']:.1f} | "
                      f"Price: {bd['price_value']:.1f} | Depth: {bd['depth']:.1f} | "
                      f"Instructor: {bd['instructor']:.1f}")
    return "\n".join(lines)


def _format_text_comparison(comparisons: List[dict]) -> str:
    """Format course comparison as text."""
    if not comparisons:
        return "No courses to compare."
    lines = ["Course Comparison:"]
    lines.append("=" * 60)
    for rec in comparisons:
        c = rec["course"]
        bd = rec["breakdown"]
        lines.append(f"\n{c.title}")
        lines.append(f"   Score: {rec['score']:.1f}/100")
        lines.append(f"   Instructor: {c.instructor} | Rating: {c.rating}/5")
        lines.append(f"   Students: {c.num_students:,} | Price: ${c.price:.2f}")
        lines.append(f"   Lectures: {c.num_lectures} | Duration: {c.duration}")
        lines.append(f"   Breakdown: Rating={bd['rating']:.1f} Students={bd['students']:.1f} "
                      f"Price={bd['price_value']:.1f} Depth={bd['depth']:.1f} "
                      f"Instructor={bd['instructor']:.1f}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="udemy",
        description="Search, compare, and recommend Udemy courses",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # search subcommand
    search_parser = subparsers.add_parser("search", help="Search courses")
    search_parser.add_argument("file", help="JSON/JSONL file with course data (or - for stdin)")
    search_parser.add_argument("--query", "-q", required=True, help="Search query")
    search_parser.add_argument("--min-rating", type=float, default=0, help="Minimum rating (0-5)")
    search_parser.add_argument("--max-price", type=float, default=None, help="Maximum price")
    search_parser.add_argument("--level", default=None, help="Course level filter")
    search_parser.add_argument("--category", default=None, help="Category filter")
    search_parser.add_argument("--output", "-o", choices=["json", "text"], default="text",
                               help="Output format (default: text)")

    # compare subcommand
    compare_parser = subparsers.add_parser("compare", help="Compare courses")
    compare_parser.add_argument("file", help="JSON/JSONL file with course data")
    compare_parser.add_argument("--ids", nargs="+", type=int, help="Course IDs (1-based indices) to compare")
    compare_parser.add_argument("--skill", default="", help="Target skill for relevance scoring")
    compare_parser.add_argument("--output", "-o", choices=["json", "text"], default="text",
                                help="Output format (default: text)")

    # recommend subcommand
    recommend_parser = subparsers.add_parser("recommend", help="Get course recommendations")
    recommend_parser.add_argument("file", help="JSON/JSONL file with course data")
    recommend_parser.add_argument("--skill", "-s", required=True, help="Target skill/topic")
    recommend_parser.add_argument("--top-n", type=int, default=5, help="Number of recommendations (default: 5)")
    recommend_parser.add_argument("--output", "-o", choices=["json", "text"], default="text",
                                  help="Output format (default: text)")

    return parser


def cli(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point. Returns exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 1

    try:
        courses = _load_courses(args.file)
    except Exception as e:
        print(f"Error loading courses: {e}", file=sys.stderr)
        return 1

    if args.command == "search":
        results = search_courses(
            courses,
            query=args.query,
            min_rating=args.min_rating,
            max_price=args.max_price,
            level=args.level,
            category=args.category,
        )
        if args.output == "json":
            print(json.dumps([c.to_dict() for c in results], indent=2))
        else:
            print(_format_text_courses(results))

    elif args.command == "compare":
        if args.ids:
            # Filter to specific courses by index
            selected = [courses[i - 1] for i in args.ids if 0 < i <= len(courses)]
            if not selected:
                print("Error: No valid course IDs.", file=sys.stderr)
                return 1
            results = compare_courses(selected, args.skill)
        else:
            results = compare_courses(courses, args.skill)
        if args.output == "json":
            print(json.dumps([{
                "course": r["course"].to_dict(),
                "score": r["score"],
                "breakdown": r["breakdown"],
            } for r in results], indent=2))
        else:
            print(_format_text_comparison(results))

    elif args.command == "recommend":
        results = recommend_courses(courses, args.skill, args.top_n)
        if args.output == "json":
            print(json.dumps([{
                "course": r["course"].to_dict(),
                "score": r["score"],
                "breakdown": r["breakdown"],
            } for r in results], indent=2))
        else:
            print(_format_text_recommendations(results))

    return 0


if __name__ == "__main__":
    sys.exit(cli())
