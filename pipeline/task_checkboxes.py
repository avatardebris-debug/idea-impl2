"""
Task checkbox honesty for phase tasks.md files.

Gates: do not advance phase or mark complete while open ``- [ ]`` / ``- []`` remain.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# Standard markdown task lines
_OPEN = re.compile(r"^(\s*)-\s*\[\s*\]\s+(.*)$", re.MULTILINE)
_DONE = re.compile(r"^(\s*)-\s*\[[xX]\]\s+(.*)$", re.MULTILINE)
# Corrupted "text- [x] Task" glued on same line — treat trailing open task as open
_OPEN_ANYWHERE = re.compile(r"-\s*\[\s*\]\s+")
_DONE_ANYWHERE = re.compile(r"-\s*\[[xX]\]\s+")


@dataclass
class TaskCheckboxStats:
    open_count: int = 0
    done_count: int = 0
    total: int = 0
    open_titles: list[str] | None = None
    path: str = ""

    @property
    def all_closed(self) -> bool:
        """True if there is at least one task and none open, or no task file / no tasks."""
        if self.total == 0:
            # No checkboxes found — treat as incomplete if file exists with Task lines
            return self.path == "" or not Path(self.path).is_file()
        return self.open_count == 0

    @property
    def has_tasks(self) -> bool:
        return self.total > 0


def count_checkboxes_in_text(content: str) -> tuple[int, int, list[str]]:
    """Return (open, done, open_title_samples)."""
    if not content:
        return 0, 0, []
    open_titles: list[str] = []
    open_n = 0
    done_n = 0
    for m in _OPEN.finditer(content):
        open_n += 1
        title = (m.group(2) or "").strip()[:80]
        if title:
            open_titles.append(title)
    for _ in _DONE.finditer(content):
        done_n += 1
    # Fallback: count any - [ ] not already counted (weird formatting)
    if open_n == 0 and done_n == 0:
        open_n = len(_OPEN_ANYWHERE.findall(content))
        done_n = len(_DONE_ANYWHERE.findall(content))
    return open_n, done_n, open_titles[:12]


def stats_for_tasks_file(path: Path) -> TaskCheckboxStats:
    if not path.is_file():
        return TaskCheckboxStats(path=str(path))
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return TaskCheckboxStats(path=str(path))
    open_n, done_n, titles = count_checkboxes_in_text(text)
    return TaskCheckboxStats(
        open_count=open_n,
        done_count=done_n,
        total=open_n + done_n,
        open_titles=titles,
        path=str(path),
    )


def phase_tasks_path(project_dir: Path, phase_num: int) -> Path:
    return project_dir / "phases" / f"phase_{phase_num}" / "tasks.md"


def stats_for_phase(project_dir: Path, phase_num: int) -> TaskCheckboxStats:
    return stats_for_tasks_file(phase_tasks_path(project_dir, phase_num))


def stats_all_phases(project_dir: Path, *, max_phase: int | None = None) -> TaskCheckboxStats:
    """Aggregate checkboxes across phases/phase_*/tasks.md."""
    phases_root = project_dir / "phases"
    open_n = done_n = 0
    titles: list[str] = []
    if not phases_root.is_dir():
        return TaskCheckboxStats()
    dirs = sorted(phases_root.glob("phase_*"))
    for d in dirs:
        if not d.is_dir():
            continue
        # phase_1, phase_2 — skip overflow for complete-all unless we want them
        name = d.name
        if "_overflow" in name:
            continue
        m = re.match(r"phase_(\d+)$", name)
        if not m:
            continue
        pnum = int(m.group(1))
        if max_phase is not None and pnum > max_phase:
            continue
        st = stats_for_tasks_file(d / "tasks.md")
        open_n += st.open_count
        done_n += st.done_count
        if st.open_titles:
            titles.extend(st.open_titles)
    return TaskCheckboxStats(
        open_count=open_n,
        done_count=done_n,
        total=open_n + done_n,
        open_titles=titles[:20],
        path=str(phases_root),
    )


def phase_tasks_closed(project_dir: Path, phase_num: int) -> bool:
    """
    True if phase may advance from a checkbox perspective.

    - No tasks.md → True (nothing to enforce; planner may not have written yet)
    - tasks.md with zero checkbox lines → False if file mentions 'Task' (malformed)
    - Otherwise open_count == 0
    """
    path = phase_tasks_path(project_dir, phase_num)
    if not path.is_file():
        return True
    st = stats_for_tasks_file(path)
    if st.total == 0:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return True
        # Malformed / empty checklist but looks like a task list
        if re.search(r"\bTask\s+\d+", text, re.IGNORECASE):
            return False
        return True
    return st.open_count == 0


def project_all_tasks_closed(project_dir: Path) -> bool:
    st = stats_all_phases(project_dir)
    if st.total == 0:
        # Any tasks.md with Task N and no checkboxes?
        phases = project_dir / "phases"
        if not phases.is_dir():
            return True
        for tasks in phases.glob("phase_*/tasks.md"):
            if "_overflow" in str(tasks):
                continue
            try:
                text = tasks.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if re.search(r"\bTask\s+\d+", text, re.IGNORECASE) and not _DONE.search(text):
                if _OPEN.search(text) or _OPEN_ANYWHERE.search(text):
                    return False
                # has Task N but no checkbox syntax at all
                return False
        return True
    return st.open_count == 0


def sync_task_counts_to_state(state: dict, project_dir: Path, phase_num: int) -> dict:
    """Update tasks_done / tasks_total on state from phase tasks.md."""
    st = stats_for_phase(project_dir, phase_num)
    if st.total > 0:
        state["tasks_done"] = st.done_count
        state["tasks_total"] = st.total
    return state


def format_open_tasks_message(stats: TaskCheckboxStats, *, phase: int | None = None) -> str:
    where = f"phase {phase}" if phase is not None else "project"
    titles = ""
    if stats.open_titles:
        titles = " Open: " + "; ".join(stats.open_titles[:5])
        if len(stats.open_titles) > 5:
            titles += "…"
    return (
        f"{stats.open_count} open task checkbox(es) on {where} "
        f"({stats.done_count}/{stats.total} done).{titles}"
    )
