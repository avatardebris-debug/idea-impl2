"""CLI entry point for video_recipe."""

import argparse
import sys
import os
import tempfile
from pathlib import Path

from video_recipe.input_handler import handle_input, VideoInputError
from video_recipe.extractor import extract_frames_and_transcript, ExtractionError
from video_recipe.llm_client import generate_recipe, LLMClientError
from video_recipe.enricher import enrich_recipe, EnrichmentError
from video_recipe.formatter import render_recipe


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = argparse.ArgumentParser(description="Generate recipes from cooking videos.")
    parser.add_argument("--input", required=True, help="Path to video file or YouTube URL")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration to process in seconds")
    parser.add_argument("--enrich", action="store_true", default=False, help="Enrich recipe with ingredients, equipment, difficulty, estimated time, and key takeaways")
    args = parser.parse_args(argv)

    try:
        # Step 1: Handle input
        video_path = handle_input(args.input)

        # Step 2: Extract frames and transcript
        output_dir = Path(tempfile.gettempdir()) / "video_recipe_frames"
        output_dir.mkdir(parents=True, exist_ok=True)
        frames, transcript = extract_frames_and_transcript(video_path, output_dir, duration=args.duration)

        # Step 3: Generate recipe
        recipe = generate_recipe(frames, transcript)

        # Step 4: Enrich recipe (optional)
        if args.enrich:
            enriched_recipe = enrich_recipe(recipe, frames, transcript)
            output = render_recipe(enriched_recipe, args.format)
        else:
            output = render_recipe(recipe, args.format)

        # Step 5: Write output
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
        else:
            print(output)

        return 0

    except VideoInputError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ExtractionError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except LLMClientError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 3
    except EnrichmentError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 4
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    sys.exit(main())
