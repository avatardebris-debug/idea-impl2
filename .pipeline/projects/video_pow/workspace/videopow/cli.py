"""CLI — Command-line entry point for VideoPow."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from videopow.pipeline import generate_video


def main(argv: Optional[list[str]] = None) -> int:
    """Main CLI entry point.

    Usage:
        python -m videopow --description "slow zoom on a forest" --input sample.mp4 --output result.mp4
    """
    parser = argparse.ArgumentParser(
        prog="videopow",
        description="Convert text descriptions of video edits into actual video transformations.",
    )
    parser.add_argument(
        "--description", "-d",
        required=True,
        help="Text description of the desired video edit.",
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the input video file.",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Path to the output video file (auto-generated if not specified).",
    )
    parser.add_argument(
        "--overlay-text",
        default=None,
        help="Text to overlay on the video.",
    )
    parser.add_argument(
        "--overlay-position",
        default=None,
        choices=["top_left", "top_right", "bottom_left", "bottom_right", "center", "top", "bottom", "left", "right"],
        help="Position of the text overlay.",
    )
    parser.add_argument(
        "--fps",
        default=None,
        type=float,
        help="Output video frame rate.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse the description and show instructions without processing.",
    )

    args = parser.parse_args(argv)

    if args.dry_run:
        from videopow.describer import VideoDescriber
        instructions = VideoDescriber.parse(args.description)
        print("Parsed instructions:")
        print(f"  Effect: {instructions.effect}")
        print(f"  Grayscale: {instructions.grayscale}")
        print(f"  Sepia: {instructions.sepia}")
        print(f"  Blur: {instructions.blur_amount}")
        print(f"  Brightness: {instructions.brightness}")
        print(f"  Contrast: {instructions.contrast}")
        print(f"  Rotation: {instructions.rotation}")
        print(f"  Crop: {instructions.crop}")
        print(f"  Zoom: {instructions.zoom_amount}")
        print(f"  Speed: {instructions.speed_multiplier}")
        print(f"  Duration: {instructions.duration}")
        print(f"  Overlay text: {instructions.overlay_text}")
        print(f"  Overlay position: {instructions.overlay_position}")
        return 0

    try:
        result = generate_video(
            description=args.description,
            input_video_path=args.input,
            output_path=args.output,
            overlay_text=args.overlay_text,
            overlay_position=args.overlay_position,
            fps=args.fps,
        )
        print(f"Video generated successfully!")
        print(f"  Output: {result['output_path']}")
        print(f"  Frames: {result['frames_processed']}")
        print(f"  Duration: {result['duration_seconds']:.2f}s")
        print(f"  Resolution: {result['width']}x{result['height']}")
        print(f"  FPS: {result['fps']:.1f}")
        print(f"  Effect: {result['effect_applied']}")
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
