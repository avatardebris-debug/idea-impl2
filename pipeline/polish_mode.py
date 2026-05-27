"""
pipeline/polish_mode.py
--polish queue processing (extracted from runner.py).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from pipeline.message_bus import Message
from pipeline.pipeline_config import PIPELINE_DIR, PROJECT_ROOT

if TYPE_CHECKING:
    from pipeline.message_bus import MessageBus

# Must match runner.AGENT_ROLES for queue depth totals
_AGENT_ROLES = (
    "idea_planner",
    "phase_planner",
    "executor",
    "reviewer",
    "validator",
    "manager",
    "documenter",
    "ideator",
    "critic",
)


def slugify_title(title: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_-]+", "_", slug)
    return slug.strip("_") or "unknown"


def queue_pending(bus: "MessageBus") -> int:
    try:
        return sum(bus.queue_depth(r) for r in _AGENT_ROLES)
    except Exception:
        return 0


_PHASE_STATUS = re.compile(r"^phase_(\d+)_(planning|executing|validating|reviewing|reviewed)$")


def _iter_polish_queue_lines(polish_path: Path):
    """Yield (raw_title, notes, slug) for unchecked polish_queue.md entries."""
    if not polish_path.exists():
        return
    for line in polish_path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"- \[ \]\s+\*\*(.+?)\*\*\s*[—–-]\s*(.*)", line)
        if not match:
            continue
        raw_title = match.group(1).strip().strip("[]")
        yield raw_title, match.group(2).strip(), slugify_title(raw_title)


def requeue_polish_in_progress(
    bus: "MessageBus",
    polish_path: Path,
    seeded_session: set[str],
) -> int:
    """Re-queue polish_queue projects already in phase_N_* (prior --polish run)."""
    from pipeline.project_ops import _rebuild_single_project

    projects_dir = PIPELINE_DIR / "projects"
    requeued = 0

    for raw_title, _notes, slug in _iter_polish_queue_lines(polish_path):
        if raw_title in seeded_session:
            continue
        state_file = projects_dir / slug / "state" / "current_idea.json"
        if not state_file.exists():
            continue
        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        status = state.get("status", "")
        if status in ("complete", "budget_exceeded", "", "dep_waiting"):
            continue
        if not _PHASE_STATUS.match(status):
            print(f"  [polish] SKIP '{raw_title}' — status is '{status}' (not a polish phase state)")
            continue

        project_dir = projects_dir / slug
        if _rebuild_single_project(bus, slug, state, project_dir):
            print(f"  [polish] Re-queued '{raw_title}' — resume {status}")
            seeded_session.add(raw_title)
            requeued += 1
        else:
            print(f"  [polish] SKIP '{raw_title}' — could not re-queue {status}")

    return requeued


def run_polish_mode(
    bus: "MessageBus",
    polish_path: Path,
    seeded_session: set[str],
) -> int:
    """Queue phase_planner work for qualifying polish_queue.md entries."""
    if not polish_path.exists():
        print(f"  [polish] {polish_path.name} not found — creating template...")
        write_polish_queue_template(polish_path)
        print(f"  [polish] Wrote template to {polish_path}")
        print("  [polish] Edit polish_queue.md then re-run with --polish")
        return 0

    queued = 0
    projects_dir = PIPELINE_DIR / "projects"

    for raw_title, notes, slug in _iter_polish_queue_lines(polish_path):
        if raw_title in seeded_session:
            continue

        state_file = projects_dir / slug / "state" / "current_idea.json"
        if not state_file.exists():
            print(f"  [polish] SKIP '{raw_title}' — no project state found (slug: {slug})")
            continue

        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [polish] SKIP '{raw_title}' — unreadable state: {e}")
            continue

        current_status = state.get("status", "")
        current_phase = state.get("phase", 1)
        total_phases = state.get("total_phases", 1)

        if current_status not in ("complete", "budget_exceeded"):
            if _PHASE_STATUS.match(current_status):
                from pipeline.project_ops import _rebuild_single_project

                project_dir = projects_dir / slug
                if _rebuild_single_project(bus, slug, state, project_dir):
                    print(f"  [polish] Re-queued '{raw_title}' — resume {current_status}")
                    seeded_session.add(raw_title)
                    queued += 1
                else:
                    print(f"  [polish] SKIP '{raw_title}' — could not re-queue {current_status}")
            else:
                print(
                    f"  [polish] SKIP '{raw_title}' — status is '{current_status}' "
                    "(not complete/budget_exceeded or phase_N_*)"
                )
            continue

        next_phase = int(current_phase) + 1 if current_status == "complete" else int(current_phase)
        if next_phase > int(total_phases):
            print(
                f"  [polish] SKIP '{raw_title}' — already at max phase "
                f"({current_phase}/{total_phases})"
            )
            continue

        resume_status = f"phase_{next_phase}_planning"
        state["status"] = resume_status
        state["session_started_at"] = datetime.now(timezone.utc).isoformat()
        state.pop("budget_note", None)
        state.pop("pre_budget_status", None)
        if notes:
            state["polish_notes"] = notes
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

        master_plan_file = projects_dir / slug / "state" / "master_plan.md"
        phase_spec = f"Polish resume: phase {next_phase} of {raw_title}. {notes}"
        if master_plan_file.exists():
            try:
                mp = master_plan_file.read_text(encoding="utf-8")
                m = re.search(
                    rf"## Phase {next_phase}\b[^\n]*\n.*?(?=## Phase \d|$)",
                    mp,
                    re.DOTALL | re.IGNORECASE,
                )
                if m:
                    phase_spec = m.group(0)[:3000]
            except Exception:
                pass

        msg = Message.create(
            from_agent="runner",
            to_agent="phase_planner",
            type="task",
            payload={"phase": next_phase, "phase_spec": phase_spec, "idea_slug": slug},
        )
        bus.send(msg)
        print(
            f"  [polish] Queued '{raw_title}' → phase_{next_phase}_planning "
            f"(was {current_status} p{current_phase}/{total_phases})"
        )
        seeded_session.add(raw_title)
        queued += 1

    if queued == 0:
        print("  [polish] Nothing to polish — all entries already done or missing.")
        print("  [polish] Hint: regenerate queue or resume in-flight polish work:")
        print("           python reset_budget_exceeded.py --generate-polish")
        print("           python pipeline/runner.py --polish --resume --provider ollama --model <model>")
    return queued


def handle_polish_idle(bus: "MessageBus", polish_path: Path, seeded_session: set[str]) -> bool:
    """Try to queue more polish work when seed returns empty."""
    if bus.has_active_work():
        return True
    extra = run_polish_mode(bus, polish_path, seeded_session)
    if extra > 0:
        from pipeline.polish_status import print_polish_lifecycle

        print_polish_lifecycle(
            "running",
            reason=f"queued {extra} additional project(s)",
            queued=extra,
            queue_path=str(polish_path),
            pending_messages=queue_pending(bus),
        )
        return True
    return False


def write_polish_queue_template(path: Path) -> None:
    projects_dir = PIPELINE_DIR / "projects"
    lines = [
        "# Polish Queue",
        "",
        "Projects marked complete but with missing phases.",
        "The --polish flag resumes them from their last completed phase.",
        "Format: `- [ ] **[project-slug]** — notes about what to add`",
        "",
    ]
    if projects_dir.exists():
        for proj_dir in sorted(projects_dir.iterdir()):
            if not proj_dir.is_dir():
                continue
            sf = proj_dir / "state" / "current_idea.json"
            if not sf.exists():
                continue
            try:
                s = json.loads(sf.read_text(encoding="utf-8"))
                status = s.get("status", "")
                phase = s.get("phase", 1)
                total = s.get("total_phases", 1)
                title = s.get("title", proj_dir.name)
                if status in ("complete", "budget_exceeded") and int(phase) < int(total):
                    lines.append(
                        f"- [ ] **[{proj_dir.name}]** — "
                        f"p{phase}/{total} {status}. Continue phases {int(phase)+1}-{total}. "
                        f"Original title: {title[:50]}"
                    )
            except Exception:
                continue
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_polish_path(
    *,
    polish_queue_file: str | None,
    ideas_file: str | None,
) -> Path:
    if polish_queue_file:
        return Path(polish_queue_file).resolve()
    if ideas_file:
        return Path(ideas_file).resolve()
    return PROJECT_ROOT / "polish_queue.md"
