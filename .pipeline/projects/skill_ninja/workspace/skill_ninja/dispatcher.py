"""
dispatcher.py — Skill loader and interactive runner.

Loads skill JSON files, presents steps to the user, and optionally calls
an LLM to adapt the skill to a specific context/target.
"""
from __future__ import annotations
import json
import pathlib
import sys
from typing import Any


def load_skill(path: str | pathlib.Path) -> dict[str, Any]:
    """Load a skill JSON file."""
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def list_skills(library_dir: str | pathlib.Path) -> list[dict[str, Any]]:
    """Return all skill dicts from JSON files in library_dir."""
    skills = []
    for p in sorted(pathlib.Path(library_dir).glob("**/*.json")):
        try:
            skill = load_skill(p)
            if "skill_id" in skill and "steps" in skill:
                skill["_path"] = str(p)
                skills.append(skill)
        except Exception:
            continue
    return skills


def format_skill_summary(skill: dict) -> str:
    """Return a compact summary line for a skill."""
    sid   = skill.get("skill_id", "?")
    name  = skill.get("name", "?")
    steps = len(skill.get("steps", []))
    tags  = ", ".join(skill.get("tags", []))
    return f"  [{sid}]  {name}  ({steps} steps)  [{tags}]"


def run_skill_interactive(skill: dict) -> None:
    """Present each step to the user interactively in the terminal."""
    name  = skill.get("name", "Skill")
    steps = skill.get("steps", [])
    tips  = skill.get("tips", [])
    comps = skill.get("components", [])

    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")

    desc = skill.get("description", "")
    if desc:
        print(f"\n  {desc}\n")

    if comps:
        print("  COMPONENTS / INGREDIENTS:")
        for c in comps:
            qty   = c.get("quantity", "")
            unit  = c.get("unit", "")
            cname = c.get("name", "")
            notes = c.get("notes", "")
            line  = f"    • {qty} {unit} {cname}".strip()
            if notes:
                line += f"  ({notes})"
            print(line)
        print()

    print(f"  STEPS ({len(steps)} total):")
    for i, step in enumerate(steps, 1):
        action  = step.get("action", "")
        detail  = step.get("detail", "")
        dur     = step.get("duration", "")
        tools   = step.get("tools", [])
        warns   = step.get("warnings", [])

        print(f"\n  [{i}/{len(steps)}] {action}")
        if detail and detail != action:
            print(f"       {detail}")
        if dur:
            print(f"       ⏱  {dur}")
        if tools:
            print(f"       🔧 {', '.join(tools)}")
        for w in warns:
            print(f"       ⚠️  {w}")

        if i < len(steps):
            try:
                resp = input("  [Enter] next / [q] quit / [n] number: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n  Stopped.")
                return
            if resp == "q":
                print("  Stopped.")
                return
            if resp.isdigit():
                target = int(resp) - 1
                if 0 <= target < len(steps):
                    # Jump: slice and re-run from that step
                    skill_copy = dict(skill, steps=steps[target:])
                    run_skill_interactive(skill_copy)
                    return

    if tips:
        print("\n  TIPS:")
        for t in tips:
            print(f"    💡 {t}")

    print(f"\n{'='*60}")
    print(f"  ✅ Complete: {name}")
    print(f"{'='*60}\n")
