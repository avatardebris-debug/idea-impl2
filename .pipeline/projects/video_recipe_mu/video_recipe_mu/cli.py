#!/usr/bin/env python3
"""CLI for video_recipe_mu — extract robot recipes from video_scribe output."""

import argparse
import json
import sys
from pathlib import Path
from typing import List

from video_recipe_mu.recipe_extractor import extract_recipe
from video_recipe_mu.recipe_validator import validate_steps, normalize_steps
from video_recipe_mu.schema import RobotRecipeStep


def main():
    parser = argparse.ArgumentParser(
        description="Extract robot recipes from video_scribe scene descriptions."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to video_scribe JSON or Markdown file.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output path for recipe JSON. Defaults to stdout.",
    )
    parser.add_argument(
        "--provider", "-p",
        default="openai",
        choices=["openai", "anthropic"],
        help="LLM provider to use (default: openai).",
    )
    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Validate recipe steps and report errors.",
    )
    parser.add_argument(
        "--normalize", "-n",
        action="store_true",
        help="Normalize recipe steps before output.",
    )

    args = parser.parse_args()

    # Extract recipe
    try:
        steps: List[RobotRecipeStep] = extract_recipe(args.input, provider=args.provider)
    except Exception as e:
        print(f"Error extracting recipe: {e}", file=sys.stderr)
        sys.exit(1)

    # Validate if requested
    if args.validate:
        errors = validate_steps(steps)
        if errors:
            print("Validation errors:", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            sys.exit(1)
        else:
            print("Recipe validation passed.", file=sys.stderr)

    # Normalize if requested
    if args.normalize:
        steps = normalize_steps(steps)

    # Output
    output_data = [dict(step) for step in steps]

    output_json = json.dumps(output_data, indent=2)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            f.write(output_json)
        print(f"Recipe written to {args.output}", file=sys.stderr)
    else:
        print(output_json)


if __name__ == "__main__":
    main()
