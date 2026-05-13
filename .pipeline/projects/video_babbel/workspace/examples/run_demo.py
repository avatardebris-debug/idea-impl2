#!/usr/bin/env python3
"""Demo script — run the full VideoBabbel pipeline on a sample video.

Usage:
    python examples/run_demo.py --video path/to/video.mp4 [--lang es]

This script demonstrates the end-to-end pipeline:
    ingest → transcribe → translate → summarize → Q&A
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the workspace root is on sys.path so video_babbel is importable.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from video_babbel.pipeline import VideoBabbel  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="VideoBabbel demo pipeline")
    parser.add_argument(
        "--video",
        type=str,
        required=True,
        help="Path to a video file to process.",
    )
    parser.add_argument(
        "--lang",
        type=str,
        default="es",
        help="Target language code (default: es).",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="base",
        help="Whisper model size (default: base).",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  VideoBabbel — Video Translation Pipeline Demo")
    print("=" * 60)
    print(f"  Video : {args.video}")
    print(f"  Lang  : {args.lang}")
    print(f"  Model : {args.model}")
    print("=" * 60)

    pipeline = VideoBabbel(target_lang=args.lang, whisper_model=args.model)

    try:
        result = pipeline.process(args.video)
    except FileNotFoundError as exc:
        print(f"\n[ERROR] {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR] Pipeline failed: {exc}")
        sys.exit(1)

    print("\n--- Results ---")
    print(f"\n[Transcript]\n{result['transcript'][:500]}")
    print(f"\n[Translated ({args.lang})]\n{result['translated_transcript'][:500]}")
    print(f"\n[Summary]\n{result['summary']}")
    print(f"\n[Q&A]\nQ: What is the main topic?\nA: {result['qa']}")
    print("\n" + "=" * 60)
    print("  Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
