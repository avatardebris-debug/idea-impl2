#!/usr/bin/env python3
"""
Deconstructor CLI — LLM candidate inventory + replacement classes.

Primary (LLM — invents structure from a bare target):
  python scripts/deconstructor.py run --mode org --target "award-winning game studio"
  python scripts/deconstructor.py run --mode org --target-file mission.txt

Secondary (no LLM):
  python scripts/deconstructor.py build ...     # parse structured text only
  python scripts/deconstructor.py from-json ... # validate supplied inventory

Other:
  validate | plan-fill | list | seed-preview | to-graph

Env:
  PIPELINE_DIR, PIPELINE_PROVIDER, PIPELINE_MODEL, OLLAMA_PLANNER_TIMEOUT

to-graph writes **draft** graph.v1 only (never smoke_pass). Smoke separately:
  python scripts/goal_compose.py smoke --goal-id <id>
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
    tf = getattr(args, "target_file", None) or ""
    if tf:
        return Path(tf).read_text(encoding="utf-8")
    t = getattr(args, "target", None) or ""
    if not str(t).strip():
        raise SystemExit("provide --target TEXT or --target-file PATH")
    return str(t)


def _add_target_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--target", default="", help="What to deconstruct")
    p.add_argument("--target-file", default="", help="Multi-line target from file")


def _add_budget(p: argparse.ArgumentParser) -> None:
    p.add_argument("--max-nodes", type=int, default=20)
    p.add_argument("--max-depth", type=int, default=3)


def _add_mode(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--mode",
        required=True,
        choices=sorted(["org", "credits", "tool_surface", "genre", "open"]),
    )


def cmd_run(args: argparse.Namespace) -> int:
    """Primary: LLM deconstruct → critique → save."""
    from pipeline.deconstructor import run_llm_deconstruct

    target = _resolve_target(args)
    inject = None
    if getattr(args, "inject_json", None):
        inject = Path(args.inject_json).read_text(encoding="utf-8")
    elif getattr(args, "inject_response", None):
        inject = Path(args.inject_response).read_text(encoding="utf-8")

    try:
        doc = run_llm_deconstruct(
            target,
            mode=args.mode,
            max_nodes=int(args.max_nodes),
            max_depth=int(args.max_depth),
            deconstruct_id=args.id or None,
            provider=args.provider or None,
            model=args.model or None,
            save=not bool(args.no_save),
            llm_response=inject,
            max_retries=int(args.retries),
        )
    except Exception as exc:
        _print_json({"error": str(exc)})
        return 1

    path_out = None
    if not args.no_save:
        from pipeline.deconstructor import deconstruct_path

        path_out = str(deconstruct_path(str(doc.get("id"))))
    _print_json(
        {
            "path": path_out,
            "id": doc.get("id"),
            "status": doc.get("status"),
            "parse_source": doc.get("parse_source"),
            "llm_provider": doc.get("llm_provider"),
            "llm_model": doc.get("llm_model"),
            "llm_route_reason": doc.get("llm_route_reason"),
            "needs_structure": doc.get("needs_structure"),
            "critique": doc.get("critique"),
            "candidate_count": len(doc.get("candidates") or []),
            "names": [c.get("name") for c in (doc.get("candidates") or [])],
            "doc": doc,
        }
    )
    return 0 if (doc.get("critique") or {}).get("ok") else 1


def cmd_build(args: argparse.Namespace) -> int:
    """Secondary: structure-parse only (no LLM). Bare titles → needs_structure."""
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
            "hint": "Use `run` for LLM deconstruct of bare titles.",
            "doc": doc,
        }
    )
    if doc.get("needs_structure"):
        return 2
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
    _print_json(plan_fill_actions(doc))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    from pipeline.deconstructor import list_deconstructs

    _print_json(list_deconstructs())
    return 0


def cmd_seed_preview(args: argparse.Namespace) -> int:
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


def cmd_to_graph(args: argparse.Namespace) -> int:
    """deconstruct.v0 → draft graph.v1 (no smoke). Save under graphs/{goal_id}.json."""
    from pipeline.deconstructor import load_deconstruct
    from pipeline.goal_graph import compile_graph_from_deconstruct, save_graph

    doc = load_deconstruct(args.id)
    if doc is None:
        _print_json({"error": f"not found: {args.id}"})
        return 1

    goal_id = (args.goal_id or "").strip() or None
    goal_text = (args.goal_text or "").strip() or None
    max_nodes = int(args.max_nodes) if args.max_nodes else None

    graph = compile_graph_from_deconstruct(
        doc,
        goal_id=goal_id,
        goal_text=goal_text,
        max_nodes=max_nodes,
        attach_plan_fill=not bool(args.no_plan_fill),
    )

    path_out = None
    if not args.no_save:
        path_out = str(save_graph(graph))

    crit = graph.get("critique") or {}
    status = str(graph.get("status") or "")
    _print_json(
        {
            "path": path_out,
            "goal_id": graph.get("goal_id"),
            "deconstruct_id": graph.get("deconstruct_id"),
            "status": status,
            "smoke_pass": graph.get("smoke_pass"),
            "production_graph": graph.get("production_graph"),
            "critique": crit,
            "node_count": len(graph.get("nodes") or []),
            "edge_count": len(graph.get("edges") or []),
            "names": [n.get("label") for n in (graph.get("nodes") or [])],
            "hint": (
                "Draft only. Run smoke separately: "
                f"python scripts/goal_compose.py smoke --goal-id {graph.get('goal_id')}"
            ),
            "graph": graph,
        }
    )
    # Exit 0 when critique ok or soft draft (critiqued/draft); 1 if blocked/missing.
    if status in ("blocked",) and not crit.get("ok"):
        return 1
    if not (graph.get("nodes") or []) and doc.get("needs_structure"):
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    # Load project .env early so XAI_API_KEY is visible before provider auto-route
    try:
        from pipeline.llm_route import ensure_project_dotenv

        ensure_project_dotenv()
    except Exception:
        pass

    ap = argparse.ArgumentParser(
        description="Deconstructor: LLM inventory (run) or parse/validate (build/from-json)"
    )
    ap.add_argument("--pipeline-dir", default="", help="Override PIPELINE_DIR")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser(
        "run",
        help=(
            "PRIMARY: LLM deconstruct → deconstruct.v0. "
            "Auto: Ollama if model present, else xAI Grok when XAI_API_KEY/.env set"
        ),
    )
    _add_mode(p_run)
    _add_target_args(p_run)
    p_run.add_argument("--id", default="")
    p_run.add_argument(
        "--provider",
        default="",
        help="ollama | grok | auto (default: auto via llm_route / Hermes policy)",
    )
    p_run.add_argument(
        "--model",
        default="",
        help="Model id (Ollama tag or grok-3). Auto picks grok-3 on xAI when Ollama model missing",
    )
    p_run.add_argument(
        "--inject-response",
        default="",
        help="Skip LLM: use this file as model response (tests/offline)",
    )
    p_run.add_argument(
        "--inject-json",
        default="",
        help="Alias of --inject-response",
    )
    p_run.add_argument("--no-save", action="store_true")
    p_run.add_argument("--retries", type=int, default=1, help="Critique-repair retries")
    _add_budget(p_run)
    p_run.set_defaults(func=cmd_run)

    p_b = sub.add_parser(
        "build",
        help="SECONDARY: parse structured target only (no LLM; bare title → needs_structure)",
    )
    _add_mode(p_b)
    _add_target_args(p_b)
    p_b.add_argument("--id", default="")
    p_b.add_argument("--notes", default="")
    _add_budget(p_b)
    p_b.set_defaults(func=cmd_build)

    p_j = sub.add_parser("from-json", help="Validate/save agent-supplied candidates")
    p_j.add_argument("--path", required=True)
    p_j.add_argument("--target", default="")
    p_j.add_argument(
        "--mode",
        default="open",
        choices=sorted(["org", "credits", "tool_surface", "genre", "open"]),
    )
    p_j.add_argument("--id", default="")
    p_j.add_argument("--notes", default="")
    _add_budget(p_j)
    p_j.set_defaults(func=cmd_from_json)

    p_v = sub.add_parser("validate", help="Re-critique a saved deconstruct")
    p_v.add_argument("--id", required=True)
    p_v.add_argument("--max-nodes", type=int, default=0)
    p_v.add_argument("--max-depth", type=int, default=0)
    p_v.set_defaults(func=cmd_validate)

    p_p = sub.add_parser("plan-fill", help="Map candidates → factory/promote actions")
    p_p.add_argument("--id", required=True)
    p_p.set_defaults(func=cmd_plan_fill)

    p_l = sub.add_parser("list", help="List saved deconstructs")
    p_l.set_defaults(func=cmd_list)

    p_s = sub.add_parser("seed-preview", help="Structure-parse preview without save")
    _add_mode(p_s)
    _add_target_args(p_s)
    _add_budget(p_s)
    p_s.set_defaults(func=cmd_seed_preview)

    p_tg = sub.add_parser(
        "to-graph",
        help=(
            "Bridge deconstruct.v0 → draft graph.v1 (CLASS_TO_GRAPH_KIND, parent_id edges). "
            "Never sets smoke_pass; run goal_compose smoke separately."
        ),
    )
    p_tg.add_argument("--id", required=True, help="Saved deconstruct id")
    p_tg.add_argument(
        "--goal-id",
        default="",
        help="graph goal_id (default: deconstruct id)",
    )
    p_tg.add_argument(
        "--goal-text",
        default="",
        help="Optional goal text (default: deconstruct target)",
    )
    p_tg.add_argument(
        "--max-nodes",
        type=int,
        default=0,
        help="Cap nodes (0 = use deconstruct max_nodes / default)",
    )
    p_tg.add_argument("--no-save", action="store_true")
    p_tg.add_argument(
        "--no-plan-fill",
        action="store_true",
        help="Skip attaching plan_fill metadata on graph notes",
    )
    p_tg.set_defaults(func=cmd_to_graph)

    args = ap.parse_args(argv)
    _bind_pipeline_dir(args.pipeline_dir)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
