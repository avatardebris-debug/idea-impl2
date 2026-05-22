"""
cli.py — podcast command-line interface.

Usage:
    python -m podcast episode.mp3 --lessons 10 --output lessons.md
    python -m podcast episode.mp3 --prompt "Focus on marketing tactics" --lessons 7
    python -m podcast transcript.txt --text-input --lessons 5 --format json
    python -m podcast episode.mp3 --no-llm --lessons 10   # rule-based fallback
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys
import textwrap
import time


AUDIO_EXTS = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".flac", ".mkv", ".webm", ".aac"}


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="podcast",
        description="Extract lessons from a podcast episode (audio → transcript → LLM → lessons)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python -m podcast episode.mp3 --lessons 10
              python -m podcast episode.mp3 --prompt "Focus on sales tactics" --lessons 7
              python -m podcast transcript.txt --text-input --lessons 5
              python -m podcast episode.mp3 --output notes.md --format markdown
              python -m podcast episode.mp3 --no-llm --lessons 10
        """),
    )
    parser.add_argument("input",        help="Audio/video file or text transcript")
    parser.add_argument("--lessons",    type=int, default=10,
                        help="Number of lessons to extract (default: 10)")
    parser.add_argument("--prompt",     default="",
                        help="Custom focus prompt (e.g. 'business tactics only')")
    parser.add_argument("--model",      default="qwen3:6b",
                        help="Ollama model (default: qwen3:6b)")
    parser.add_argument("--output",     default=None,
                        help="Output file path (.md, .txt, or .json)")
    parser.add_argument("--format",     choices=["markdown", "plain", "json"],
                        default="markdown", help="Output format (default: markdown)")
    parser.add_argument("--text-input", action="store_true",
                        help="Input is already a text transcript, skip transcription")
    parser.add_argument("--no-llm",     action="store_true",
                        help="Skip LLM — use rule-based extraction only")
    parser.add_argument("--lang",       default=None,
                        help="Source language for Whisper (e.g. en, es). Auto-detect if omitted.")
    parser.add_argument("--no-quotes",  action="store_true",
                        help="Omit verbatim quotes from Markdown output")

    args = parser.parse_args()

    inp = pathlib.Path(args.input)
    if not inp.exists():
        print(f"ERROR: file not found: {inp}", file=sys.stderr)
        sys.exit(1)

    episode_name = inp.stem

    print(f"\n{'='*60}", file=sys.stderr)
    print(f"  podcast — {episode_name}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)

    # Step 1: Get transcript
    if args.text_input or inp.suffix.lower() == ".txt":
        print("  [1/2] Reading transcript from text file...", file=sys.stderr)
        transcript = inp.read_text(encoding="utf-8")
    else:
        print(f"  [1/2] Transcribing audio ({inp.suffix})...", file=sys.stderr, flush=True)
        t0 = time.time()
        from podcast.transcriber import transcribe
        transcript = transcribe(str(inp), language=args.lang)
        print(f"         {len(transcript)} chars in {time.time()-t0:.1f}s", file=sys.stderr)

    if not transcript.strip():
        print("ERROR: empty transcript", file=sys.stderr)
        sys.exit(1)

    # Step 2: Extract lessons
    print(f"  [2/2] Extracting {args.lessons} lessons"
          + (f" (focus: {args.prompt[:40]})" if args.prompt else "") + "...",
          file=sys.stderr, flush=True)
    t0 = time.time()

    from podcast.extractor import extract_lessons, _fallback_extract_lessons
    if args.no_llm:
        lessons_list = _fallback_extract_lessons(transcript, args.lessons)
        result = {
            "episode": episode_name,
            "lessons": lessons_list,
            "summary": transcript[:300] + "...",
            "metadata": {
                "model": "fallback", "n_lessons": len(lessons_list),
                "transcript_length": len(transcript), "custom_prompt": args.prompt,
                "extracted_at": __import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc).isoformat()
            }
        }
    else:
        result = extract_lessons(
            transcript=transcript,
            episode_name=episode_name,
            n_lessons=args.lessons,
            custom_prompt=args.prompt,
            model=args.model,
        )
    print(f"         {len(result.get('lessons',[]))} lessons in {time.time()-t0:.1f}s",
          file=sys.stderr)

    # Format output
    from podcast.formatter import to_markdown, to_plain
    if args.format == "markdown":
        output_str = to_markdown(result, include_quotes=not args.no_quotes)
    elif args.format == "plain":
        output_str = to_plain(result)
    else:  # json
        output_str = json.dumps(result, indent=2, ensure_ascii=False)

    # Write or print
    if args.output:
        out = pathlib.Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(output_str, encoding="utf-8")
        print(f"  Saved to {out}", file=sys.stderr)
    else:
        print(output_str)

    print(f"\n  Done — {len(result.get('lessons',[]))} lessons from '{episode_name}'",
          file=sys.stderr)


if __name__ == "__main__":
    main()
