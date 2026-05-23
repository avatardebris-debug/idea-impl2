#!/usr/bin/env python3
"""
Phase 8 preview: minimal stdio capability server for external agents.

One JSON object per line on stdin; one JSON response per line on stdout.

Example:
  echo '{"method":"list_capabilities","params":{"limit":5}}' | python scripts/mcp_capability_server.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.pipeline_mode import set_legacy_mode  # noqa: E402

set_legacy_mode(False)


def _handle(req: dict) -> dict:
    method = req.get("method", "")
    params = req.get("params") or {}
    if not isinstance(params, dict):
        params = {}

    try:
        if method == "list_capabilities":
            from pipeline.capability_tools import list_capabilities

            text = list_capabilities(
                domain=params.get("domain", ""),
                status=params.get("status", "verified"),
                limit=int(params.get("limit", 15)),
            )
            return {"ok": True, "result": text}

        if method == "describe_capability":
            from pipeline.capability_tools import describe_capability

            slug = params.get("slug", "")
            return {"ok": True, "result": describe_capability(slug)}

        if method == "suggest_capabilities":
            from pipeline.capability_tools import suggest_capabilities

            return {
                "ok": True,
                "result": suggest_capabilities(
                    params.get("task", ""),
                    limit=int(params.get("limit", 5)),
                ),
            }

        if method == "invoke_capability":
            from pipeline.capability_tools import invoke_capability

            return {
                "ok": True,
                "result": invoke_capability(
                    params.get("slug", ""),
                    params.get("args", ""),
                    params.get("cwd", ""),
                ),
            }

        if method == "ping":
            return {"ok": True, "result": "capability-mcp-ok"}

        return {"ok": False, "error": f"unknown method: {method}"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError as exc:
            sys.stdout.write(json.dumps({"ok": False, "error": str(exc)}) + "\n")
            sys.stdout.flush()
            continue
        resp = _handle(req)
        sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
