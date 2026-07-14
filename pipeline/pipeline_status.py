"""
pipeline/pipeline_status.py
Pipeline status persistence and active-project state queries.
"""

from __future__ import annotations

import json
import pathlib
import re
from typing import TYPE_CHECKING

from pipeline.paths import (
    get_pipeline_dir,
    pipeline_status_json,
    throughput_json,
)

if TYPE_CHECKING:
    pass

_RUNNER_IDEAS_PATH: pathlib.Path | None = None


def set_runner_ideas_path(path: pathlib.Path | None) -> None:
    global _RUNNER_IDEAS_PATH
    _RUNNER_IDEAS_PATH = path


def get_runner_ideas_path() -> pathlib.Path | None:
    return _RUNNER_IDEAS_PATH


def _read_json_file(path: pathlib.Path) -> dict:
    """Read a JSON file with encoding robustness (try UTF-8, try CP1252, fallback with replacement)."""
    if not path.exists():
        return {}
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            content = path.read_text(encoding="cp1252")
        except Exception:
            content = path.read_text(encoding="utf-8", errors="replace")
    try:
        return json.loads(content)
    except Exception:
        return {}


def init_pipeline_dirs() -> None:
    """Create all pipeline runtime directories."""
    for subdir in [
        "queues",
        "state",
        "projects",
        "logs",
        "finetune_corpus/raw/task",
        "finetune_corpus/raw/phase",
        "finetune_corpus/raw/project",
        "shared_libs",
        "workflows",
        "workflows/connectors",
        "memory",
        "metrics",
        "goals",
    ]:
        (get_pipeline_dir() / subdir).mkdir(parents=True, exist_ok=True)

    # Session-Agnostic Throughput Cleanup: clear throughput.json on startup
    tp_path = throughput_json()
    if tp_path.exists():
        try:
            tp_path.unlink()
        except Exception:
            pass



def _get_active_idea_state(
    pipeline_dir: pathlib.Path,
    preferred_slug: str | None = None,
) -> dict:
    """Return the current_idea.json from the most recently modified IN-PROGRESS project.

    Skips projects in terminal states (complete, budget_exceeded) so that
    manually-edited state files don't permanently hijack the active slot.
    Falls back to the old global .pipeline/state/current_idea.json for
    backwards compatibility with runs that predate the per-project isolation.

    When *preferred_slug* is set (single-idea runs), that project wins for display.
    """
    if preferred_slug:
        preferred_path = (
            pipeline_dir / "projects" / preferred_slug / "state" / "current_idea.json"
        )
        if preferred_path.exists():
            try:
                state = _read_json_file(preferred_path)
                state.setdefault("_slug", preferred_slug)
                from pipeline.dep_policy import is_runner_inactive

                if not is_runner_inactive(state.get("status", "")):
                    return state
            except Exception:
                pass

    from pipeline.dep_policy import is_runner_inactive

    projects_dir = pipeline_dir / "projects"
    candidates: list[pathlib.Path] = []

    if projects_dir.exists():
        candidates = list(projects_dir.glob("*/state/current_idea.json"))

    if candidates:
        # Prefer in-progress projects sorted by most recently modified
        def sort_key(p: pathlib.Path):
            try:
                state = _read_json_file(p)
                is_terminal = is_runner_inactive(state.get("status", ""))
                return (1 if is_terminal else 0, -p.stat().st_mtime)
            except Exception:
                return (2, 0.0)

        candidates.sort(key=sort_key)
        for path in candidates:
            try:
                state = _read_json_file(path)
                state.setdefault("_slug", path.parent.parent.name)
                return state
            except Exception:
                continue

    # Fallback: old global location (pre-isolation runs)
    old_path = pipeline_dir / "state" / "current_idea.json"
    if old_path.exists():
        try:
            return _read_json_file(old_path)
        except Exception:
            pass

    return {}


def _get_all_active_idea_states(pipeline_dir: pathlib.Path) -> list[dict]:
    """Return all non-terminal project states sorted by most recently modified.

    Unlike _get_active_idea_state which returns only the single most-recently-modified
    project, this returns ALL in-progress projects for multi-project status display
    and checkpoint-on-interrupt.
    """
    from pipeline.dep_policy import is_runner_inactive

    projects_dir = pipeline_dir / "projects"
    results: list[tuple[float, dict]] = []

    if not projects_dir.exists():
        return []

    for p in projects_dir.glob("*/state/current_idea.json"):
        try:
            state = _read_json_file(p)
            if not is_runner_inactive(state.get("status", "")):
                state.setdefault("_slug", p.parent.parent.name)
                results.append((p.stat().st_mtime, state))
        except Exception:
            continue

    results.sort(key=lambda x: -x[0])
    return [s for _, s in results]


def save_pipeline_status(status: dict) -> None:
    path = pipeline_status_json()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=2)


def load_pipeline_status() -> dict:
    path = pipeline_status_json()
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def print_dashboard(*, activity_tail: int = 12) -> None:
    """Print a compact ops summary (active projects, status file, recent activity)."""
    pipeline_dir = get_pipeline_dir()
    print(f"Pipeline dir: {pipeline_dir}")
    status = load_pipeline_status()
    if status:
        print(f"Runner status: {json.dumps({k: status.get(k) for k in list(status)[:12]}, default=str)}")
    else:
        print("Runner status: (none)")

    active = _get_all_active_idea_states(pipeline_dir)
    print(f"\nActive projects: {len(active)}")
    for st in active[:20]:
        slug = st.get("_slug") or st.get("slug") or "?"
        print(
            f"  - {slug}: {st.get('status', '?')} "
            f"phase={st.get('phase', '?')}/{st.get('total_phases', '?')}"
        )
    if not active:
        # Show a few terminals for context
        projects = pipeline_dir / "projects"
        if projects.exists():
            n = 0
            for p in sorted(projects.glob("*/state/current_idea.json"))[:8]:
                try:
                    st = _read_json_file(p)
                    print(
                        f"  · {p.parent.parent.name}: {st.get('status', '?')} "
                        f"p{st.get('phase', '?')}/{st.get('total_phases', '?')}"
                    )
                    n += 1
                except Exception:
                    pass
            if n == 0:
                print("  (no projects)")

    try:
        from pipeline.paths import activity_jsonl

        act = activity_jsonl()
        if act.exists():
            lines = act.read_text(encoding="utf-8", errors="replace").splitlines()
            tail = lines[-activity_tail:] if lines else []
            print(f"\nRecent activity ({len(tail)} of {len(lines)}):")
            for line in tail:
                try:
                    row = json.loads(line)
                    print(f"  {row.get('ts', '')[:19]}  {row.get('event', '?')}  "
                          f"{row.get('slug') or row.get('title') or ''}")
                except Exception:
                    print(f"  {line[:120]}")
        else:
            print("\nActivity log: (none yet)")
    except Exception as exc:
        print(f"\nActivity log: error {exc}")

    try:
        from pipeline import bug_memory
        if hasattr(bug_memory, "print_stats"):
            print("\nBug memory:")
            bug_memory.print_stats()
    except Exception:
        pass


def main() -> None:
    print_dashboard()


if __name__ == "__main__":
    main()
