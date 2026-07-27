#!/usr/bin/env python3
"""
Thin graph engineer CLI — author/revise draft graph.v1; finalize only via smoke_graph.

Usage:
  python scripts/graph_engineer.py author --goal-id ID --text "..." [--hits-json file]
  python scripts/graph_engineer.py author --goal-id ID --from-deconstruct DECONSTRUCT_ID
  python scripts/graph_engineer.py revise --goal-id ID [--patches-json file]
  python scripts/graph_engineer.py finalize --goal-id ID [--write-trace]
  python scripts/graph_engineer.py import-success-model [--fixture path] [--goal-id ID]
       [--no-smoke] [--write-trace]

Rules:
  - author/revise never set smoke_pass or field_proven (status draft|critiqued|blocked)
  - finalize must call smoke_graph (fail-closed on smoke fail)
  - Non-goals: trust/funds/captcha, RSI primary, nest-system-as-only-tool, unattended external pull

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


def _load_patches(path: str | None) -> list[dict] | None:
    if not path:
        return None
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("patches"), list):
        return data["patches"]
    raise SystemExit(f"patches-json must be a list or {{patches: [...]}}: {path}")


def _print(result: dict) -> None:
    # Drop full graph body by default? Keep it for operators (matches goal_compose).
    print(json.dumps(result, indent=2, default=str))


def cmd_author(args: argparse.Namespace) -> int:
    from pipeline.graph_engineer import engineer_author

    try:
        if args.from_deconstruct:
            result = engineer_author(
                goal_id=args.goal_id,
                goal_text=args.text or "",
                deconstruct_id=args.from_deconstruct,
                max_nodes=args.max_nodes or None,
                save=True,
            )
        else:
            hits = _load_hits(args.hits_json)
            result = engineer_author(
                goal_id=args.goal_id,
                goal_text=args.text or "",
                route_hits=hits,
                max_nodes=args.max_nodes or None,
                save=True,
            )
    except (FileNotFoundError, ValueError, TypeError) as exc:
        _print({"error": str(exc), "ok": False})
        return 1

    # Never smoke_pass from author alone
    if result.get("smoke_pass"):
        _print(
            {
                "error": "internal: author claimed smoke_pass",
                "ok": False,
                "result": result,
            }
        )
        return 1
    _print(result)
    status = str(result.get("status") or "")
    if status == "blocked":
        return 1
    return 0


def cmd_revise(args: argparse.Namespace) -> int:
    from pipeline.graph_engineer import engineer_revise

    try:
        result = engineer_revise(
            args.goal_id,
            node_patches=_load_patches(args.patches_json),
            goal_text=args.text or None,
            save=True,
        )
    except (FileNotFoundError, ValueError, TypeError) as exc:
        _print({"error": str(exc), "ok": False})
        return 1

    if result.get("smoke_pass"):
        _print(
            {
                "error": "internal: revise claimed smoke_pass",
                "ok": False,
                "result": result,
            }
        )
        return 1
    _print(result)
    return 0 if result.get("ok") else 1


def cmd_finalize(args: argparse.Namespace) -> int:
    from pipeline.graph_engineer import engineer_finalize

    try:
        result = engineer_finalize(
            args.goal_id,
            save=True,
            write_trace=bool(args.write_trace),
        )
    except (FileNotFoundError, ValueError, TypeError) as exc:
        _print({"error": str(exc), "ok": False})
        return 1

    if result.get("refused"):
        _print(result)
        return 1
    _print(result)
    # Fail-closed: exit 1 when smoke fails
    return 0 if result.get("smoke_pass") else 1


def cmd_import_success_model(args: argparse.Namespace) -> int:
    from pipeline.graph_engineer import import_success_model

    fixture = (args.fixture or "").strip() or None
    try:
        result = import_success_model(
            fixture,
            goal_id=(args.goal_id or "").strip() or None,
            prepare_stubs=not args.no_stubs,
            smoke=not args.no_smoke,
            write_trace=bool(args.write_trace),
            save=True,
        )
    except (FileNotFoundError, ValueError, TypeError, json.JSONDecodeError) as exc:
        _print({"error": str(exc), "ok": False})
        return 1

    _print(result)
    return 0 if result.get("ok") else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Thin graph engineer: draft author/revise via gates; "
            "finalize only via smoke_graph (fail-closed)"
        )
    )
    ap.add_argument("--pipeline-dir", default="", help="Override PIPELINE_DIR")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_auth = sub.add_parser(
        "author",
        help="Author draft graph.v1 (never smoke_pass); via hits or deconstruct",
    )
    p_auth.add_argument("--goal-id", required=True)
    p_auth.add_argument("--text", default="", help="Goal text")
    p_auth.add_argument("--hits-json", default="", help="Route hits JSON file")
    p_auth.add_argument(
        "--from-deconstruct",
        default="",
        help="deconstruct id under deconstructs/ (draft bridge)",
    )
    p_auth.add_argument("--max-nodes", type=int, default=0)

    p_rev = sub.add_parser(
        "revise",
        help="Revise graph + re-critique; strip smoke claims; status draft|critiqued|blocked",
    )
    p_rev.add_argument("--goal-id", required=True)
    p_rev.add_argument(
        "--patches-json",
        default="",
        help="Node patches list [{id|slug, status?, oracle?, label?}]",
    )
    p_rev.add_argument("--text", default="", help="Optional new goal_text")

    p_fin = sub.add_parser(
        "finalize",
        help=(
            "Claim smoke_pass only via smoke_graph (fail-closed). "
            "Never sets field_proven."
        ),
    )
    p_fin.add_argument("--goal-id", required=True)
    p_fin.add_argument(
        "--write-trace",
        action="store_true",
        help="Write optional goal_trace.v1 (presence smoke ≠ goal proven)",
    )

    p_imp = sub.add_parser(
        "import-success-model",
        help="Import success-model inventory fixture → critique → smoke (stubs)",
    )
    p_imp.add_argument(
        "--fixture",
        default="",
        help="Path to graph.v1 JSON (default: tests/fixtures/success_model_inventory.json)",
    )
    p_imp.add_argument("--goal-id", default="", help="Override goal_id")
    p_imp.add_argument(
        "--no-smoke",
        action="store_true",
        help="Import + critique only (no smoke_graph)",
    )
    p_imp.add_argument(
        "--no-stubs",
        action="store_true",
        help="Do not create workflow project/connector stubs under PIPELINE_DIR",
    )
    p_imp.add_argument(
        "--write-trace",
        action="store_true",
        help="Write optional goal_trace.v1 for the import",
    )

    args = ap.parse_args(argv)
    _bind_pipeline_dir(args.pipeline_dir)

    if args.cmd == "author":
        return cmd_author(args)
    if args.cmd == "revise":
        return cmd_revise(args)
    if args.cmd == "finalize":
        return cmd_finalize(args)
    if args.cmd == "import-success-model":
        return cmd_import_success_model(args)
    ap.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
