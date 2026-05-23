"""
pipeline/project_state.py
Project state I/O, retries, polish, eviction.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from pipeline.message_bus import Message, MessageBus
from pipeline.pipeline_config import (
    AGENT_ROLES,
    MAX_PHASE_RETRIES,
    MAX_PROJECT_LIFETIME_RETRIES,
    PIPELINE_DIR,
    PROJECT_ROOT,
)
from pipeline.slug_util import slugify_title as _slugify

if TYPE_CHECKING:
    pass

def _write_state(project_dir: pathlib.Path, state: dict, new_status: str) -> None:
    """Update status in current_idea.json."""
    state["status"] = new_status
    state.pop("review_result", None)
    _write_state_dict(project_dir, state)


def _write_state_dict(project_dir: pathlib.Path, state: dict) -> None:
    """Write state dict to disk."""
    state_file = project_dir / "state" / "current_idea.json"
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _increment_retries(project_dir: pathlib.Path, phase_num: int) -> int:
    """Increment and return the retry count for a phase."""
    retries_file = project_dir / "state" / "phase_retries.json"
    try:
        data = json.loads(retries_file.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    key = f"phase_{phase_num}"
    data[key] = data.get(key, 0) + 1
    retries_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data[key]


def _reset_retries(project_dir: pathlib.Path, phase_num: int) -> None:
    """Reset retry counter for a phase."""
    retries_file = project_dir / "state" / "phase_retries.json"
    try:
        data = json.loads(retries_file.read_text(encoding="utf-8"))
        data.pop(f"phase_{phase_num}", None)
        retries_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def _append_polish(project_dir: pathlib.Path, phase_num: int, notes: str) -> None:
    """Save non-blocking review notes as deferred polish tasks."""
    path = PIPELINE_DIR / "state" / "plan_amendments.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    bullets = re.findall(r'^[-*]\s+(.+)$', notes, re.MULTILINE)
    if not bullets:
        return
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n### Phase {phase_num} Polish Items\n")
        for b in bullets:
            f.write(f"- [ ] (polish) {b}\n")


def _check_priority_eviction(bus: MessageBus, parallel_seeds: int, ideas_path: pathlib.Path | None = None) -> None:
    """Eviction Controller: pre-empts lowest priority running project if a higher priority one is ready."""
    projects_dir = PIPELINE_DIR / "projects"
    if not projects_dir.exists():
        return

    # 1. Scan active and evicted projects
    active_projects = []
    evicted_projects = []
    
    for p in projects_dir.iterdir():
        if not p.is_dir():
            continue
        sf = p / "state" / "current_idea.json"
        if not sf.exists():
            continue
        try:
            state = json.loads(sf.read_text(encoding="utf-8"))
            status = state.get("status", "")
            priority = int(state.get("priority_tier", 0))
            project_info = {
                "slug": p.name,
                "priority": priority,
                "status": status,
                "state_file": sf,
                "state": state
            }
            if status in ("complete", "budget_exceeded", "dep_waiting", ""):
                continue
            elif status == "evicted":
                evicted_projects.append(project_info)
            else:
                active_projects.append(project_info)
        except Exception:
            pass

    active_count = len(active_projects)
    if active_count < parallel_seeds:
        return  # Slots not full — no eviction needed

    # 2. Scan ready unseeded projects from master_ideas.md
    mi_path = ideas_path if ideas_path else PROJECT_ROOT / "master_ideas.md"
    ready_unseeded = []
    if mi_path.exists():
        try:
            import re
            content = mi_path.read_text(encoding="utf-8")
            for line in content.split("\n"):
                match = re.match(r"- \[ \]\s+\*\*(.+?)\*\*\s*[—–-]\s*(.*)", line)
                if not match:
                    continue
                title = match.group(1).strip()
                slug = _slugify(title)
                
                if (projects_dir / slug / "state" / "current_idea.json").exists():
                    continue

                description_raw = match.group(2).strip()
                if description_raw.startswith("[") and description_raw.endswith("]"):
                    description_raw = description_raw[1:-1].strip()

                priority_match = re.search(r'\b(?:priority|priority_tier):\s*(\d+)', description_raw, re.IGNORECASE)
                priority_tier = 0
                if priority_match:
                    priority_tier = int(priority_match.group(1))
                    description_raw = re.sub(r'\s*[,;.-]?\s*\b(?:priority|priority_tier):\s*\d+\s*', '', description_raw, flags=re.IGNORECASE).strip()

                locked = bool(re.search(r'\[lock\]', description_raw, re.IGNORECASE))
                dep_match = re.search(r'\brequires:\s*([\w,\s_-]+?)[\]\s.]*$', description_raw, re.IGNORECASE)
                deps = []
                if dep_match:
                    raw_deps = dep_match.group(1)
                    deps = [d.strip() for d in re.split(r'[,;]+', raw_deps) if d.strip()]

                blocking = []
                for dep_slug in deps:
                    dep_state_file = projects_dir / dep_slug / "state" / "current_idea.json"
                    if not dep_state_file.exists():
                        blocking.append(dep_slug)
                        continue
                    try:
                        dep_state = json.loads(dep_state_file.read_text(encoding="utf-8"))
                        if dep_state.get("status") not in ("complete", "budget_exceeded"):
                            blocking.append(dep_slug)
                    except Exception:
                        blocking.append(dep_slug)

                if not blocking:
                    ready_unseeded.append({
                        "slug": slug,
                        "priority": priority_tier,
                        "title": title
                    })
        except Exception:
            pass

    waiting_projects = []
    for ep in evicted_projects:
        deps = ep["state"].get("depends_on", [])
        blocking = []
        for dep_slug in deps:
            dep_file = projects_dir / dep_slug / "state" / "current_idea.json"
            if not dep_file.exists():
                blocking.append(dep_slug)
                continue
            try:
                dep_st = json.loads(dep_file.read_text(encoding="utf-8"))
                if dep_st.get("status") not in ("complete", "budget_exceeded"):
                    blocking.append(dep_slug)
            except Exception:
                blocking.append(dep_slug)
        if not blocking:
            waiting_projects.append(ep)

    for rup in ready_unseeded:
        waiting_projects.append(rup)

    if not waiting_projects:
        return

    highest_waiting = max(waiting_projects, key=lambda x: x["priority"])
    
    eligible_active = [ap for ap in active_projects if not ap["state"].get("evict_requested")]
    if not eligible_active:
        return

    lowest_active = min(eligible_active, key=lambda x: x["priority"])

    if highest_waiting["priority"] > lowest_active["priority"]:
        print(f"\n  [!] [EVICTION] Higher priority project '{highest_waiting.get('title', highest_waiting['slug'])}' (priority {highest_waiting['priority']}) is ready!")
        print(f"  [!] [EVICTION] Evicting lower priority active project '{lowest_active['slug']}' (priority {lowest_active['priority']}) to free slot.")
        
        state = lowest_active["state"]
        state["evict_requested"] = True
        lowest_active["state_file"].write_text(json.dumps(state, indent=2), encoding="utf-8")
