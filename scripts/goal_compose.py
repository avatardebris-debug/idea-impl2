#!/usr/bin/env python3
"""
Goal compose CLI — compile graph.v1, plan factory actions, smoke, attempt via policy.

Usage:
  python scripts/goal_compose.py compile --goal-id ID --text "..." [--hits-json file]
      [--include-external id1,id2]
  python scripts/goal_compose.py from-deconstruct --id DECONSTRUCT_ID [--goal-id ID]
  python scripts/goal_compose.py plan-factories --goal-id ID
  python scripts/goal_compose.py smoke --goal-id ID
  python scripts/goal_compose.py attempt --goal-id ID --text "..."

Env:
  PIPELINE_DIR  — factory output root (graphs/ lives here)

from-deconstruct writes **draft** graph.v1 only. Smoke is a separate step
(never auto smoke_pass from deconstruct convert).

External nodes (Phase 6): only **promoted** ids under external/promoted/ may
be attached via --include-external or hits-json (trust=external). Compose never
git-clones. Smoke fails on draft/quarantine/approved-not-promoted/revoked.
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


def _parse_include_external(raw: str | None) -> list[str] | None:
    if not raw or not str(raw).strip():
        return None
    ids = [x.strip() for x in str(raw).split(",") if x.strip()]
    return ids or None


def cmd_compile(args: argparse.Namespace) -> int:
    from pipeline.goal_graph import compile_goal_graph, save_graph

    hits = _load_hits(args.hits_json)
    include_ext = _parse_include_external(getattr(args, "include_external", None))
    try:
        graph = compile_goal_graph(
            args.text,
            goal_id=args.goal_id,
            route_hits=hits,
            include_promoted_ids=include_ext,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "hint": (
                        "External ids must be promoted first: "
                        "pin → scan → approve → promote. "
                        "Compose never git-clones."
                    ),
                },
                indent=2,
            )
        )
        return 1
    path = save_graph(graph)
    print(json.dumps({"path": str(path), "graph": graph}, indent=2, default=str))
    return 0


def cmd_from_deconstruct(args: argparse.Namespace) -> int:
    """Load deconstruct.v0 → draft graph.v1 → save. Smoke is separate."""
    from pipeline.deconstructor import load_deconstruct
    from pipeline.goal_graph import compile_graph_from_deconstruct, save_graph

    doc = load_deconstruct(args.id)
    if doc is None:
        print(json.dumps({"error": f"not found deconstruct id={args.id}"}))
        return 1

    goal_id = (args.goal_id or "").strip() or None
    goal_text = (args.text or "").strip() or None
    max_nodes = int(args.max_nodes) if getattr(args, "max_nodes", 0) else None

    graph = compile_graph_from_deconstruct(
        doc,
        goal_id=goal_id,
        goal_text=goal_text,
        max_nodes=max_nodes,
    )
    path = save_graph(graph)
    crit = graph.get("critique") or {}
    out = {
        "path": str(path),
        "goal_id": graph.get("goal_id"),
        "deconstruct_id": graph.get("deconstruct_id"),
        "status": graph.get("status"),
        "smoke_pass": graph.get("smoke_pass"),
        "production_graph": graph.get("production_graph"),
        "critique": crit,
        "nodes": [n.get("label") or n.get("slug") for n in (graph.get("nodes") or [])],
        "hint": (
            "Draft candidate map only. Smoke separately: "
            f"python scripts/goal_compose.py smoke --goal-id {graph.get('goal_id')}"
        ),
        "graph": graph,
    }
    print(json.dumps(out, indent=2, default=str))
    status = str(graph.get("status") or "")
    if status == "blocked" and not crit.get("ok"):
        return 1
    return 0


def cmd_fixture_mcps(args: argparse.Namespace) -> int:
    """Build graph.v1 from already-smoked MCPs (map-blocks fixture)."""
    from pipeline.goal_graph import compile_graph_from_smoked_mcps, critique_graph, save_graph

    slugs = None
    if args.slugs:
        slugs = [s.strip() for s in args.slugs.split(",") if s.strip()]
    graph = compile_graph_from_smoked_mcps(
        goal_id=args.goal_id,
        goal_text=args.text
        or "Utility MCP workflow: compose smoked tools as graph nodes",
        mcp_slugs=slugs,
        max_nodes=int(args.max_nodes),
    )
    crit = critique_graph(graph)
    graph["critique"] = crit
    graph["status"] = "executable" if crit.get("ok") else "blocked"
    path = save_graph(graph)
    print(
        json.dumps(
            {
                "path": str(path),
                "nodes": [n.get("slug") for n in (graph.get("nodes") or [])],
                "critique": crit,
                "graph": graph,
            },
            indent=2,
            default=str,
        )
    )
    return 0 if crit.get("ok") else 1


def cmd_plan_factories(args: argparse.Namespace) -> int:
    from pipeline.goal_graph import load_graph, plan_factory_actions

    graph = load_graph(args.goal_id)
    if graph is None:
        print(json.dumps({"error": f"no graph for goal_id={args.goal_id}"}))
        return 1
    out = plan_factory_actions(graph)
    print(json.dumps(out, indent=2, default=str))
    return 0 if not out.get("issues") else 0  # issues are soft; still ok


def cmd_smoke(args: argparse.Namespace) -> int:
    """Whole-graph cheap smoke (P3). Load → smoke_graph → save → JSON; exit 0/1."""
    from pipeline.goal_graph import load_graph, save_graph, smoke_graph

    graph = load_graph(args.goal_id)
    if graph is None:
        print(json.dumps({"error": f"no graph for goal_id={args.goal_id}"}))
        return 1
    report = smoke_graph(graph, mutate=True, re_critique=True)
    path = save_graph(graph)
    out = {
        "path": str(path),
        "goal_id": args.goal_id,
        "smoke_pass": report.get("smoke_pass"),
        "ok": report.get("ok"),
        "blocked": report.get("blocked"),
        "graph_status": graph.get("status"),
        "issues": report.get("issues") or [],
        "node_results": report.get("node_results") or [],
        "ts": report.get("ts"),
    }
    print(json.dumps(out, indent=2, default=str))
    return 0 if report.get("smoke_pass") else 1


def cmd_attempt(args: argparse.Namespace) -> int:
    from pipeline.goal_graph import compile_goal_graph, load_graph, save_graph, smoke_graph
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

    # Light P3: if graph is executable (nodes resolved) and not yet smoke_pass,
    # run whole-graph smoke before policy execute. Fail closed on smoke miss.
    smoke_report = None
    g_status = str(graph.get("status") or "")
    nodes = graph.get("nodes") if isinstance(graph.get("nodes"), list) else []
    has_missing = any(
        isinstance(n, dict) and str(n.get("status") or "").lower() == "missing"
        for n in nodes
    )
    # Only auto-smoke when nodes look resolved (executable) or prior smoke failed.
    # Separate CLI: goal_compose.py smoke --goal-id ID
    needs_smoke = (
        not has_missing
        and not graph.get("smoke_pass")
        and g_status in ("executable", "smoke_failed")
        and bool(nodes)
    )
    if needs_smoke:
        smoke_report = smoke_graph(graph, mutate=True, re_critique=True)
        try:
            save_graph(graph)
        except Exception as exc:
            # Fail closed: do not continue policy execute if smoke mutation
            # cannot be persisted (disk/ACL/path). Matches cmd_smoke honesty.
            result = {
                "goal_id": args.goal_id,
                "policy": None,
                "reason": "smoke_save_failed",
                "execute": {"status": "smoke_save_failed"},
                "graph_status": graph.get("status"),
                "smoke": {
                    "smoke_pass": smoke_report.get("smoke_pass"),
                    "issues": list(smoke_report.get("issues") or [])
                    + [f"save_graph failed: {exc}"],
                    "node_results": smoke_report.get("node_results") or [],
                    "blocked": smoke_report.get("blocked"),
                    "save_error": str(exc),
                },
                "nodes": len(nodes),
            }
            print(json.dumps(result, indent=2, default=str))
            return 1
        if not smoke_report.get("smoke_pass"):
            result = {
                "goal_id": args.goal_id,
                "policy": None,
                "reason": "whole_graph_smoke_failed",
                "execute": {"status": "smoke_failed"},
                "graph_status": graph.get("status"),
                "smoke": {
                    "smoke_pass": False,
                    "issues": smoke_report.get("issues") or [],
                    "node_results": smoke_report.get("node_results") or [],
                    "blocked": smoke_report.get("blocked"),
                },
                "nodes": len(nodes),
            }
            print(json.dumps(result, indent=2, default=str))
            return 1

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
    if smoke_report is not None:
        result["smoke"] = {
            "smoke_pass": smoke_report.get("smoke_pass"),
            "issues": smoke_report.get("issues") or [],
        }
    elif graph.get("smoke_pass"):
        result["smoke"] = {"smoke_pass": True, "skipped": "already_smoked"}
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
    p_compile.add_argument(
        "--include-external",
        default="",
        help=(
            "Comma-separated promoted external asset ids "
            "(from external/promoted/; trust=external; never clones)"
        ),
    )

    p_fd = sub.add_parser(
        "from-deconstruct",
        help=(
            "Bridge saved deconstruct.v0 → draft graph.v1 "
            "(never smoke_pass; use smoke subcommand separately)"
        ),
    )
    p_fd.add_argument("--id", required=True, help="deconstruct id under deconstructs/")
    p_fd.add_argument(
        "--goal-id",
        default="",
        help="graph goal_id (default: deconstruct id)",
    )
    p_fd.add_argument(
        "--text",
        default="",
        help="Optional goal text (default: deconstruct target)",
    )
    p_fd.add_argument("--max-nodes", type=int, default=0)

    p_plan = sub.add_parser(
        "plan-factories",
        help="Load graph; enqueue missing MCPs; log software handoffs",
    )
    p_plan.add_argument("--goal-id", required=True)

    p_smoke = sub.add_parser(
        "smoke",
        help="Whole-graph cheap smoke after nodes resolved (P3); exit 0/1",
    )
    p_smoke.add_argument("--goal-id", required=True)

    p_attempt = sub.add_parser(
        "attempt",
        help="Compile if missing; smoke if needed; classify + execute_policy",
    )
    p_attempt.add_argument("--goal-id", required=True)
    p_attempt.add_argument("--text", required=True, help="Goal / branch text")
    p_attempt.add_argument(
        "--hits-json",
        default="",
        help="Optional route hits when compiling missing graph",
    )

    p_fix = sub.add_parser(
        "fixture-mcps",
        help="Compile graph from smoked MCPs under PIPELINE_DIR/mcps/ (map-blocks fixture)",
    )
    p_fix.add_argument("--goal-id", default="utility_mcp_fixture")
    p_fix.add_argument(
        "--text",
        default="",
        help="Optional goal text (default describes utility MCP workflow)",
    )
    p_fix.add_argument(
        "--slugs",
        default="",
        help="Comma-separated mcp slugs (default: all smoked)",
    )
    p_fix.add_argument("--max-nodes", type=int, default=10)

    args = ap.parse_args(argv)
    _bind_pipeline_dir(args.pipeline_dir)

    if args.cmd == "compile":
        return cmd_compile(args)
    if args.cmd == "from-deconstruct":
        return cmd_from_deconstruct(args)
    if args.cmd == "plan-factories":
        return cmd_plan_factories(args)
    if args.cmd == "smoke":
        return cmd_smoke(args)
    if args.cmd == "attempt":
        return cmd_attempt(args)
    if args.cmd == "fixture-mcps":
        return cmd_fixture_mcps(args)
    ap.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
