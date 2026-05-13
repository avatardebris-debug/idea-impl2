"""CLI entry point for video_langfake.

Provides subcommands for video translation, language detection, video info,
and API server management.

Usage:
    video_langfake translate input.mp4 es output.mp4
    video_langfake detect-language input.mp4
    video_langfake info input.mp4
    video_langfake api          # starts the REST API server
"""

import argparse
import sys
import json
import os
import logging

from video_langfake.pipeline import VideoLangFake
from video_langfake.translate import SUPPORTED_LANGUAGES, LANG_NAMES
from video_langfake.exceptions import PipelineError, VideoLangFakeError


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------

def cmd_translate(args):
    """Run the video translation pipeline."""
    logger = logging.getLogger("video_langfake.cli")

    # Validate language
    if args.target_language not in SUPPORTED_LANGUAGES:
        print(
            f"Error: Unsupported target language '{args.target_language}'.\n"
            f"Supported languages: {', '.join(sorted(SUPPORTED_LANGUAGES))}",
            file=sys.stderr,
        )
        sys.exit(1)

    # Validate input
    if not os.path.exists(args.input):
        print(f"Error: Input video not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Run pipeline with progress output
    print(f"Translating video to {LANG_NAMES.get(args.target_language, args.target_language)}...")
    print(f"  Input:  {args.input}")
    print(f"  Output: {args.output}")
    if args.source_language:
        print(f"  Source: {LANG_NAMES.get(args.source_language, args.source_language)}")
    else:
        print("  Source: auto-detect")

    if args.dry_run:
        print("\n[Dry run] Skipping actual processing.")
        return

    try:
        pipeline = VideoLangFake()
        try:
            pipeline.process(
                video_path=args.input,
                target_language=args.target_language,
                output_path=args.output,
                source_language=args.source_language,
            )
        finally:
            pipeline.cleanup()

        if args.json_output:
            print(json.dumps({
                "status": "success",
                "output": args.output,
                "target_language": args.target_language,
            }, indent=2))
        else:
            print(f"\nTranslation complete! Output saved to: {args.output}")

    except PipelineError as e:
        print(f"\nError: Pipeline failed at step '{e.step}': {e.message}", file=sys.stderr)
        sys.exit(1)
    except VideoLangFakeError as e:
        print(f"\nError: {e.message}", file=sys.stderr)
        sys.exit(1)


def cmd_detect_language(args):
    """Detect the language of a video's audio track."""
    from video_langfake.audio import detect_language

    if not os.path.exists(args.input):
        print(f"Error: Input video not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        result = detect_language(args.input)
        if args.json_output:
            print(json.dumps(result, indent=2))
        else:
            print(f"Detected language: {result.get('language', 'unknown')} "
                  f"({result.get('confidence', 0):.2%} confidence)")
    except VideoLangFakeError as e:
        print(f"Error: {e.message}", file=sys.stderr)
        sys.exit(1)


def cmd_info(args):
    """Show video file information."""
    from moviepy.editor import VideoFileClip

    if not os.path.exists(args.input):
        print(f"Error: Input video not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    try:
        clip = VideoFileClip(args.input)
        info = {
            "filename": args.input,
            "duration": clip.duration,
            "fps": clip.fps,
            "size": clip.size,
            "n_frames": clip.n_frames,
            "audio": clip.audio is not None,
            "audio_duration": clip.audio.duration if clip.audio else None,
        }
        clip.close()

        if args.json_output:
            print(json.dumps(info, indent=2))
        else:
            print(f"Video Info:")
            print(f"  Duration:   {info['duration']:.2f}s")
            print(f"  FPS:        {info['fps']}")
            print(f"  Resolution: {info['size'][0]}x{info['size'][1]}")
            print(f"  Frames:     {info['n_frames']}")
            print(f"  Has Audio:  {info['audio']}")
            if info['audio_duration']:
                print(f"  Audio Dur:  {info['audio_duration']:.2f}s")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_api(args):
    """Start the REST API server."""
    from video_langfake.api import main
    main()


def cmd_languages(args):
    """List supported languages."""
    if args.json_output:
        lang_list = [{"code": k, "name": v} for k, v in LANG_NAMES.items()]
        print(json.dumps({"languages": lang_list, "count": len(lang_list)}, indent=2))
    else:
        print("Supported Languages:")
        for code, name in sorted(LANG_NAMES.items()):
            print(f"  {code:4s} - {name}")
        print(f"\nTotal: {len(LANG_NAMES)} languages")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="video_langfake",
        description="Video Language Fake - Translate videos to different languages with lip-sync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s translate input.mp4 es output.mp4
  %(prog)s translate input.mp4 fr output.mp4 --source-language en
  %(prog)s detect-language input.mp4
  %(prog)s info input.mp4
  %(prog)s api
  %(prog)s languages
        """,
    )
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--config", type=str, help="Path to config file (YAML)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # translate
    translate_parser = subparsers.add_parser(
        "translate",
        help="Translate a video to a target language",
    )
    translate_parser.add_argument("input", help="Input video file path")
    translate_parser.add_argument("target_language", help="Target language code (e.g. es, fr)")
    translate_parser.add_argument("output", help="Output video file path")
    translate_parser.add_argument("--source-language", "-s", type=str, default=None,
                                  help="Source language code (auto-detect if not specified)")
    translate_parser.add_argument("--dry-run", action="store_true",
                                  help="Validate inputs without processing")
    translate_parser.add_argument("--json-output", action="store_true",
                                  help="Output results as JSON")

    # detect-language
    detect_parser = subparsers.add_parser(
        "detect-language",
        help="Detect the language of a video's audio track",
    )
    detect_parser.add_argument("input", help="Input video file path")
    detect_parser.add_argument("--json-output", action="store_true",
                               help="Output results as JSON")

    # info
    info_parser = subparsers.add_parser(
        "info",
        help="Show video file information",
    )
    info_parser.add_argument("input", help="Input video file path")
    info_parser.add_argument("--json-output", action="store_true",
                             help="Output results as JSON")

    # api
    subparsers.add_parser("api", help="Start the REST API server")

    # languages
    lang_parser = subparsers.add_parser(
        "languages",
        help="List supported languages",
    )
    lang_parser.add_argument("--json-output", action="store_true",
                             help="Output results as JSON")

    return parser


# ---------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------------

def main():
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Dispatch to subcommand
    commands = {
        "translate": cmd_translate,
        "detect-language": cmd_detect_language,
        "info": cmd_info,
        "api": cmd_api,
        "languages": cmd_languages,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
