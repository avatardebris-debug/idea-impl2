"""CLI entry point for subgoal_generator."""

from __future__ import annotations

import argparse
import json
import sys

from subgoal_generator.generator import SubgoalGenerator
from subgoal_generator.prompt_builder import build_prompt


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Decompose a high-level goal into subgoals."
    )
    parser.add_argument("--goal", required=True, help="The high-level goal to decompose.")
    parser.add_argument(
        "--output",
        default=None,
        help="Path to master_ideas.md to append subgoals to.",
    )
    parser.add_argument(
        "--provider",
        default="openai",
        choices=["openai", "ollama"],
        help="LLM provider (default: openai).",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="LLM model name (default: gpt-4o-mini).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the generated prompt and exit without calling the LLM.",
    )
    parser.add_argument(
        "--format",
        default="md",
        choices=["md", "json"],
        help="Output format: 'md' for markdown entries (default), 'json' for JSON.",
    )
    args = parser.parse_args()

    # Build the prompt (used by both dry-run and actual generation)
    prompt = build_prompt(args.goal)

    if args.dry_run:
        print("=== DRY RUN: Generated Prompt ===")
        print(prompt)
        print("=== END DRY RUN ===")
        return

    generator = SubgoalGenerator(provider=args.provider, model=args.model)
    subgoals = generator.generate(args.goal, master_ideas_path=args.output)

    if args.format == "json":
        result = [
            {
                "title": s.title,
                "description": s.description,
                "dependencies": s.dependencies,
                "priority": s.priority,
            }
            for s in subgoals
        ]
        print(json.dumps(result, indent=2))
    else:
        # Default: markdown output
        for s in subgoals:
            print(f"- **{s.title}**: {s.description}")
            if s.dependencies:
                print(f"  Dependencies: {', '.join(s.dependencies)}")
            if s.priority != 1:
                print(f"  Priority: {s.priority}")
            print()


if __name__ == "__main__":
    main()
