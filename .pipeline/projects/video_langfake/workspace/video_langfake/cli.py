"""CLI entry point for video_langfake."""

import argparse
import sys
from video_langfake.pipeline import VideoLangFake


def main():
    parser = argparse.ArgumentParser(
        description="Translate a video to any language with lip-sync."
    )
    parser.add_argument("input", help="Path to input video file")
    parser.add_argument("target_language", help="Target language code (e.g. es, fr, de)")
    parser.add_argument("output", help="Path to output video file")
    parser.add_argument(
        "--source-language",
        default=None,
        help="Source language code (auto-detected if not provided)",
    )
    args = parser.parse_args()

    pipeline = VideoLangFake()
    pipeline.process(
        video_path=args.input,
        target_language=args.target_language,
        output_path=args.output,
        source_language=args.source_language,
    )
    print(f"Done. Output written to {args.output}")


if __name__ == "__main__":
    main()
