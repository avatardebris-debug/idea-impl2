"""CLI for the consistent character developer pipeline.

Usage:
    python -m ai_consistent_char.cli --logline "..." --title "..." --genre "..." \
        --generate-scene-renders

Flags:
    --logline          The movie logline.
    --title            The movie title.
    --genre            The movie genre.
    --generate-scene-renders  Enable per-scene character rendering.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ai_movie_gen_suite.models import CharacterRegistry, Script
from ai_movie_gen_suite.pipeline import MovieGenerationPipeline

from ai_consistent_char.image_provider import DummyCharacterImageProvider
from ai_consistent_char.pipeline_extension import PipelineExtension

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Consistent Character Developer CLI")
    parser.add_argument("--logline", type=str, required=True, help="Movie logline")
    parser.add_argument("--title", type=str, required=True, help="Movie title")
    parser.add_argument("--genre", type=str, required=True, help="Movie genre")
    parser.add_argument(
        "--generate-scene-renders",
        action="store_true",
        help="Enable per-scene character rendering",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output",
        help="Output directory for generated assets",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize pipeline
    pipeline = MovieGenerationPipeline(
        logline=args.logline,
        title=args.title,
        genre=args.genre,
    )

    # Add character consistency extension
    provider = DummyCharacterImageProvider()
    extension = PipelineExtension(pipeline)
    extension.add_character_consistency(
        provider=provider,
        output_dir=output_dir,
        generate_renders=args.generate_scene_renders,
    )

    # Run pipeline
    logger.info("Running movie generation pipeline...")
    script: Script = pipeline.run()  # type: ignore[assignment]

    # Get character registry from pipeline state
    registry: CharacterRegistry = pipeline.state.get("character_registry", CharacterRegistry())  # type: ignore[assignment]

    # Run character consistency
    if args.generate_scene_renders:
        logger.info("Running character consistency pipeline...")
        collection = extension.run_character_consistency(script, registry)
        if collection:
            logger.info(
                "Generated %d scene character renders.",
                len(collection.renders),
            )
    else:
        logger.info("Scene rendering disabled. Reference sheets generated only.")

    logger.info("Pipeline complete. Output in %s", output_dir)


if __name__ == "__main__":
    main()
