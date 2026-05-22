"""CLI entry point for the beatsheet_generator."""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from beatsheet_generator.service import BeatSheetService


def _format_beat_sheet_text(beat_sheet_data: dict, title: str, genre: str) -> str:
    """Format a beat sheet dict as human-readable text."""
    lines: List[str] = []
    lines.append(f"🎬 {title}")
    lines.append(f"   Genre: {genre}")
    lines.append(f"   Logline: {beat_sheet_data.get('logline', 'N/A')}")
    lines.append("")
    lines.append("   " + "─" * 60)

    beats = beat_sheet_data.get("beats", [])
    for beat in beats:
        phase = beat.get("phase", "unknown")
        phase_emoji = {"setup": "🟢", "confrontation": "🟡", "resolution": "🔴"}.get(phase, "⚪")
        lines.append(
            f"   {phase_emoji} Beat {beat.get('beat_number', '?'):>2}: {beat.get('beat_name', 'Unknown')}"
        )
        lines.append(f"      Summary: {beat.get('summary', 'N/A')}")
        chars = beat.get("characters_involved", [])
        if chars:
            lines.append(f"      Characters: {', '.join(chars)}")
        lines.append("")

    lines.append("   " + "─" * 60)
    lines.append(f"   Total beats: {len(beats)}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a Save-the-Cat 15-beat sheet for a movie.",
    )
    parser.add_argument("--title", type=str, default="Untitled", help="Movie title.")
    parser.add_argument("--genre", type=str, default="", help="Movie genre.")
    parser.add_argument("--logline", type=str, default="", help="Movie logline.")
    parser.add_argument("--tone", type=str, default="", help="Tone (e.g. dark, whimsical).")
    parser.add_argument(
        "--output", "-o", type=str, default=None, help="Output file path (JSON).",
    )
    parser.add_argument(
        "--format", "-f", type=str, choices=["text", "json"], default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--source-movie-idea", type=str, default=None,
        help="Path to a JSON file from movie_idea_generator.",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducibility (passed to movie_idea_generator).",
    )
    parser.add_argument(
        "--count", type=int, default=1,
        help="Number of ideas to generate (via movie_idea_generator), then pick one.",
    )
    args = parser.parse_args(argv)

    # Load idea from movie_idea_generator output or generate one
    if args.source_movie_idea:
        service = BeatSheetService.from_json_file(args.source_movie_idea)
    else:
        # If no logline provided at all, generate one via movie_idea_generator
        if args.logline is None:
            try:
                from movie_idea_generator.generator import MovieIdeaGenerator

                generator = MovieIdeaGenerator(seed=args.seed)
                ideas = generator.generate_batch(count=args.count)
                if not ideas:
                    print("Error: No ideas generated.", file=sys.stderr)
                    sys.exit(1)
                # Use the first idea (or last if count > 1)
                idea = ideas[-1]
                service = BeatSheetService.from_idea_dict(idea)
                service.tone = args.tone
            except ImportError:
                print(
                    "Error: movie_idea_generator not installed. "
                    "Provide --logline and --genre directly.",
                    file=sys.stderr,
                )
                sys.exit(1)
        else:
            service = BeatSheetService(
                title=args.title,
                genre=args.genre,
                logline=args.logline,
                tone=args.tone,
            )

    # Generate beat sheet
    try:
        result = service.generate()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    if args.format == "json":
        print(result["beat_sheet_json"])
    else:
        print(_format_beat_sheet_text(result["beat_sheet_dict"], result["title"], result["genre"]))

    # Save to file if requested
    if args.output:
        path = service.save_to_file(args.output)
        print(f"\n💾 Saved to {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
