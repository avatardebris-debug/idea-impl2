"""CLI entry point for the Movie Idea Generator."""

import argparse
import json
import sys

from movie_idea_generator.generator import MovieIdeaGenerator


def _format_idea(idea: dict, fmt: str = "text") -> str:
    """Format a single movie idea for output."""
    if fmt == "json":
        return json.dumps(idea, indent=2)

    lines = [
        f"🎬 {idea['title']}",
        f"   Genre: {idea['genre']}",
        f"   Logline: {idea['logline']}",
        "   Characters:",
    ]
    for ch in idea["characters"]:
        lines.append(f"     • {ch['name']} ({ch['role']}) — {ch['description']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate creative movie ideas.",
    )
    parser.add_argument(
        "-g", "--genre",
        type=str,
        default=None,
        help="Filter by genre (e.g. Action, Comedy, Drama, Horror, Sci-Fi, Romance, Thriller, Fantasy, Mystery, Adventure).",
    )
    parser.add_argument(
        "-n", "--count",
        type=int,
        default=1,
        help="Number of ideas to generate (default: 1).",
    )
    parser.add_argument(
        "-f", "--format",
        type=str,
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility.",
    )
    args = parser.parse_args(argv)

    generator = MovieIdeaGenerator(seed=args.seed)
    ideas = generator.generate_batch(count=args.count, genre=args.genre)

    if args.format == "json":
        if args.count == 1:
            print(json.dumps(ideas[0], indent=2))
        else:
            print(json.dumps(ideas, indent=2))
    else:
        for i, idea in enumerate(ideas):
            if i > 0:
                print()
            print(_format_idea(idea, "text"))


if __name__ == "__main__":
    main()
