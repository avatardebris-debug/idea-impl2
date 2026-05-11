"""CLI entry point for the Audiobook Script Pipeline."""

import argparse
import json
import sys
import os

from audiobook_script_pipeline import __version__
from audiobook_script_pipeline.pipeline.script_pipeline import ScriptPipeline
from audiobook_script_pipeline.parser.manuscript_parser import ManuscriptParseError


def main():
    """CLI entry point — accepts a manuscript file path and runs the pipeline."""
    parser = argparse.ArgumentParser(
        description="Convert a manuscript text file into a formatted audio script with pacing markers."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show the package version and exit.",
    )
    parser.add_argument(
        "manuscript",
        help="Path to the manuscript text file.",
    )
    parser.add_argument(
        "-o", "--output",
        help="Optional output file path. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format: 'text' (default) for formatted script, 'json' for structured JSON.",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=1.0,
        help="Default pause duration in seconds (default: 1.0).",
    )
    parser.add_argument(
        "--config",
        help="Path to a JSON config file with pause/emphasis settings.",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.manuscript):
        print(f"Error: File not found: {args.manuscript}", file=sys.stderr)
        sys.exit(1)

    # Load config if provided
    config = {}
    if args.config:
        if not os.path.isfile(args.config):
            print(f"Error: Config file not found: {args.config}", file=sys.stderr)
            sys.exit(1)
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)

    # Merge config values with CLI args (CLI args take precedence)
    default_pause = args.pause
    if "default_pause" in config and "default_pause" not in vars(args):
        default_pause = config["default_pause"]

    pipeline = ScriptPipeline(default_pause=default_pause)

    # Apply config emphasis settings if present
    if "emphasis" in config:
        pipeline.formatter.emphasis_markers = config["emphasis"]

    try:
        audio_script = pipeline.run(args.manuscript)
    except ManuscriptParseError as e:
        print(f"Error: Manuscript is empty: {args.manuscript}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: File not found: {args.manuscript}", file=sys.stderr)
        sys.exit(1)

    if args.format == "json":
        output = json.dumps(audio_script, indent=2, ensure_ascii=False)
    else:
        output = pipeline.formatter.format_to_string(audio_script)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Audio script written to: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
