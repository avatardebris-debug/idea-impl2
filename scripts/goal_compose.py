#!/usr/bin/env python3
"""
Goal compose CLI — compile graph.v1, plan factory actions, attempt via policy.

Usage:
  python scripts/goal_compose.py compile --goal-id ID --text "..." [--hits-json file]
  python scripts/goal_compose.py plan-factories --goal-id ID
  python scripts/goal_compose.py attempt --goal-id ID --text "..."

Env:
  PIPELINE_DIR  — factory output root (graphs/ lives here)
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


def _load_hits(path: str | None) -> list[dict] | None:
    if not path:
        return None
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("hits"), list):
        return data["hits"]
    raise SystemExit(f"hits-json must be a list or {{hits: [...]}}: {path}")


def cmd_compile(args: argparse.Namespace) -> int:
    from pipeline.goal_graph import compile_goal_graph, save_graph

    hits = _load_hits(args.hits_json)
    graph = compile_goal_graph(
        args.text,
        goal_id=args.goal_id,
        route_hits=hits,
    )
    path = save_graph(graph)
    print(json.dumps({"path": str(path), "graph": graph}, indent=2, default=str))
    return 0


def cmd_plan_factories(args: argparse.Namespace) -> int:
    from pipeline.goal_graph import load_graph, plan_factory_actions

    graph = load_graph(args.goal_id)
    if graph is None:
        print(json.dumps({"error": f"no graph for goal_id={args.goal_id}"}))
        return 1
    out = plan_factory_actions(graph)
    print(json.dumps(out, indent=2, default=str))
    return 0 if not out.get("issues") else 0  # issues are soft; still ok


def cmd_attempt(args: argparse.Namespace) -> int:
    from pipeline.goal_graph import compile_goal_graph, load_graph, save_graph
    from pipeline.goal_policy import (
        append_policy_history,
        classify_goal_branch,
        execute_policy,
    )

    graph = load_graph(args.goal_id)
    if graph is None:
        hits = _load_hits(args.hits_json) if getattr(args, "hits_json", None) else None
        graph = compile_goal_graph(
            args.text,
            goal_id=args.goal_id,
            route_hits=hits,
        )
        save_graph(graph)

    text = args.text or str(graph.get("goal_text") or "")
    decision = classify_goal_branch(
        branch_type="capability",
        text=text,
        route_hits=None,
    )
    exec_out = execute_policy(
        decision,
        goal_text=text,
        branch_id=args.goal_id,
    )
    try:
        append_policy_history(
            {
                "branch": args.goal_id,
                "policy": decision.policy,
                "reason": decision.reason,
                "status": exec_out.get("status"),
                "goal_trace_id": exec_out.get("goal_id"),
                "capability": decision.capability_slug,
                "connector": decision.connector_slug,
                "source": "goal_compose.attempt",
            }
        )
    except Exception:
        pass

    result = {
        "goal_id": args.goal_id,
        "policy": decision.policy,
        "reason": decision.reason,
        "execute": exec_out,
        "graph_status": graph.get("status"),
        "nodes": len(graph.get("nodes") or []),
    }
    print(json.dumps(result, indent=2, default=str))
    status = str(exec_out.get("status") or "")
    if status in ("failed",):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Goal compose: compile graph.v1, plan factories, attempt policy"
    )
    ap.add_argument("--pipeline-dir", default="", help="Override PIPELINE_DIR")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_compile = sub.add_parser("compile", help="Compile + save graph.v1")
    p_compile.add_argument("--goal-id", required=True)
    p_compile.add_argument("--text", required=True, help="Goal text")
    p_compile.add_argument(
        "--hits-json",
        default="",
        help="Optional JSON file of route hits (list or {hits: [...]})",
    )

    p_plan = sub.add_parser(
        "plan-factories",
        help="Load graph; enqueue missing MCPs; log software handoffs",
    )
    p_plan.add_argument("--goal-id", required=True)

    p_attempt = sub.add_parser(
        "attempt",
        help="Compile if missing; classify + execute_policy on text",
    )
    p_attempt.add_argument("--goal-id", required=True)
    p_attempt.add_argument("--text", required=True, help="Goal / branch text")
    p_attempt.add_argument(
        "--hits-json",
        default="",
        help="Optional route hits when compiling missing graph",
    )

    args = ap.parse_args(argv)
    _bind_pipeline_dir(args.pipeline_dir)

    if args.cmd == "compile":
        return cmd_compile(args)
    if args.cmd == "plan-factories":
        return cmd_plan_factories(args)
    if args.cmd == "attempt":
        return cmd_attempt(args)
    ap.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
