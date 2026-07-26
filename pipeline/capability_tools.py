"""
pipeline/capability_tools.py
Agent tools for capability registry (Phase 4). Merged into agent loop when not --legacy.

Workdirs and entrypoints resolve under PIPELINE_DIR (live projects) first, not only
factory PROJECT_ROOT. Legacy registry rows with ``.pipeline/projects/...`` are
rewritten to ``{PIPELINE_DIR}/projects/...``.
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
from pipeline.paths import get_pipeline_dir, registry_db
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

def _path_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def _allowed_roots() -> list[Path]:
    roots = [PROJECT_ROOT.resolve()]
    try:
        pipe = get_pipeline_dir().resolve()
        if pipe not in roots:
            roots.append(pipe)
    except Exception:
        pass
    return roots


def _is_allowed_workdir(work_dir: Path) -> bool:
    return any(_path_under(work_dir, r) for r in _allowed_roots())


def _strip_pipeline_projects_prefix(raw: str) -> str | None:
    """If path is factory/pipeline projects layout, return rest under projects/.

    Matches only:
      - relative ``projects/...``
      - relative/absolute ``.pipeline/projects/...``
    Does **not** strip bare ``.../projects/...`` from unrelated absolute trees
    (e.g. ``D:/code/projects/mytool``).
    """
    text = (raw or "").strip().replace("\\", "/")
    if not text:
        return None
    if text.startswith("projects/"):
        return text[len("projects/") :]
    if text.startswith(".pipeline/projects/"):
        return text[len(".pipeline/projects/") :]
    lower = text.lower()
    marker = ".pipeline/projects/"
    if marker in lower:
        idx = lower.rfind(marker)
        return text[idx + len(marker) :]
    return None


def _looks_like_projects_layout(raw: str) -> bool:
    """True when cwd_template is project workspace layout (not shared_libs etc.)."""
    text = (raw or "").strip()
    if not text:
        return False
    if _strip_pipeline_projects_prefix(text) is not None:
        return True
    try:
        p = Path(text).expanduser().resolve()
        factory_nested = (PROJECT_ROOT / ".pipeline" / "projects").resolve()
        if _path_under(p, factory_nested):
            return True
        pipe_projects = (get_pipeline_dir().resolve() / "projects")
        if _path_under(p, pipe_projects):
            return True
    except (OSError, ValueError):
        pass
    return False


def _should_prefer_project_workspace(*, kind: str, cwd_template: str) -> bool:
    """Prefer ``{PIPELINE_DIR}/projects/<slug>/workspace`` only for project-shaped caps.

    shared_lib / hermes / pipeline_script may carry ``source_project`` but must
    honor their own cwd_template (e.g. absolute shared_libs path).
    """
    k = (kind or "").strip().lower()
    if k and k not in ("project",):
        return False
    ct = (cwd_template or "").strip()
    if not ct:
        return True
    return _looks_like_projects_layout(ct)


def resolve_capability_workdir(
    *,
    slug: str = "",
    source_project: str = "",
    cwd_template: str = "",
    cwd_override: str = "",
    kind: str = "",
) -> Path:
    """Resolve invoke/workflow cwd under PIPELINE_DIR or factory PROJECT_ROOT.

    Preference order:
      1. Explicit cwd_override (rewritten if ``.pipeline/projects/...``)
      2. Project workspace ``{PIPELINE_DIR}/projects/<slug>/workspace`` when
         capability is project-shaped (kind empty/project and template empty
         or projects-layout)
      3. cwd_template under pipeline root / factory root (absolute shared_libs etc.)
      4. PROJECT_ROOT
    """
    pipe = get_pipeline_dir().resolve()
    factory_nested = (PROJECT_ROOT / ".pipeline" / "projects").resolve()
    # Prefer source_project only when project-shaped; slug is the capability id
    proj_slug = (slug or source_project or "").strip()
    if (kind or "").strip().lower() == "project":
        proj_slug = (source_project or slug or "").strip() or proj_slug
    elif (kind or "").strip().lower() not in ("", "project"):
        # non-project: only use slug if template is projects-layout; never
        # source_project as workspace preference key
        proj_slug = (slug or "").strip()

    def _from_raw(raw: str) -> Path | None:
        text = (raw or "").strip()
        if not text:
            return None
        p = Path(text).expanduser()
        if p.is_absolute():
            try:
                pr = p.resolve()
            except OSError:
                pr = p
            # Absolute under factory .pipeline/projects → prefer live PIPELINE_DIR
            if _path_under(pr, factory_nested):
                try:
                    rest = pr.relative_to(factory_nested).as_posix()
                except ValueError:
                    rest = _strip_pipeline_projects_prefix(str(pr)) or ""
                if rest:
                    live = (pipe / "projects" / rest).resolve()
                    # Prefer live when it exists, or when factory path is stale/missing
                    if live.exists() or not pr.exists():
                        return live
                    return live  # both exist: still prefer live pipeline
            if pr.exists() and _is_allowed_workdir(pr):
                return pr
            # Only rewrite absolute paths that embed .pipeline/projects/
            rest = _strip_pipeline_projects_prefix(str(pr).replace("\\", "/"))
            if rest is not None:
                cand = (pipe / "projects" / rest).resolve()
                if cand.exists() or _is_allowed_workdir(cand):
                    return cand
            return pr

        rest = _strip_pipeline_projects_prefix(text)
        if rest is not None:
            return (pipe / "projects" / rest).resolve()

        # Relative: prefer under pipeline root when it exists there
        under_pipe = (pipe / text).resolve()
        if under_pipe.exists():
            return under_pipe
        under_factory = (PROJECT_ROOT / text).resolve()
        if under_factory.exists():
            return under_factory
        if text.replace("\\", "/").startswith("projects/"):
            return under_pipe
        return under_factory

    if cwd_override:
        resolved = _from_raw(cwd_override)
        if resolved is not None:
            return resolved

    prefer_ws = _should_prefer_project_workspace(kind=kind, cwd_template=cwd_template)
    if prefer_ws and proj_slug:
        preferred = (pipe / "projects" / proj_slug / "workspace").resolve()
        if preferred.is_dir():
            return preferred
        proj_root = (pipe / "projects" / proj_slug).resolve()
        if proj_root.is_dir() and not cwd_template:
            return proj_root

    if cwd_template:
        resolved = _from_raw(cwd_template)
        if resolved is not None:
            return resolved

    if prefer_ws and proj_slug:
        return (pipe / "projects" / proj_slug / "workspace").resolve()

    return PROJECT_ROOT.resolve()


def rewrite_capability_entrypoint(entry: str, *, work_dir: Path | None = None) -> str:
    """Rewrite factory ``.pipeline/projects/...`` segments to live PIPELINE_DIR paths.

    Does not rewrite unrelated absolute trees that merely contain ``/projects/``.
    Relative ``projects/...`` tokens (path boundary) are rewritten under PIPELINE_DIR.
    """
    text = (entry or "").strip()
    if not text:
        return text
    pipe = get_pipeline_dir().resolve()
    factory_nested = (PROJECT_ROOT / ".pipeline" / "projects").resolve()
    out = text

    # Absolute factory nested projects path → pipeline
    try:
        fn = str(factory_nested)
        if fn and fn in out:
            out = out.replace(fn, str(pipe / "projects"))
    except Exception:
        pass

    # .pipeline/projects/... only (not bare projects inside D:\code\projects\...)
    def _repl_dot_pipeline(m: re.Match[str]) -> str:
        token = m.group(0)
        rest = _strip_pipeline_projects_prefix(token)
        if rest is None:
            return token
        return str((pipe / "projects" / rest).resolve())

    out = re.sub(
        r"\.pipeline[/\\]+projects[/\\]+[^\s\"']+",
        _repl_dot_pipeline,
        out,
        flags=re.IGNORECASE,
    )

    # Relative projects/... at path boundary (start or after whitespace/quote)
    def _repl_rel_projects(m: re.Match[str]) -> str:
        prefix = m.group(1)
        token = m.group(2)
        rest = _strip_pipeline_projects_prefix(token)
        if rest is None:
            return m.group(0)
        return prefix + str((pipe / "projects" / rest).resolve())

    out = re.sub(
        r"(^|[\s\"'])(projects[/\\]+[^\s\"']+)",
        _repl_rel_projects,
        out,
        flags=re.IGNORECASE,
    )

    # Fallback: only for absolute/multi-segment scripts that went missing after
    # rewrite; leave bare names like ``cli.py`` workspace-relative for cwd.
    if work_dir is not None:
        try:
            parts = shlex.split(out, posix=False)
        except ValueError:
            parts = out.split()
        if len(parts) >= 2:
            script = Path(parts[1])
            if (script.is_absolute() or len(script.parts) > 1) and not script.is_file():
                local = work_dir / script.name
                if local.is_file():
                    parts[1] = str(local)
                    out = " ".join(parts)
    return out


def _get_capability(slug: str) -> dict[str, Any] | None:
    if not registry_db().exists():
        return None
    conn = _connect()
    row = conn.execute(
        """
        SELECT slug, title, kind, status, purpose, entrypoint, example_invoke,
               cwd_template, requires, source_project
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

    work_dir = resolve_capability_workdir(
        slug=str(row.get("slug") or slug),
        source_project=str(row.get("source_project") or ""),
        cwd_template=str(row.get("cwd_template") or ""),
        cwd_override=cwd or "",
        kind=str(row.get("kind") or ""),
    )
    entry = rewrite_capability_entrypoint(entry, work_dir=work_dir)

    cmd = entry
    if args:
        cmd = f"{entry} {args}"

    if not _is_allowed_workdir(work_dir):
        return (
            "ERROR: cwd must stay inside project root or PIPELINE_DIR "
            f"(got {work_dir})"
        )

    try:
        argv = shlex.split(cmd, posix=False)
    except ValueError as e:
        return f"ERROR: cannot parse command: {e}"

    try:
        # Ensure cwd exists when possible (clearer error than WinError 267)
        if not work_dir.is_dir():
            return f"ERROR: cwd does not exist: {work_dir}"
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
