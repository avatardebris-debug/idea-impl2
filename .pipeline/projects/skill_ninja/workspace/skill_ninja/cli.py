"""
cli.py — skill_ninja master CLI.

Subcommands:
    build   text.txt --topic X --output skills/X.json  (text → extract → skillify)
    run     skills/X.json                               (interactive step runner)
    list    skills/                                     (list all skills in dir)
    show    skills/X.json                               (print skill metadata)
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys
import textwrap


def cmd_build(args: argparse.Namespace) -> None:
    """Full pipeline: raw text → extraction → skill JSON."""
    # Read text
    if args.input == "-":
        text = sys.stdin.read()
    else:
        p = pathlib.Path(args.input)
        if not p.exists():
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            sys.exit(1)
        text = p.read_text(encoding="utf-8")

    if not text.strip():
        print("ERROR: empty input", file=sys.stderr)
        sys.exit(1)

    print(f"\n  skill_ninja build", file=sys.stderr)
    print(f"  {'─'*40}", file=sys.stderr)

    # Step 1: Extract
    print(f"  [1/2] Extracting ({args.format})...", file=sys.stderr, flush=True)
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent.parent / "extraction" / "workspace"))
    try:
        from extraction.extractor import extract, _fallback_extract
        if args.no_llm:
            extraction = _fallback_extract(text, args.topic, args.format)
        else:
            extraction = extract(text, topic=args.topic, fmt=args.format, model=args.model)
    except ImportError:
        print("  Warning: extraction package not found on path — using built-in fallback", file=sys.stderr)
        from skill_ninja._embedded_extractor import extract_fallback
        extraction = extract_fallback(text, args.topic, args.format)

    step_count = len(extraction.get("steps", []))
    print(f"         {step_count} steps extracted", file=sys.stderr)

    # Step 2: Skillify
    print(f"  [2/2] Converting to skill...", file=sys.stderr, flush=True)
    sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent.parent / "skillify" / "workspace"))
    try:
        from skillify.converter import convert, save_skill
    except ImportError:
        print("  Warning: skillify package not found — using built-in converter", file=sys.stderr)
        from skill_ninja._embedded_converter import convert, save_skill

    skill = convert(extraction, skill_id=args.skill_id)

    if args.output:
        out = pathlib.Path(args.output)
        save_skill(skill, out)
        print(f"  Skill '{skill['skill_id']}' → {out}", file=sys.stderr)
    else:
        print(json.dumps(skill, indent=2, ensure_ascii=False))


def cmd_run(args: argparse.Namespace) -> None:
    from skill_ninja.dispatcher import load_skill, run_skill_interactive
    try:
        skill = load_skill(args.skill_file)
    except Exception as e:
        print(f"ERROR loading skill: {e}", file=sys.stderr)
        sys.exit(1)
    run_skill_interactive(skill)


def cmd_list(args: argparse.Namespace) -> None:
    from skill_ninja.dispatcher import list_skills, format_skill_summary
    lib = pathlib.Path(args.library)
    if not lib.exists():
        print(f"ERROR: directory not found: {lib}", file=sys.stderr)
        sys.exit(1)
    skills = list_skills(lib)
    if not skills:
        print(f"  No skills found in {lib}")
        return
    print(f"\n  Skills in {lib}/ ({len(skills)} found):\n")
    for s in skills:
        print(format_skill_summary(s))
    print()


def cmd_show(args: argparse.Namespace) -> None:
    from skill_ninja.dispatcher import load_skill
    try:
        skill = load_skill(args.skill_file)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"\n  Skill: {skill.get('name')}")
    print(f"  ID:    {skill.get('skill_id')}")
    print(f"  Tags:  {', '.join(skill.get('tags', []))}")
    print(f"  Steps: {len(skill.get('steps', []))}")
    print(f"  Desc:  {skill.get('description', '')}")
    print(f"  Created: {skill.get('created_at', '')}")
    if args.full:
        print("\n" + json.dumps(skill, indent=2, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="skill_ninja",
        description="Build, manage and run JSON skill files (text → extract → skill → run)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              skill_ninja build article.txt --topic "sourdough bread" --output skills/sourdough.json
              skill_ninja run  skills/sourdough.json
              skill_ninja list skills/
              skill_ninja show skills/sourdough.json
        """),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # build
    p_build = sub.add_parser("build", help="Build a skill from text (extract + skillify)")
    p_build.add_argument("input",  help="Input text file or '-' for stdin")
    p_build.add_argument("--topic",  default="", help="Topic hint for extraction")
    p_build.add_argument("--format", choices=["recipe","steps","sop"], default="steps")
    p_build.add_argument("--output", default=None, help="Output .json path")
    p_build.add_argument("--model",  default="qwen3:6b")
    p_build.add_argument("--skill-id", default=None, dest="skill_id")
    p_build.add_argument("--no-llm",   action="store_true")

    # run
    p_run = sub.add_parser("run", help="Run a skill interactively")
    p_run.add_argument("skill_file", help="Path to skill .json file")

    # list
    p_list = sub.add_parser("list", help="List all skills in a directory")
    p_list.add_argument("library", help="Directory containing skill .json files")

    # show
    p_show = sub.add_parser("show", help="Show skill metadata")
    p_show.add_argument("skill_file", help="Path to skill .json file")
    p_show.add_argument("--full", action="store_true", help="Print full JSON")

    args = parser.parse_args()

    if args.command == "build":  cmd_build(args)
    elif args.command == "run":  cmd_run(args)
    elif args.command == "list": cmd_list(args)
    elif args.command == "show": cmd_show(args)


if __name__ == "__main__":
    main()
