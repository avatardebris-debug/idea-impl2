#!/usr/bin/env python3
"""
Cursor MCP server for the idea-impl capability registry (Phase 8).

Setup (project .cursor/mcp.json is included):
  pip install mcp>=1.2.0
  Reload MCP in Cursor: Settings → Tools & MCP

Tools: list_capabilities, describe_capability, suggest_capabilities, invoke_capability
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("PIPELINE_LEGACY", "0")

from pipeline.pipeline_mode import set_legacy_mode  # noqa: E402

set_legacy_mode(False)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print(
        "ERROR: MCP SDK not installed. Run: pip install mcp>=1.2.0",
        file=sys.stderr,
    )
    print(
        "Fallback: scripts/mcp_capability_server.py (line-delimited JSON)",
        file=sys.stderr,
    )
    raise SystemExit(1) from None

mcp = FastMCP(
    "idea-capabilities",
    instructions=(
        "Pipeline capability registry for the idea-impl monorepo. "
        "Prefer suggest_capabilities before building new tools; use invoke_capability "
        "for verified entrypoints only. Blocked tools have unmet requires: dependencies."
    ),
)


@mcp.tool()
def list_capabilities(domain: str = "", status: str = "verified", limit: int = 15) -> str:
    """List capabilities from the SQLite registry."""
    from pipeline.capability_tools import list_capabilities as _list

    return _list(domain=domain, status=status, limit=limit)


@mcp.tool()
def describe_capability(slug: str) -> str:
    """Full metadata for one capability slug (requires, entrypoint, purpose)."""
    from pipeline.capability_tools import describe_capability as _desc

    return _desc(slug)


@mcp.tool()
def suggest_capabilities(task: str, limit: int = 5) -> str:
    """Rank registry capabilities for a natural-language task (respects dependency graph)."""
    from pipeline.capability_tools import suggest_capabilities as _suggest

    return _suggest(task, limit=limit)


@mcp.tool()
def invoke_capability(slug: str, args: str = "", cwd: str = "") -> str:
    """Run a verified capability CLI entrypoint (whitelist: python/python3 only)."""
    from pipeline.capability_tools import invoke_capability as _invoke

    return _invoke(slug, args=args, cwd=cwd)


@mcp.tool()
def registry_blocked_ideas(limit: int = 20) -> str:
    """List master_ideas.md entries blocked by unmet requires: prerequisites."""
    from pipeline.capability_graph import blocked_unchecked_ideas

    blocked = blocked_unchecked_ideas()
    if not blocked:
        return "No blocked unchecked ideas in master_ideas.md."
    lines = [f"Blocked downstream ({len(blocked)}):"]
    for b in blocked[:limit]:
        miss = ", ".join(b["missing"])
        lines.append(f"  - {b['slug']}: needs verified [{miss}]")
    if len(blocked) > limit:
        lines.append(f"  ... +{len(blocked) - limit} more")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="stdio")
