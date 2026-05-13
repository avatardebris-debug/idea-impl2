"""CLI entry point for Video Scribe.

Usage:
    python video_scribe.py input.mp4 --output description.md
    python video_scribe.py input.mp4 --output description.json --format json
    python video_scribe.py input.mp4 --threshold 20 --min-scene-duration 3 --max-workers 8

Phase 2: Multi-scene analysis with parallel VLM processing,
cross-scene context enrichment, and structured output formatting.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from video_scribe.config import (
    DEFAULT_PROVIDER,
    PROVIDER_CLAUDE,
    PROVIDER_GPT4O,
    DEFAULT_SCENE_THRESHOLD,
    DEFAULT_MIN_SCENE_DURATION,
    DEFAULT_MAX_WORKERS,
    get_api_key,
    load_env,
)
from video_scribe.scene_segmenter import detect_scenes
from video_scribe.frame_extractor import extract_multi_frames
from video_scribe.vlm_analyzer import analyze_scenes_parallel
from video_scribe.context_enricher import enrich_scenes
from video_scribe.output_formatter import (
    format_multi_scene_markdown,
    format_multi_scene_json,
    ProgressIndicator,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="video_scribe",
        description="Translate videos into rich, structured scene descriptions.",
    )
    parser.add_argument(
        "input",
        type=str,
        help="Path to the input video file (mp4, mov, avi, etc.).",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Path to the output file (markdown or json). If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=DEFAULT_PROVIDER,
        choices=[PROVIDER_GPT4O, PROVIDER_CLAUDE],
        help="VLM provider to use (default: gpt-4o).",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API key for the VLM provider. Overrides the environment variable.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_SCENE_THRESHOLD,
        help=f"Scene detection sensitivity (0-100, higher = fewer scenes). Default: {DEFAULT_SCENE_THRESHOLD}",
    )
    parser.add_argument(
        "--min-scene-duration",
        type=float,
        default=DEFAULT_MIN_SCENE_DURATION,
        help=f"Minimum scene duration in seconds. Default: {DEFAULT_MIN_SCENE_DURATION}",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=DEFAULT_MAX_WORKERS,
        help=f"Maximum number of parallel VLM workers. Default: {DEFAULT_MAX_WORKERS}",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="md",
        choices=["md", "json"],
        help="Output format: 'md' for markdown (default) or 'json' for JSON.",
    )
    return parser


def run(
    input_path: str,
    output_path: Optional[str],
    provider: str,
    api_key: Optional[str],
    threshold: float = DEFAULT_SCENE_THRESHOLD,
    min_scene_duration: float = DEFAULT_MIN_SCENE_DURATION,
    max_workers: int = DEFAULT_MAX_WORKERS,
    output_format: str = "md",
) -> None:
    """Run the full Video Scribe pipeline (Phase 2: multi-scene)."""
    # Load .env if present
    load_env()

    # Resolve API key
    key = api_key or get_api_key(provider)

    # Validate input file
    video_path = Path(input_path)
    if not video_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Step 1: Detect scenes
    print(f"Detecting scenes in {input_path} ...", file=sys.stderr)
    scenes = detect_scenes(
        str(video_path),
        threshold=threshold,
        min_scene_duration=min_scene_duration,
    )
    print(f"Found {len(scenes)} scene(s).", file=sys.stderr)

    if not scenes:
        print("No scenes detected. Exiting.", file=sys.stderr)
        sys.exit(1)

    # Step 2: Extract multi-frames per scene
    print("Extracting key frames per scene ...", file=sys.stderr)
    scenes_frames = extract_multi_frames(str(video_path), scenes)
    total_frames = sum(len(f) for f in scenes_frames)
    print(f"Extracted {total_frames} frame(s) across {len(scenes_frames)} scene(s).", file=sys.stderr)

    # Step 3: Parallel VLM analysis
    print(f"Analyzing scenes with {provider} (max_workers={max_workers}) ...", file=sys.stderr)
    progress = ProgressIndicator(len(scenes_frames), label="Analyzing")
    scene_analyses = analyze_scenes_parallel(
        scenes_frames,
        provider=provider,
        api_key=key,
        max_workers=max_workers,
    )
    progress.finish()

    # Step 4: Enrich with cross-scene context
    print("Enriching with cross-scene context ...", file=sys.stderr)
    enriched = enrich_scenes(scene_analyses, provider=provider, api_key=key)

    # Add timing info to each scene
    for i, (scene, analysis) in enumerate(zip(scenes, enriched)):
        start_frame, end_frame, start_time, end_time = scene
        analysis["start_frame"] = start_frame
        analysis["end_frame"] = end_frame
        analysis["start_time"] = start_time
        analysis["end_time"] = end_time

    # Calculate total duration
    total_duration = scenes[-1][3] if scenes else 0.0

    # Step 5: Format output
    if output_format == "json":
        output_text = format_multi_scene_json(enriched, title="Video Analysis", duration=total_duration)
    else:
        output_text = format_multi_scene_markdown(enriched, title="Video Analysis", duration=total_duration)

    # Step 6: Write output
    if output_path:
        out = Path(output_path)
        out.write_text(output_text, encoding="utf-8")
        print(f"Output written to {output_path}", file=sys.stderr)
    else:
        print(output_text)


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()
    run(
        args.input,
        args.output,
        args.provider,
        args.api_key,
        threshold=args.threshold,
        min_scene_duration=args.min_scene_duration,
        max_workers=args.max_workers,
        output_format=args.format,
    )


if __name__ == "__main__":
    main()
