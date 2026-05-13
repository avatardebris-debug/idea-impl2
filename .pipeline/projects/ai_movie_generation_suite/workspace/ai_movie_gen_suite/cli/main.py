"""CLI entry point for AI Movie Generation Suite."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ai_movie_gen_suite.pipeline.orchestrator import MovieGenerationPipeline, PipelineConfig

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="ai-movie-gen",
        description="AI Movie Generation Suite — Generate screenplays with AI",
    )

    parser.add_argument(
        "--title",
        type=str,
        required=True,
        help="Title of the screenplay",
    )
    parser.add_argument(
        "--logline",
        type=str,
        required=True,
        help="One-sentence logline of the story",
    )
    parser.add_argument(
        "--genre",
        type=str,
        default="drama",
        help="Genre of the screenplay (default: drama)",
    )
    parser.add_argument(
        "--tone",
        type=str,
        default="",
        help="Tone of the screenplay (e.g., 'dark', 'hopeful', 'comedic')",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        default="json",
        choices=["json", "yaml", "fdx"],
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Directory to save output files (default: ./output)",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM for generation (requires OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args(argv)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main(argv: list[str] | None = None) -> None:
    """Main entry point."""
    args = parse_args(argv)
    setup_logging(args.verbose)

    logger.info("AI Movie Generation Suite v0.1.0")
    logger.info(f"Title: {args.title}")
    logger.info(f"Logline: {args.logline}")
    logger.info(f"Genre: {args.genre}")
    logger.info(f"Tone: {args.tone or 'Not specified'}")

    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create pipeline config
    config = PipelineConfig(
        logline=args.logline,
        title=args.title,
        genre=args.genre,
        tone=args.tone,
        output_format=args.output_format,
        output_dir=str(output_dir),
        use_llm=args.use_llm,
    )

    # Run pipeline
    pipeline = MovieGenerationPipeline(config)
    results = pipeline.run()

    logger.info("Pipeline complete!")
    logger.info(f"Results: {results}")


if __name__ == "__main__":
    main()
