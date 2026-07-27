#!/usr/bin/env python3
"""
Block registry CLI v0 — skill/prompt catalog, sockets, sandbox → promote.

Usage:
  python scripts/block_registry.py register-skill --name create-skill
  python scripts/block_registry.py register-prompt --path pipeline/prompts/executor.md --name executor
  python scripts/block_registry.py sandbox --id skill_create-skill
  python scripts/block_registry.py promote --id skill_create-skill
  python scripts/block_registry.py attach --socket executor.pre_task_skills --id skill_create-skill
  python scripts/block_registry.py detach --socket executor.pre_task_skills --id skill_create-skill
  python scripts/block_registry.py list-blocks
  python scripts/block_registry.py list-sockets
  python scripts/block_registry.py resolve --socket executor.pre_task_skills
  python scripts/block_registry.py revoke --id skill_create-skill

Env:
  PIPELINE_DIR  — factory output root (state/block_registry/ lives here)
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Block registry v0: skill/prompt blocks + role sockets + promote"
    )
    ap.add_argument("--pipeline-dir", default="", help="Override PIPELINE_DIR")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_rs = sub.add_parser("register-skill", help="Register draft skill block via skill_load")
    p_rs.add_argument("--name", required=True, help="Skill name (e.g. create-skill)")
    p_rs.add_argument("--force", action="store_true", help="Overwrite existing draft record")
    p_rs.add_argument("--risk", default="low", choices=["low", "medium", "high"])
    p_rs.add_argument(
        "--sandbox",
        action="store_true",
        help="Run static sandbox immediately after register (habit convenience)",
    )

    p_rp = sub.add_parser("register-prompt", help="Register draft prompt block from markdown file")
    p_rp.add_argument("--path", required=True, help="Path to prompt .md")
    p_rp.add_argument("--name", required=True, help="Block name")
    p_rp.add_argument("--force", action="store_true")
    p_rp.add_argument("--risk", default="low", choices=["low", "medium", "high"])
    p_rp.add_argument(
        "--sandbox",
        action="store_true",
        help="Run static sandbox immediately after register (habit convenience)",
    )

    p_sb = sub.add_parser("sandbox", help="Static sandbox checks → sandboxed if pass")
    p_sb.add_argument("--id", required=True, help="Block id")

    p_pr = sub.add_parser("promote", help="Promote sandboxed → verified")
    p_pr.add_argument("--id", required=True, help="Block id")
    p_pr.add_argument("--notes", default="", help="Promote notes")
    p_pr.add_argument(
        "--sandbox-if-needed",
        action="store_true",
        help="Run sandbox first if still draft",
    )

    p_rv = sub.add_parser("revoke", help="Revoke block and detach from sockets")
    p_rv.add_argument("--id", required=True)
    p_rv.add_argument("--no-detach", action="store_true", help="Leave socket attachments")

    p_at = sub.add_parser("attach", help="Attach block to socket")
    p_at.add_argument("--socket", required=True)
    p_at.add_argument("--id", required=True, help="Block id")
    p_at.add_argument(
        "--force",
        action="store_true",
        help=(
            "Break-glass: attach even if status not allowed. "
            "resolve/load still skip non-allowed statuses; after a later promote "
            "the body becomes injectable without re-attach. Prefer not to use."
        ),
    )

    p_dt = sub.add_parser("detach", help="Detach block from socket (or clear socket)")
    p_dt.add_argument("--socket", required=True)
    p_dt.add_argument("--id", default="", help="Block id; omit to clear all")

    p_lb = sub.add_parser("list-blocks", help="List registered blocks")
    p_lb.add_argument("--kind", default="", help="Filter skill|prompt")
    p_lb.add_argument("--status", default="", help="Filter draft|sandboxed|verified|revoked")

    sub.add_parser("list-sockets", help="List sockets and attachments")

    p_re = sub.add_parser("resolve", help="Resolve socket → bodies (allowed statuses only)")
    p_re.add_argument("--socket", required=True)
    p_re.add_argument(
        "--bodies",
        action="store_true",
        help="Print concatenated bodies instead of JSON metadata",
    )

    args = ap.parse_args(argv)
    _bind_pipeline_dir(args.pipeline_dir)

    from pipeline import block_registry as br

    try:
        if args.cmd == "register-skill":
            rec = br.register_block_from_skill(
                args.name,
                force=bool(args.force),
                risk_class=args.risk,
                sandbox=bool(args.sandbox),
            )
            _print_json(rec)
            if args.sandbox and not (rec.get("sandbox_report") or {}).get("pass"):
                return 1
            return 0

        if args.cmd == "register-prompt":
            rec = br.register_block_from_prompt_file(
                args.path,
                args.name,
                force=bool(args.force),
                risk_class=args.risk,
                sandbox=bool(args.sandbox),
            )
            _print_json(rec)
            if args.sandbox and not (rec.get("sandbox_report") or {}).get("pass"):
                return 1
            return 0

        if args.cmd == "sandbox":
            rec = br.sandbox_block(args.id)
            _print_json(rec)
            return 0 if (rec.get("sandbox_report") or {}).get("pass") else 1

        if args.cmd == "promote":
            rec = br.promote_block(
                args.id,
                notes=args.notes or "",
                sandbox_if_needed=bool(args.sandbox_if_needed),
            )
            _print_json(rec)
            return 0

        if args.cmd == "revoke":
            rec = br.revoke_block(args.id, detach=not bool(args.no_detach))
            _print_json(rec)
            return 0

        if args.cmd == "attach":
            sock = br.attach_block(args.socket, args.id, force=bool(args.force))
            _print_json(sock)
            return 0

        if args.cmd == "detach":
            sock = br.detach_block(args.socket, args.id or None)
            _print_json(sock)
            return 0

        if args.cmd == "list-blocks":
            rows = br.list_blocks(
                kind=args.kind or None,
                status=args.status or None,
            )
            slim = [
                {
                    "id": r.get("id"),
                    "kind": r.get("kind"),
                    "name": r.get("name"),
                    "status": r.get("status"),
                    "source_path": r.get("source_path"),
                    "provenance": r.get("provenance"),
                }
                for r in rows
            ]
            _print_json(slim)
            return 0

        if args.cmd == "list-sockets":
            # strict_sockets=True: corrupt sockets.json raises after quarantine
            _print_json(br.list_sockets(strict_sockets=True))
            return 0

        if args.cmd == "resolve":
            if args.bodies:
                print(br.load_socket_skill_bodies(args.socket))
            else:
                items = br.resolve_socket_skills(args.socket)
                # omit full body in default JSON for readability
                slim = [
                    {
                        "block_id": i.get("block_id"),
                        "name": i.get("name"),
                        "kind": i.get("kind"),
                        "status": i.get("status"),
                        "path": i.get("path"),
                        "body_len": len(i.get("body") or ""),
                    }
                    for i in items
                ]
                _print_json(slim)
            return 0

    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"unknown cmd: {args.cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
