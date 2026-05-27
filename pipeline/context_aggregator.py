"""
pipeline/context_aggregator.py
Strategy 3 — Project Context Aggregator.

Flattens every context file a project's agents need into a single
`context_cache.json` per project.  Agents read ONE file instead of
performing 5-10 separate `read_file` / `list_tree` tool calls per turn.

The cache is rebuilt:
  - When the runner starts (via `refresh_all_projects`)
  - After each phase transition (via `refresh_project`)
  - On a background thread every N minutes (via `start_background_refresh`)

Cache location:
  .pipeline/projects/<slug>/state/context_cache.json

Cache schema:
  {
    "slug":           "my_project",
    "refreshed_at":   "2026-05-18T...",
    "master_plan":    "...",          # full text of state/master_plan.md
    "current_phase":  2,
    "current_tasks":  "...",          # text of phases/phase_2/tasks.md
    "workspace_tree": ["foo/bar.py", ...],   # relative paths, max 200
    "shared_libs":    ["http_client", ...],  # dir names under shared_libs/
    "reusable_tools": "...",          # .pipeline/state/reusable_tools.md
    "capabilities_summary": "...",    # generated from capability_registry.sqlite (non-legacy)
    "validation_report": "...",       # phases/phase_N/validation_report.md (last)
    "fix_report":     "...",          # phases/phase_N/fix_report.md (last)
    "pending_fixes":  "...",          # state/pending_fixes.md
  }

Usage in agents (see agent_process.py):
    from pipeline.context_aggregator import load_context_cache
    ctx = load_context_cache(project_dir)
    # ctx["master_plan"], ctx["current_tasks"], ctx["workspace_tree"], ...
"""
from __future__ import annotations

import json
import pathlib
import threading
import time
from datetime import datetime, timezone
from typing import Any

PIPELINE_DIR_NAME = ".pipeline"
MAX_TREE_ENTRIES  = 200    # workspace file listing cap
MAX_TEXT_BYTES    = 6_000  # max chars per text field in cache


def _read(path: pathlib.Path, max_bytes: int = MAX_TEXT_BYTES) -> str:
    """Read a text file safely; return '' on any error."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[:max_bytes] if len(text) > max_bytes else text
    except Exception:
        return ""


def _workspace_tree(workspace: pathlib.Path, max_entries: int = MAX_TREE_ENTRIES) -> list[str]:
    """Return sorted relative paths of all files in workspace (capped)."""
    if not workspace.exists():
        return []
    files = []
    for p in workspace.rglob("*"):
        if p.is_file() and not p.name.startswith("."):
            try:
                files.append(str(p.relative_to(workspace)))
            except ValueError:
                pass
        if len(files) >= max_entries:
            break
    return sorted(files)


def build_context_cache(project_dir: pathlib.Path) -> dict[str, Any]:
    """
    Build and write the context cache for a single project.
    Returns the cache dict.
    """
    state_dir  = project_dir / "state"
    phases_dir = project_dir / "phases"
    workspace  = project_dir / "workspace"

    # Discover current phase from state file
    current_phase = 1
    state_file = state_dir / "current_idea.json"
    if state_file.exists():
        try:
            content = state_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                content = state_file.read_text(encoding="cp1252")
            except Exception:
                content = state_file.read_text(encoding="utf-8", errors="replace")
        try:
            ci = json.loads(content)
            current_phase = int(ci.get("phase", 1))
        except Exception:
            pass

    # Paths for this phase
    phase_dir   = phases_dir / f"phase_{current_phase}"
    tasks_path  = phase_dir / "tasks.md"
    val_path    = phase_dir / "validation_report.md"
    fix_path    = phase_dir / "fix_report.md"

    # Shared libs
    pipeline_root = project_dir.parent.parent  # <root>/.pipeline/projects/<slug>
    shared_libs_dir = project_dir.parent.parent / "shared_libs"
    shared_libs: list[str] = []
    if shared_libs_dir.exists():
        shared_libs = sorted(d.name for d in shared_libs_dir.iterdir() if d.is_dir())

    # Reusable tools index (pipeline-global)
    reusable_tools_path = project_dir.parent.parent / "state" / "reusable_tools.md"

    cap_summary = ""
    try:
        from pipeline.pipeline_mode import legacy_mode
        if not legacy_mode():
            from pipeline.capability_registry import capabilities_summary
            cap_summary = capabilities_summary(project_dir.name)
    except Exception:
        pass

    cache: dict[str, Any] = {
        "slug":              project_dir.name,
        "refreshed_at":      datetime.now(timezone.utc).isoformat(),
        "current_phase":     current_phase,
        "master_plan":       _read(state_dir / "master_plan.md"),
        "current_tasks":     _read(tasks_path),
        "workspace_tree":    _workspace_tree(workspace),
        "shared_libs":       shared_libs,
        "reusable_tools":       _read(reusable_tools_path),
        "capabilities_summary": cap_summary[:MAX_TEXT_BYTES] if cap_summary else "",
        "validation_report": _read(val_path),
        "fix_report":        _read(fix_path),
        "pending_fixes":     _read(state_dir / "pending_fixes.md"),
    }

    # Write to disk
    out_path = state_dir / "context_cache.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
    return cache


def load_context_cache(project_dir: pathlib.Path) -> dict[str, Any]:
    """
    Load the cached context for a project.
    Returns an empty dict if the cache doesn't exist yet (agent falls back
    to individual file reads).
    """
    cache_path = project_dir / "state" / "context_cache.json"
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def refresh_project(project_dir: pathlib.Path) -> None:
    """Rebuild the context cache for one project (called after phase transitions)."""
    try:
        build_context_cache(project_dir)
    except Exception:
        pass  # Never crash the caller


def refresh_all_projects(pipeline_dir: pathlib.Path, active_only: bool = True) -> int:
    """
    Rebuild context caches for projects under .pipeline/projects/.
    If active_only is True (default), skips projects in terminal/inactive states.
    Returns the number of projects refreshed.
    """
    projects_dir = pipeline_dir / "projects"
    if not projects_dir.exists():
        return 0
    INACTIVE = {"complete", "budget_exceeded", "dep_waiting"}
    count = 0
    for proj in projects_dir.iterdir():
        if proj.is_dir():
            state_file = proj / "state" / "current_idea.json"
            if state_file.exists():
                if active_only:
                    try:
                        state_data = json.loads(state_file.read_text(encoding="utf-8"))
                        if state_data.get("status", "") in INACTIVE:
                            continue
                    except Exception:
                        pass
                refresh_project(proj)
                count += 1
    return count


# ---------------------------------------------------------------------------
# Background refresh thread
# ---------------------------------------------------------------------------

_bg_thread: threading.Thread | None = None
_bg_stop   = threading.Event()


def start_background_refresh(
    pipeline_dir: pathlib.Path,
    interval_seconds: int = 120,
) -> None:
    """
    Start a daemon thread that rebuilds all project context caches every
    `interval_seconds` (default 2 min).  Safe to call multiple times —
    only one thread runs at a time.
    """
    global _bg_thread, _bg_stop

    if _bg_thread and _bg_thread.is_alive():
        return  # already running

    _bg_stop.clear()

    def _loop() -> None:
        while not _bg_stop.is_set():
            _bg_stop.wait(interval_seconds)
            if _bg_stop.is_set():
                break
            try:
                refresh_all_projects(pipeline_dir)
            except Exception:
                pass

    _bg_thread = threading.Thread(target=_loop, name="ctx-aggregator", daemon=True)
    _bg_thread.start()


def stop_background_refresh() -> None:
    """Signal the background refresh thread to stop."""
    _bg_stop.set()


# ---------------------------------------------------------------------------
# ContextAggregator singleton  (used by Strategy 1 async preload)
# ---------------------------------------------------------------------------

class ContextAggregator:
    """Thin singleton wrapper so agent_process can call get_aggregator().build().

    Decouples callers from knowing the project dir path — they only supply
    a slug and we resolve the rest.
    """

    def build(self, slug: str, force: bool = False) -> dict[str, Any]:
        """Build (or return cached) context for a project slug.

        Args:
            slug:  Project slug (e.g. 'video_pow').
            force: If True, always rebuild even if a cache already exists.

        Returns:
            The context cache dict, or {} if the project dir doesn't exist.
        """
        from pipeline.paths import project_dir as pipeline_project_dir

        proj = pipeline_project_dir(slug)
        if not proj.exists():
            return {}
        cache_path = proj / "state" / "context_cache.json"
        if not force and cache_path.exists():
            # Already warm — return quickly without I/O
            try:
                return json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception:
                pass  # Fall through to rebuild
        return build_context_cache(proj)


_aggregator: ContextAggregator | None = None
_agg_lock = threading.Lock()


def get_aggregator() -> ContextAggregator:
    """Return the process-level ContextAggregator singleton."""
    global _aggregator
    if _aggregator is None:
        with _agg_lock:
            if _aggregator is None:
                _aggregator = ContextAggregator()
    return _aggregator
