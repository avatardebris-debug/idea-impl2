#!/usr/bin/env python3
"""
External ingest CLI v1 — pin → scan → approve/reject → promote (manual human gate).

Usage:
  python scripts/external_ingest.py pin --path ./fixture-skill --kind skill [--id my-skill]
  python scripts/external_ingest.py scan --id skill_fixture-skill
  python scripts/external_ingest.py approve --id skill_fixture-skill [--notes "..."]
  python scripts/external_ingest.py reject --id skill_fixture-skill --reason "..."
  python scripts/external_ingest.py promote --id skill_fixture-skill
  python scripts/external_ingest.py list
  python scripts/external_ingest.py show --id skill_fixture-skill

Env:
  PIPELINE_DIR              — factory output root (external/ lives here)
  EXTERNAL_INGEST_ACTOR     — optional actor name for approve/reject audit

Out of scope: unattended GitHub search/auto-pull (no live clone in library path).
Promote is blocked without prior approve.
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
        description=(
            "External ingest v1: pin (local path) → scan → human approve → promote. "
            "No unattended auto-pull."
        )
    )
    ap.add_argument("--pipeline-dir", default="", help="Override PIPELINE_DIR")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_pin = sub.add_parser(
        "pin",
        help="Snapshot local path/dir into quarantine (no live git required)",
    )
    p_pin.add_argument(
        "--path",
        required=True,
        help="Local file or directory (fixture skill/software/mcp tree)",
    )
    p_pin.add_argument(
        "--kind",
        required=True,
        choices=["skill", "software", "mcp", "external_mcp"],
    )
    p_pin.add_argument("--id", default="", help="Asset id (default: kind_sourcename)")
    p_pin.add_argument("--force", action="store_true", help="Re-pin overwrite same id")
    p_pin.add_argument("--license-note", default="", help="Optional license note")
    p_pin.add_argument(
        "--risk",
        default="medium",
        choices=["low", "medium", "high"],
        help="Risk class (default medium)",
    )
    p_pin.add_argument(
        "--commit-sha",
        default="",
        help="Optional commit SHA to record in pin (when known from offline pin)",
    )
    p_pin.add_argument(
        "--source-url",
        default="",
        help="Optional provenance URL label (does not fetch)",
    )
    p_pin.add_argument(
        "--allow-url",
        action="store_true",
        help=(
            "Reserved: live URL fetch is NOT implemented. "
            "Flag accepted only to document default-off network path; pin still requires --path."
        ),
    )

    p_scan = sub.add_parser("scan", help="Static scan quarantined payload")
    p_scan.add_argument("--id", required=True, help="Asset id")

    p_ap = sub.add_parser("approve", help="Human approve (required before promote)")
    p_ap.add_argument("--id", required=True)
    p_ap.add_argument("--notes", default="")
    p_ap.add_argument(
        "--actor",
        default="",
        help="Override actor (default EXTERNAL_INGEST_ACTOR / USER / USERNAME)",
    )

    p_rj = sub.add_parser("reject", help="Human reject")
    p_rj.add_argument("--id", required=True)
    p_rj.add_argument("--reason", default="rejected")
    p_rj.add_argument("--actor", default="")

    p_pr = sub.add_parser(
        "promote",
        help="Promote approved → external_* draft (blocked without approve)",
    )
    p_pr.add_argument("--id", required=True)
    p_pr.add_argument("--notes", default="")

    p_rv = sub.add_parser("revoke", help="Revoke asset / promoted draft")
    p_rv.add_argument("--id", required=True)
    p_rv.add_argument("--reason", default="")

    p_ls = sub.add_parser("list", help="List external assets")
    p_ls.add_argument("--kind", default="", help="Filter kind")
    p_ls.add_argument("--status", default="", help="Filter status")

    p_sh = sub.add_parser("show", help="Show asset + scan report")
    p_sh.add_argument("--id", required=True)

    args = ap.parse_args(argv)
    _bind_pipeline_dir(args.pipeline_dir)

    from pipeline import external_ingest as ei

    try:
        if args.cmd == "pin":
            # --path is always required; --allow-url is reserved (no live fetch).
            if args.allow_url:
                print(
                    "warning: --allow-url is accepted but live fetch is not implemented; "
                    "using local --path only",
                    file=sys.stderr,
                )
            rec = ei.pin_asset(
                args.path,
                kind=args.kind,
                asset_id=args.id or None,
                force=bool(args.force),
                license_note=args.license_note,
                risk_class=args.risk,
                commit_sha=args.commit_sha or None,
                source_url=args.source_url or None,
            )
            _print_json(rec)
            return 0

        if args.cmd == "scan":
            rec = ei.scan_asset(args.id)
            _print_json(rec)
            report = rec.get("scan_report") or {}
            return 0 if report.get("pass") else 1

        if args.cmd == "approve":
            rec = ei.approve_asset(
                args.id,
                notes=args.notes,
                actor=args.actor or None,
            )
            _print_json(rec)
            return 0

        if args.cmd == "reject":
            rec = ei.reject_asset(
                args.id,
                reason=args.reason,
                actor=args.actor or None,
            )
            _print_json(rec)
            return 0

        if args.cmd == "promote":
            rec = ei.promote_asset(args.id, notes=args.notes)
            _print_json(rec)
            return 0

        if args.cmd == "revoke":
            rec = ei.revoke_asset(args.id, reason=args.reason)
            _print_json(rec)
            return 0

        if args.cmd == "list":
            rows = ei.list_assets(
                kind=args.kind or None,
                status=args.status or None,
            )
            slim = [
                {
                    "id": r.get("id"),
                    "kind": r.get("kind"),
                    "status": r.get("status"),
                    "risk_class": r.get("risk_class"),
                    "source_url_or_path": r.get("source_url_or_path"),
                    "pin": r.get("pin"),
                }
                for r in rows
            ]
            _print_json(slim)
            return 0

        if args.cmd == "show":
            _print_json(ei.show_asset(args.id))
            return 0

    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"error: unknown command {args.cmd!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
