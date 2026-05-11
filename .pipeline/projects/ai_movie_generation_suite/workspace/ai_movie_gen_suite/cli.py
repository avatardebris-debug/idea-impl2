#!/usr/bin/env python3
"""CLI entry point for AI Movie Gen Suite.

Usage:
    python -m ai_movie_gen_suite.cli --title "My Movie" --logline "A story" --genre "Drama"
    python -m ai_movie_gen_suite.cli --help
"""

from __future__ import annotations

import argparse
import logging
import sys

from ai_movie_gen_suite.pipeline.orchestrator import MovieGenerationPipeline, PipelineConfig


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Movie Gen Suite — Generate screenplays with AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a drama screenplay
  python -m ai_movie_gen_suite.cli --title "The Last Light" --logline "A lighthouse keeper discovers a secret" --genre "Drama"

  # Generate with LLM (requires LLM_API_KEY)
  python -m ai_movie_gen_suite.cli --title "Space Odyssey" --logline "A journey to the stars" --genre "Sci-Fi" --use-llm

  # Output as FDX (Final Draft)
  python -m ai_movie_gen_suite.cli --title "Action Hero" --logline "A hero saves the day" --genre "Action" --output-format fdx
        """,
    )

    parser.add_argument("--title", type=str, required=True, help="Title of the screenplay")
    parser.add_argument("--logline", type=str, required=True, help="One-sentence logline of the story")
    parser.add_argument("--genre", type=str, default="Drama", help="Genre (default: Drama)")
    parser.add_argument("--tone", type=str, default="", help="Tone (e.g., 'dark', 'hopeful', 'comedic')")
    parser.add_argument("--output-format", type=str, default="json", choices=["json", "yaml", "fdx"], help="Output format (default: json)")
    parser.add_argument("--output-dir", type=str, default="./output", help="Output directory (default: ./output)")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM for richer content")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # Create pipeline config
    config = PipelineConfig(
        logline=args.logline,
        title=args.title,
        genre=args.genre,
        tone=args.tone,
        output_format=args.output_format,
        output_dir=args.output_dir,
        use_llm=args.use_llm,
    )

    # Run pipeline
    pipeline = MovieGenerationPipeline(config)
    results = pipeline.run()

    print(f"\n✅ Pipeline complete!")
    print(f"   Title: {config.title}")
    print(f"   Genre: {config.genre}")
    print(f"   Output: {results.get('output_path', 'N/A')}")
    print(f"   Scenes: {len(pipeline.script.scenes) if pipeline.script else 0}")
    print(f"   Characters: {len(pipeline.character_registry.characters) if pipeline.character_registry else 0}")
    print(f"   Beats: {len(pipeline.beat_sheet.beats) if pipeline.beat_sheet else 0}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
