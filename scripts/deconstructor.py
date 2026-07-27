#!/usr/bin/env python3
"""
Deconstructor v0 CLI — candidate inventory + replacement classes.

Usage:
  python scripts/deconstructor.py build --mode org --target "small indie game studio"
  python scripts/deconstructor.py build --mode credits --target "NES platformer credits"
  python scripts/deconstructor.py validate --id org_small-indie-game-studio
  python scripts/deconstructor.py plan-fill --id org_small-indie-game-studio
  python scripts/deconstructor.py from-json --path inventory.json
  python scripts/deconstructor.py list

Env:
  PIPELINE_DIR  — factory output root (deconstructs/ lives here)

Does not write production graph.v1. See notes/lmao-agi-discuss.md.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _bind_pipeline_dir(explicit: str) -> None:
    if explicit:
        os.environ["PIPELINE_DIR"] = explicit
    if os.environ.get("PIPELINE_DIR", "").strip():
        try:
            from pipeline.paths import reload_pipeline_dir

            reload_pipeline_dir()
        except Exception:
            pass


def _print_json(obj: object) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def _resolve_target(args: argparse.Namespace) -> str:
    """Prefer --target-file for multi-line structure; else --target."""
    tf = getattr(args, "target_file", None) or ""
    if tf:
        p = Path(tf)
        return p.read_text(encoding="utf-8")
    t = getattr(args, "target", None) or ""
    if not str(t).strip():
        raise SystemExit("provide --target TEXT or --target-file PATH (structured lists deconstruct)")
    return str(t)


def cmd_build(args: argparse.Namespace) -> int:
    from pipeline.deconstructor import build_deconstruct, save_deconstruct

    target = _resolve_target(args)
    doc = build_deconstruct(
        target,
        mode=args.mode,
        deconstruct_id=args.id or None,
        max_nodes=int(args.max_nodes),
        max_depth=int(args.max_depth),
        notes=args.notes or "",
    )
    path = save_deconstruct(doc)
    _print_json(
        {
            "path": str(path),
            "id": doc.get("id"),
            "status": doc.get("status"),
            "needs_structure": doc.get("needs_structure"),
            "parse_source": doc.get("parse_source"),
            "critique": doc.get("critique"),
            "candidate_count": len(doc.get("candidates") or []),
            "names": [c.get("name") for c in (doc.get("candidates") or [])],
            "doc": doc,
        }
    )
    if doc.get("needs_structure"):
        return 2  # distinct from critique fail
    return 0 if (doc.get("critique") or {}).get("ok") else 1


def cmd_from_json(args: argparse.Namespace) -> int:
    from pipeline.deconstructor import from_candidates, save_deconstruct

    path = Path(args.path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        candidates = data
        target = args.target or path.stem
        mode = args.mode
        departments = None
        did = args.id
        notes = args.notes or ""
    elif isinstance(data, dict):
        if isinstance(data.get("candidates"), list):
            candidates = data["candidates"]
            target = args.target or str(data.get("target") or path.stem)
            mode = args.mode or str(data.get("mode") or "open")
            departments = data.get("departments")
            did = args.id or data.get("id")
            notes = args.notes or str(data.get("notes") or "")
        else:
            raise SystemExit("JSON must be a list of candidates or {candidates: [...]}")
    else:
        raise SystemExit("JSON must be a list or object")

    doc = from_candidates(
        target,
        candidates,
        mode=mode,
        departments=departments if isinstance(departments, list) else None,
        deconstruct_id=str(did) if did else None,
        max_nodes=int(args.max_nodes),
        max_depth=int(args.max_depth),
        notes=notes,
    )
    out = save_deconstruct(doc)
    _print_json(
        {
            "path": str(out),
            "id": doc.get("id"),
            "status": doc.get("status"),
            "critique": doc.get("critique"),
            "doc": doc,
        }
    )
    return 0 if (doc.get("critique") or {}).get("ok") else 1


def cmd_validate(args: argparse.Namespace) -> int:
    from pipeline.deconstructor import critique_deconstruct, load_deconstruct

    doc = load_deconstruct(args.id)
    if doc is None:
        _print_json({"error": f"not found: {args.id}"})
        return 1
    crit = critique_deconstruct(
        doc,
        max_nodes=int(args.max_nodes) if args.max_nodes else int(doc.get("max_nodes") or 20),
        max_depth=int(args.max_depth) if args.max_depth else int(doc.get("max_depth") or 3),
    )
    _print_json({"id": doc.get("id"), "critique": crit})
    return 0 if crit.get("ok") else 1


def cmd_plan_fill(args: argparse.Namespace) -> int:
    from pipeline.deconstructor import load_deconstruct, plan_fill_actions

    doc = load_deconstruct(args.id)
    if doc is None:
        _print_json({"error": f"not found: {args.id}"})
        return 1
    out = plan_fill_actions(doc)
    _print_json(out)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    from pipeline.deconstructor import list_deconstructs

    _print_json(list_deconstructs())
    return 0


def cmd_seed_preview(args: argparse.Namespace) -> int:
    """Print parse+classify result without saving."""
    from pipeline.deconstructor import build_deconstruct

    target = _resolve_target(args)
    doc = build_deconstruct(
        target,
        mode=args.mode,
        max_nodes=int(args.max_nodes),
        max_depth=int(args.max_depth),
    )
    _print_json(doc)
    if doc.get("needs_structure"):
        return 2
    return 0 if (doc.get("critique") or {}).get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Deconstructor v0: candidate inventory + replacement classes (not graph.v1)"
    )
    ap.add_argument("--pipeline-dir", default="", help="Override PIPELINE_DIR")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add_budget(p: argparse.ArgumentParser) -> None:
        p.add_argument("--max-nodes", type=int, default=20)
        p.add_argument("--max-depth", type=int, default=3)

    p_b = sub.add_parser(
        "build",
        help="Parse target structure → classify → save deconstruct.v0 (no fixed templates)",
    )
    p_b.add_argument("--mode", required=True, choices=sorted(
        ["org", "credits", "tool_surface", "genre", "open"]
    ))
    p_b.add_argument(
        "--target",
        default="",
        help="Text to deconstruct (lists, 'Dept: a, b', credits Role - Name). Bare titles need structure.",
    )
    p_b.add_argument(
        "--target-file",
        default="",
        help="Read multi-line structured target from file (preferred for org charts)",
    )
    p_b.add_argument("--id", default="", help="Optional deconstruct id")
    p_b.add_argument("--notes", default="")
    add_budget(p_b)
    p_b.set_defaults(func=cmd_build)

    p_j = sub.add_parser("from-json", help="Validate/save agent- or fixture-supplied candidates")
    p_j.add_argument("--path", required=True, help="JSON list or {candidates, target, mode}")
    p_j.add_argument("--target", default="", help="Override target")
    p_j.add_argument(
        "--mode",
        default="open",
        choices=sorted(["org", "credits", "tool_surface", "genre", "open"]),
    )
    p_j.add_argument("--id", default="")
    p_j.add_argument("--notes", default="")
    add_budget(p_j)
    p_j.set_defaults(func=cmd_from_json)

    p_v = sub.add_parser("validate", help="Re-critique a saved deconstruct")
    p_v.add_argument("--id", required=True)
    p_v.add_argument("--max-nodes", type=int, default=0)
    p_v.add_argument("--max-depth", type=int, default=0)
    p_v.set_defaults(func=cmd_validate)

    p_p = sub.add_parser("plan-fill", help="Map candidates → next factory/promote actions")
    p_p.add_argument("--id", required=True)
    p_p.set_defaults(func=cmd_plan_fill)

    p_l = sub.add_parser("list", help="List saved deconstructs")
    p_l.set_defaults(func=cmd_list)

    p_s = sub.add_parser("seed-preview", help="Print parse+classify without saving")
    p_s.add_argument("--mode", required=True, choices=sorted(
        ["org", "credits", "tool_surface", "genre", "open"]
    ))
    p_s.add_argument("--target", default="")
    p_s.add_argument("--target-file", default="")
    add_budget(p_s)
    p_s.set_defaults(func=cmd_seed_preview)

    args = ap.parse_args(argv)
    _bind_pipeline_dir(args.pipeline_dir)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
