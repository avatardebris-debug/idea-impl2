"""
pipeline/capability_tools.py
Agent tools for capability registry (Phase 4). Merged into agent loop when not --legacy.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

from pipeline.capability_registry import PROJECT_ROOT, _connect
from pipeline.paths import registry_db
from pipeline.capability_router import route_task
from pipeline.pipeline_mode import legacy_mode

# Whitelisted command prefixes for invoke_capability (incl. Windows)
def _allowed_prefixes() -> tuple[str, ...]:
    exe = Path(sys.executable).name.lower()
    prefixes = [
        "python ",
        "python3 ",
        "py ",
        "py.exe ",
    ]
    # Full path to current interpreter (quoted or unquoted)
    try:
        full = str(Path(sys.executable).resolve())
        prefixes.append(full + " ")
        if " " in full:
            prefixes.append(f'"{full}" ')
    except Exception:
        pass
    if exe and not exe.startswith("python"):
        prefixes.append(exe + " ")
    return tuple(prefixes)


_ALLOWED_PREFIXES = _allowed_prefixes()


def _get_capability(slug: str) -> dict[str, Any] | None:
    if not registry_db().exists():
        return None
    conn = _connect()
    row = conn.execute(
        """
        SELECT slug, title, kind, status, purpose, entrypoint, example_invoke,
               cwd_template, requires
        FROM capabilities WHERE slug = ?
        """,
        (slug,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_capabilities(domain: str = "", status: str = "verified", limit: int = 15) -> str:
    if legacy_mode():
        return "Capability tools disabled (runner started with --legacy)."
    from pipeline.capability_registry import list_capabilities as _list

    rows = _list(domain=domain or None, status=status or None)
    if not rows:
        return "No matching capabilities in registry."
    lines = [f"Capabilities ({len(rows)} shown, max {limit}):"]
    for r in rows[:limit]:
        ep = r.get("entrypoint") or "(no entrypoint)"
        lines.append(f"  - {r['slug']}: {r['title']} [{r['kind']}] — {ep}")
    return "\n".join(lines)


def describe_capability(slug: str) -> str:
    if legacy_mode():
        return "Capability tools disabled (--legacy)."
    row = _get_capability(slug)
    if not row:
        return f"ERROR: Unknown capability slug '{slug}'"
    parts = [
        f"slug: {row['slug']}",
        f"title: {row['title']}",
        f"kind: {row['kind']}",
        f"status: {row['status']}",
        f"purpose: {row['purpose']}",
        f"entrypoint: {row['entrypoint'] or '(none)'}",
        f"example: {row['example_invoke'] or '(none)'}",
        f"cwd: {row['cwd_template'] or PROJECT_ROOT}",
        f"requires: {row['requires']}",
    ]
    suggestions = route_task(row["purpose"] or slug, limit=3)
    if suggestions:
        parts.append("related: " + ", ".join(s["slug"] for s in suggestions))
    return "\n".join(parts)


def suggest_capabilities(task: str, limit: int = 5) -> str:
    if legacy_mode():
        return "Capability tools disabled (--legacy)."
    from pipeline.capability_router import format_suggestions

    hits = route_task(task, limit=limit)
    if not hits:
        return "No strong capability matches. Consider building new or use list_capabilities."
    try:
        from pipeline.capability_metrics import log_capability_event

        for h in hits[:limit]:
            log_capability_event("suggest", h.get("slug", ""), ok=h.get("requires_ok"))
    except Exception:
        pass
    return format_suggestions(hits)


def invoke_capability(slug: str, args: str = "", cwd: str = "") -> str:
    if legacy_mode():
        return "ERROR: invoke_capability disabled (--legacy). Use run_shell or build new code."

    row = _get_capability(slug)
    if not row:
        return f"ERROR: Unknown capability '{slug}'"
    if row["status"] != "verified" and row["kind"] not in ("workflow", "connector"):
        return f"ERROR: Capability '{slug}' is not verified (status={row['status']})"

    if row["kind"] in ("workflow", "connector"):
        from pipeline.workflow_runner import format_workflow_result_for_agent, run_workflow

        result = run_workflow(slug, args=args)
        return format_workflow_result_for_agent(result)

    from pipeline.capability_graph import missing_requires

    blocked = missing_requires(slug)
    if blocked:
        return (
            f"ERROR: Capability '{slug}' is blocked — prerequisites not verified: "
            f"{', '.join(blocked)}"
        )

    entry = (row["entrypoint"] or "").strip()
    if not entry:
        return f"ERROR: Capability '{slug}' has no entrypoint"

    entry_norm = entry.strip()
    entry_lower = entry_norm.lower()
    allowed = _allowed_prefixes()
    # Case-insensitive prefix match (Windows paths vary)
    if not any(entry_lower.startswith(p.lower()) for p in allowed):
        return f"ERROR: Entrypoint not allowed for invoke_capability: {entry}"

    # Block shell metacharacters in user args
    if args and re.search(r"[;&|`$<>]", args):
        return "ERROR: args contain disallowed shell characters"

    cmd = entry
    if args:
        cmd = f"{entry} {args}"

    work_dir = PROJECT_ROOT
    if cwd:
        work_dir = (PROJECT_ROOT / cwd).resolve()
    elif row["cwd_template"]:
        work_dir = (PROJECT_ROOT / row["cwd_template"]).resolve()

    try:
        work_dir.relative_to(PROJECT_ROOT.resolve())
    except ValueError:
        return "ERROR: cwd must stay inside project root"

    try:
        argv = shlex.split(cmd, posix=False)
    except ValueError as e:
        return f"ERROR: cannot parse command: {e}"

    try:
        result = subprocess.run(
            argv,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
        )
        out = (result.stdout or "") + (result.stderr or "")
        if len(out) > 4000:
            out = out[:4000] + "\n...(truncated)"
        ok = result.returncode == 0
        try:
            from pipeline.capability_metrics import log_capability_event

            log_capability_event("invoke", slug, ok=ok, detail=f"exit={result.returncode}")
        except Exception:
            pass
        prefix = f"OK (exit {result.returncode}): " if ok else f"FAIL (exit {result.returncode}): "
        return prefix + (out or "(no output)")
    except subprocess.TimeoutExpired:
        return "ERROR: invoke_capability timed out after 120s"
    except Exception as e:
        return f"ERROR: {e}"


CAPABILITY_TOOL_SCHEMAS = [
    {
        "name": "list_capabilities",
        "description": "List verified capabilities from the pipeline registry (reuse before building).",
        "parameters": {
            "type": "object",
            "properties": {
                "domain": {"type": "string", "description": "Optional domain filter: robotics, video, finance, ..."},
                "limit": {"type": "integer", "description": "Max rows (default 15)."},
            },
        },
    },
    {
        "name": "describe_capability",
        "description": "Get full details for one capability slug from the registry.",
        "parameters": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Capability slug, e.g. json_diff_tool"},
            },
            "required": ["slug"],
        },
    },
    {
        "name": "suggest_capabilities",
        "description": "Rank registry capabilities that may already solve this task.",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "What you need to accomplish."},
                "limit": {"type": "integer", "description": "Max suggestions (default 5)."},
            },
            "required": ["task"],
        },
    },
    {
        "name": "invoke_capability",
        "description": "Run a verified capability's registered entrypoint (safe whitelist). Prefer over raw run_shell for known tools.",
        "parameters": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Registry slug"},
                "args": {"type": "string", "description": "Extra CLI args appended to entrypoint"},
                "cwd": {"type": "string", "description": "Optional cwd relative to repo root"},
            },
            "required": ["slug"],
        },
    },
]

CAPABILITY_TOOLS: dict[str, object] = {
    "list_capabilities": list_capabilities,
    "describe_capability": describe_capability,
    "suggest_capabilities": suggest_capabilities,
    "invoke_capability": invoke_capability,
}
