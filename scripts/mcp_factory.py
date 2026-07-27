#!/usr/bin/env python3
"""
MCP factory CLI v0 — wrap verified capabilities as stdio JSONL MCP servers.

Usage:
  python scripts/mcp_factory.py wrap --slug CAP
  python scripts/mcp_factory.py smoke --mcp-slug mcp_CAP
  python scripts/mcp_factory.py drain-queue --limit 1
  python scripts/mcp_factory.py list

Env:
  PIPELINE_DIR  — factory output root (mcps/ lives here)
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


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="MCP factory v0: wrap capability → stdio JSONL server + smoke"
    )
    ap.add_argument("--pipeline-dir", default="", help="Override PIPELINE_DIR")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_wrap = sub.add_parser("wrap", help="Scaffold mcps/mcp_{slug}/server.py + manifest")
    p_wrap.add_argument("--slug", required=True, help="Capability slug to wrap")
    p_wrap.add_argument("--entrypoint", default="", help="Optional entrypoint override (manifest only)")
    p_wrap.add_argument("--cwd", default="", help="Optional cwd override (manifest only)")
    p_wrap.add_argument("--force", action="store_true", help="Overwrite existing scaffold")
    p_wrap.add_argument("--register", action="store_true", help="Also best-effort registry insert")

    p_smoke = sub.add_parser(
        "smoke",
        help="Spawn server; ping + describe (+ optional invoke oracle)",
    )
    p_smoke.add_argument("--mcp-slug", required=True, help="MCP slug (mcp_CAP)")
    p_smoke.add_argument("--timeout", type=float, default=15.0, help="Smoke timeout seconds")
    p_smoke.add_argument("--register", action="store_true", help="Register after successful smoke")
    p_smoke.set_defaults(require_invoke=True)
    p_smoke.add_argument(
        "--require-invoke",
        dest="require_invoke",
        action="store_true",
        help="Require invoke oracle (default)",
    )
    p_smoke.add_argument(
        "--no-require-invoke",
        dest="require_invoke",
        action="store_false",
        help="Only ping + describe (legacy soft smoke)",
    )
    p_smoke.add_argument(
        "--invoke-args",
        default="--help",
        help="Args for invoke oracle (default: --help)",
    )
    p_smoke.add_argument(
        "--skip-if-smoked",
        action="store_true",
        help="No-op success if already smoked (unless --force-resmoke)",
    )
    p_smoke.add_argument(
        "--force-resmoke",
        action="store_true",
        help="Re-run smoke even if already smoked",
    )

    p_drain = sub.add_parser("drain-queue", help="Process pending mcp_factory jobs")
    p_drain.add_argument("--limit", type=int, default=1, help="Max jobs to process")
    p_drain.add_argument(
        "--no-require-invoke",
        action="store_true",
        help="Soft smoke only (ping+describe) when wrapping new MCPs",
    )
    p_drain.add_argument(
        "--no-skip-smoked",
        action="store_true",
        help="Re-wrap/smoke even if already smoked",
    )
    p_drain.add_argument("--invoke-args", default="--help", help="Invoke oracle args")

    sub.add_parser("list", help="List MCP manifests under mcps/")

    args = ap.parse_args(argv)
    _bind_pipeline_dir(args.pipeline_dir)

    from pipeline import mcp_factory as mf

    if args.cmd == "wrap":
        manifest = mf.wrap_capability_as_mcp(
            args.slug,
            entrypoint=args.entrypoint or None,
            cwd=args.cwd or None,
            force=bool(args.force),
        )
        if args.register:
            mf.register_mcp(manifest)
            # reload after note annotation
            man2 = mf._load_manifest(manifest["mcp_slug"])  # noqa: SLF001
            if man2:
                manifest = man2
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0

    if args.cmd == "smoke":
        report = mf.smoke_mcp(
            args.mcp_slug,
            timeout_s=float(args.timeout),
            require_invoke=bool(args.require_invoke),
            invoke_args=str(args.invoke_args or "--help"),
            skip_if_smoked=bool(args.skip_if_smoked),
            force=bool(args.force_resmoke),
        )
        if args.register and report.get("ok") and not report.get("skipped"):
            man = mf._load_manifest(args.mcp_slug)  # noqa: SLF001
            if man:
                mf.register_mcp(man)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report.get("ok") else 1

    if args.cmd == "drain-queue":
        results = mf.drain_queue(
            limit=int(args.limit),
            require_invoke=not bool(args.no_require_invoke),
            invoke_args=str(args.invoke_args or "--help"),
            skip_if_smoked=not bool(args.no_skip_smoked),
        )
        print(json.dumps(results, indent=2, ensure_ascii=False))
        if not results:
            return 0
        return 0 if all(r.get("ok") for r in results) else 1

    if args.cmd == "list":
        rows = mf.list_mcps()
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return 0

    ap.error(f"unknown command: {args.cmd}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
