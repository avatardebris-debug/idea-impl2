"""
cli.py — skillify command-line interface.

Usage:
    python -m skillify extraction.json --output skill.json
    python -m skillify extraction.json --id "make_sourdough_bread"
    cat extraction.json | python -m skillify -
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys
import textwrap


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="skillify",
        description="Convert an extraction JSON into a reusable skill file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              python -m skillify steps.json --output skills/sourdough.json
              cat steps.json | python -m skillify - --id make_sourdough
              python -m skillify steps.json  # prints skill JSON to stdout
        """),
    )
    parser.add_argument("input", help="Extraction JSON file or '-' for stdin")
    parser.add_argument("--output", default=None, help="Write skill to this file")
    parser.add_argument("--id", default=None, dest="skill_id",
                        help="Override skill ID (auto-generated if omitted)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")

    args = parser.parse_args()

    # Read extraction JSON
    if args.input == "-":
        raw = sys.stdin.read()
    else:
        p = pathlib.Path(args.input)
        if not p.exists():
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            sys.exit(1)
        raw = p.read_text(encoding="utf-8")

    try:
        extraction = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    from skillify.converter import convert, save_skill
    skill = convert(extraction, skill_id=args.skill_id)

    indent = 2 if args.pretty else None
    output_str = json.dumps(skill, indent=indent, ensure_ascii=False)

    if args.output:
        out = pathlib.Path(args.output)
        save_skill(skill, out)
        step_count = len(skill.get("steps", []))
        print(f"  Skill '{skill['skill_id']}' saved to {out} ({step_count} steps)", file=sys.stderr)
    else:
        print(output_str)


if __name__ == "__main__":
    main()
