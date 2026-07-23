"""
Budget yield ladder (BE1 → BE2 → BE3).

Semantics:
  budget_exceeded remains the on-disk status for compatibility, but is a *yield*
  (slot free), not permanent death. Strikes escalate:

  strike 1 → AUTO_RETRY_CLEAN (fresh active clock)
  strike 2 → BE2 tactical (DEBUG_AGAIN / THIN_FIELD flag)
  strike ≥3 → blocker_report.v1 + rule-based manager menu

Env (defaults favor safety / overnight):
  BUDGET_ACTIVE_CLOCK=1          wall idle gaps do not count toward budget
  BUDGET_IDLE_GAP_MINUTES=45     pause clock after this idle gap
  BUDGET_BE1_AUTO_RETRY=1        strike-1 auto resume
  BUDGET_BE2=1                   mark BE2 path on strike 2
  BUDGET_BE3_BLOCKER=1           write blocker_report + manager decision
  BUDGET_PREREQ_RESET=1          reset unlocked BE prereq once when deps block seed
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.env_flags import env_bool, env_float, env_int
from pipeline.paths import get_pipeline_dir, project_dir, projects_dir, state_dir

MANAGER_DECISIONS = frozenset({
    "AUTO_RETRY_CLEAN",
    "EXTEND_BUDGET",
    "DEBUG_AGAIN",
    "THIN_FIELD",
    "BYPASS_RETURN",
    "SOFT_SKIP_REQUIRES",
    "SUBSTITUTE",
    "IGNORE_NEXT",
    "ASK_OPERATOR",
    "ARCHIVE_GOAL_EDGE",
})


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(s: str | None) -> datetime | None:
    if not s or not isinstance(s, str):
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).isoformat()


def active_clock_enabled() -> bool:
    return env_bool("BUDGET_ACTIVE_CLOCK", default=True)


def idle_gap_minutes() -> float:
    return max(5.0, env_float("BUDGET_IDLE_GAP_MINUTES", default=45.0))


def be1_auto_retry_enabled() -> bool:
    return env_bool("BUDGET_BE1_AUTO_RETRY", default=True)


def be2_enabled() -> bool:
    return env_bool("BUDGET_BE2", default=True)


def be3_enabled() -> bool:
    return env_bool("BUDGET_BE3_BLOCKER", default=True)


def prereq_reset_enabled() -> bool:
    return env_bool("BUDGET_PREREQ_RESET", default=True)


def touch_active_work(state: dict[str, Any]) -> dict[str, Any]:
    """Stamp last_active_work_at (call when project is actually progressing)."""
    state["last_active_work_at"] = _iso()
    return state


def effective_elapsed_minutes(state: dict[str, Any], *, now: datetime | None = None) -> float:
    """Minutes charged against budget (active clock when enabled)."""
    now = now or _now()
    start = _parse_iso(state.get("session_started_at") or state.get("started_at"))
    if start is None:
        return 0.0
    wall = max(0.0, (now - start).total_seconds() / 60.0)
    if not active_clock_enabled():
        return wall
    last = _parse_iso(state.get("last_active_work_at")) or start
    idle = max(0.0, (now - last).total_seconds() / 60.0)
    gap = idle_gap_minutes()
    if idle > gap:
        # Paused: only charge through last activity, not calendar sleep
        return max(0.0, (last - start).total_seconds() / 60.0)
    return wall


def maybe_refresh_stale_session(
    state: dict[str, Any], *, now: datetime | None = None
) -> tuple[dict[str, Any], bool]:
    """If idle gap is large, refresh session_started_at so we don't BE on wake.

    Returns (state, refreshed).
    """
    if not active_clock_enabled():
        return state, False
    now = now or _now()
    start = _parse_iso(state.get("session_started_at"))
    if start is None:
        return state, False
    last = _parse_iso(state.get("last_active_work_at")) or start
    idle = (now - last).total_seconds() / 60.0
    if idle <= idle_gap_minutes():
        return state, False
    # Wake from long idle: fresh session window, keep pre-budget if any
    state["session_started_at"] = _iso(now)
    state["last_active_work_at"] = _iso(now)
    state["budget_session_refreshed_at"] = _iso(now)
    return state, True


def get_strikes(state: dict[str, Any]) -> int:
    try:
        return max(0, int(state.get("budget_strikes") or 0))
    except (TypeError, ValueError):
        return 0


def apply_budget_yield(
    state: dict[str, Any],
    *,
    elapsed_min: float,
    phase_budget: float,
    total_phases: int,
) -> dict[str, Any]:
    """Mark project budget_exceeded with strike increment (yield, not archive)."""
    strikes = get_strikes(state) + 1
    state["budget_strikes"] = strikes
    state["pre_budget_status"] = state.get("status", "phase_1_executing")
    state["status"] = "budget_exceeded"
    state["budget_yielded"] = True
    state["budget_note"] = (
        f"Yielded after {elapsed_min:.0f} active-min "
        f"(budget: {phase_budget:.0f} min for {total_phases}-phase project; strike={strikes})"
    )
    state["budget_yielded_at"] = _iso()
    return state


def auto_retry_clean(
    state: dict[str, Any],
    *,
    reason: str = "AUTO_RETRY_CLEAN",
) -> dict[str, Any]:
    """Resume from pre_budget_status with fresh active clock."""
    pre = state.get("pre_budget_status") or ""
    phase = state.get("phase", 1)
    if not (isinstance(pre, str) and pre.startswith("phase_")):
        pre = f"phase_{phase}_executing"
    state["status"] = pre
    state["session_started_at"] = _iso()
    state["last_active_work_at"] = _iso()
    state.pop("budget_note", None)
    state["budget_yielded"] = False
    state["last_decision"] = reason
    state["next_policy"] = state.get("next_policy") or "remain_queue"
    return state


def is_near_done(state: dict[str, Any]) -> bool:
    try:
        phase = int(state.get("phase") or 0)
        total = int(state.get("total_phases") or 1)
    except (TypeError, ValueError):
        return False
    if phase >= total:
        return True
    pre = str(state.get("pre_budget_status") or "")
    if phase >= max(1, total - 0) and any(
        x in pre for x in ("validating", "reviewing", "reviewed")
    ):
        return True
    return False


def likely_timer_glitch(state: dict[str, Any]) -> bool:
    note = str(state.get("budget_note") or "")
    m = re.search(r"after (\d+)", note)
    if m and int(m.group(1)) > 24 * 60:
        return True
    start = _parse_iso(state.get("session_started_at") or state.get("started_at"))
    if start and (_now() - start).total_seconds() > 7 * 24 * 3600:
        # multi-week session stamp
        if "active-min" not in note and "Force-completed after" in note:
            return True
    return False


def classify_blocker(
    state: dict[str, Any],
    *,
    slug: str,
    dependents_open: list[dict[str, Any]] | None = None,
    deps_status: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build blocker_report.v1 (rule-based classifier)."""
    strikes = get_strikes(state)
    near = is_near_done(state)
    timer = likely_timer_glitch(state)
    secondary: list[str] = []
    if near:
        secondary.append("near_done_unproven")
    if dependents_open:
        secondary.append("dep_chain_critical")
    if str(state.get("pre_budget_status") or "").endswith("validating"):
        secondary.append("validate_stuck")

    if timer:
        primary = "timer_glitch"
    elif near:
        primary = "near_done_unproven"
    elif any(not d.get("satisfies") for d in (deps_status or [])):
        primary = "missing_dep"
    else:
        primary = "unknown"

    recommended: list[str] = []
    if timer or strikes <= 1:
        recommended.append("AUTO_RETRY_CLEAN")
    if near:
        recommended.append("THIN_FIELD")
        recommended.append("DEBUG_AGAIN")
    else:
        recommended.append("DEBUG_AGAIN")
    if dependents_open and not near:
        recommended.append("ASK_OPERATOR")
    recommended.append("BYPASS_RETURN")
    # de-dupe preserve order
    seen: set[str] = set()
    rec_out: list[str] = []
    for r in recommended:
        if r not in seen and r in MANAGER_DECISIONS:
            seen.add(r)
            rec_out.append(r)

    report = {
        "schema": "blocker_report.v1",
        "slug": slug,
        "title": state.get("title") or slug,
        "generated_at": _iso(),
        "pipeline_dir": str(get_pipeline_dir()),
        "strike": strikes,
        "yield_reviews": int(state.get("yield_reviews") or 0) + 1,
        "status": state.get("status"),
        "phase": state.get("phase"),
        "total_phases": state.get("total_phases"),
        "pre_budget_status": state.get("pre_budget_status"),
        "budget_lock": bool(state.get("budget_lock")),
        "budget_note": (state.get("budget_note") or "")[:200],
        "blocker_class": primary,
        "secondary_classes": secondary,
        "near_done": near,
        "timer": {
            "session_started_at": state.get("session_started_at"),
            "last_active_work_at": state.get("last_active_work_at"),
            "likely_calendar_glitch": timer,
            "effective_elapsed_min": effective_elapsed_minutes(state),
        },
        "deps_status": deps_status or [],
        "dependents_open": dependents_open or [],
        "goal_relevance": "high" if dependents_open else "unknown",
        "est_fix_minutes": 45 if near else 120,
        "est_debug_pass_minutes": 30,
        "est_rebuild_minutes": 240,
        "recommended": rec_out,
        "primary_recommendation": rec_out[0] if rec_out else "ASK_OPERATOR",
        "rationale": (
            f"class={primary} strike={strikes} near_done={near} "
            f"timer_glitch={timer} open_deps={len(dependents_open or [])}"
        ),
        "next_policy": "remain_queue",
        "do_not": [
            "mark_complete_without_proof",
            "soft_satisfy_requires_as_field_proven",
            "spawn_new_ideas_that_re_require_this_slug",
        ],
        "evidence": [
            f"status={state.get('status')}",
            f"pre={state.get('pre_budget_status')}",
            f"note={(state.get('budget_note') or '')[:120]}",
        ],
        "related_skills": ["blocker-identifier", "systematic-debugging", "field-test"],
        "report_path": f"projects/{slug}/state/blocker_report.json",
    }
    return report


def write_blocker_report(slug: str, report: dict[str, Any]) -> Path:
    pd = project_dir(slug)
    state_p = pd / "state"
    state_p.mkdir(parents=True, exist_ok=True)
    path = state_p / "blocker_report.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def append_manager_decision(slug: str, decision: str, report: dict[str, Any]) -> None:
    md = state_dir() / "manager_decisions.md"
    md.parent.mkdir(parents=True, exist_ok=True)
    block = (
        f"\n## budget_ladder {slug} {_iso()}\n"
        f"- class: {report.get('blocker_class')}\n"
        f"- strike: {report.get('strike')}\n"
        f"- decision: {decision}\n"
        f"- primary: {report.get('primary_recommendation')}\n"
        f"- next_policy: {report.get('next_policy')}\n"
        f"- report: projects/{slug}/state/blocker_report.json\n"
    )
    with md.open("a", encoding="utf-8") as f:
        f.write(block)


def manager_decide(report: dict[str, Any], state: dict[str, Any]) -> str:
    """Closed rule menu — no LLM required for BE3 defaults."""
    policy = str(state.get("next_policy") or "remain_queue")
    if policy == "ask_again":
        return "ASK_OPERATOR"
    if policy == "ignore_next":
        return "IGNORE_NEXT"
    if report.get("blocker_class") == "timer_glitch":
        return "AUTO_RETRY_CLEAN"
    if report.get("near_done") and report.get("dependents_open"):
        return "THIN_FIELD"
    if report.get("near_done"):
        return "DEBUG_AGAIN"
    primary = report.get("primary_recommendation") or "BYPASS_RETURN"
    if primary in MANAGER_DECISIONS:
        return str(primary)
    return "BYPASS_RETURN"


def apply_manager_decision(
    state: dict[str, Any],
    decision: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    """Mutate state according to decision. Does not mark complete/field_proven."""
    state["yield_reviews"] = int(state.get("yield_reviews") or 0) + 1
    state["last_decision"] = decision
    state["last_decision_at"] = _iso()
    state["next_policy"] = report.get("next_policy") or "remain_queue"

    if decision == "AUTO_RETRY_CLEAN":
        return auto_retry_clean(state, reason="AUTO_RETRY_CLEAN")
    if decision == "DEBUG_AGAIN":
        state = auto_retry_clean(state, reason="DEBUG_AGAIN")
        state["be2_path"] = "debug"
        state["be2_pending"] = True
        return state
    if decision == "THIN_FIELD":
        # Prefer thin ship path if near done — leave status that field_ship can pick up
        # after complete; if still mid-phase, resume then mark field intent
        state = auto_retry_clean(state, reason="THIN_FIELD")
        state["be2_path"] = "thin_field"
        state["be2_pending"] = True
        state["prefer_thin_field"] = True
        return state
    if decision == "EXTEND_BUDGET":
        state = auto_retry_clean(state, reason="EXTEND_BUDGET")
        state["budget_extension_grants"] = int(state.get("budget_extension_grants") or 0) + 1
        return state
    if decision == "IGNORE_NEXT":
        state["seed_skip_cycles"] = int(state.get("seed_skip_cycles") or 0) + 1
        state["next_policy"] = "ignore_next"
        return state
    if decision == "ASK_OPERATOR":
        state["next_policy"] = "ask_again"
        state["awaiting_operator"] = True
        return state
    if decision == "ARCHIVE_GOAL_EDGE":
        state["next_policy"] = "ignore_until"
        state["budget_archived"] = True
        return state
    # BYPASS_RETURN / SOFT_SKIP_REQUIRES / SUBSTITUTE — keep yielded, stay parked
    if decision == "SOFT_SKIP_REQUIRES":
        state["soft_skip_requires_ok"] = True
    state["next_policy"] = "remain_queue" if decision == "BYPASS_RETURN" else state.get("next_policy")
    return state


def _deps_status_for(state: dict[str, Any]) -> list[dict[str, Any]]:
    from pipeline.dep_policy import is_full_complete

    out: list[dict[str, Any]] = []
    for dep in state.get("depends_on") or []:
        df = projects_dir() / dep / "state" / "current_idea.json"
        if not df.is_file():
            out.append({"slug": dep, "status": "missing", "satisfies": False})
            continue
        try:
            ds = json.loads(df.read_text(encoding="utf-8"))
            out.append({
                "slug": dep,
                "status": ds.get("status"),
                "satisfies": is_full_complete(ds),
            })
        except Exception:
            out.append({"slug": dep, "status": "unreadable", "satisfies": False})
    return out


def _open_dependents(slug: str) -> list[dict[str, Any]]:
    """Scan master_ideas for unchecked requires: this slug."""
    roots = [
        get_pipeline_dir() / "master_ideas.md",
        Path(__file__).resolve().parent.parent / "master_ideas.md",
    ]
    found: list[dict[str, Any]] = []
    for mi in roots:
        if not mi.is_file():
            continue
        try:
            text = mi.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for line in text.splitlines():
            if not re.search(r"^\s*[-*]?\s*\[\s*\]", line):
                continue
            m = re.search(r"requires:\s*([\w,\s_-]+)", line, re.I)
            if not m:
                continue
            reqs = [x.strip() for x in re.split(r"[,;]+", m.group(1)) if x.strip()]
            if slug not in reqs:
                continue
            t = re.search(r"\*\*\[([^\]]+)\]\*\*", line)
            found.append({
                "title": t.group(1) if t else line[:60],
                "requires": reqs,
            })
        if found:
            break
    return found


def process_budget_exceeded_project(
    slug: str,
    state: dict[str, Any],
    state_file: Path,
) -> dict[str, Any]:
    """Advance one yielded project through BE1/BE2/BE3. Returns new state."""
    if state.get("status") != "budget_exceeded":
        return state
    if state.get("awaiting_operator") or state.get("budget_archived"):
        return state
    if state.get("next_policy") == "ignore_next" and int(state.get("seed_skip_cycles") or 0) > 0:
        # consume one skip
        state["seed_skip_cycles"] = max(0, int(state.get("seed_skip_cycles") or 0) - 1)
        if state["seed_skip_cycles"] == 0:
            state["next_policy"] = "remain_queue"
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state

    strikes = get_strikes(state)

    # BE1: auto clean retry
    if strikes <= 1 and be1_auto_retry_enabled() and not state.get("be1_consumed"):
        state["be1_consumed"] = True
        state = auto_retry_clean(state, reason="AUTO_RETRY_CLEAN")
        print(f"  [budget_ladder] BE1 AUTO_RETRY_CLEAN '{slug}' → {state.get('status')}")
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state

    # BE2: mark tactical path once, then resume
    if strikes == 2 and be2_enabled() and not state.get("be2_consumed"):
        state["be2_consumed"] = True
        path = "thin_field" if is_near_done(state) else "debug"
        state = auto_retry_clean(state, reason="BE2_" + path.upper())
        state["be2_path"] = path
        state["be2_pending"] = True
        if path == "thin_field":
            state["prefer_thin_field"] = True
        print(f"  [budget_ladder] BE2 path={path} for '{slug}' → {state.get('status')}")
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state

    # BE3: blocker report + manager
    if strikes >= 3 and be3_enabled() and not state.get("be3_consumed"):
        state["be3_consumed"] = True
        deps = _deps_status_for(state)
        deps_open = _open_dependents(slug)
        report = classify_blocker(
            state, slug=slug, dependents_open=deps_open, deps_status=deps
        )
        write_blocker_report(slug, report)
        decision = manager_decide(report, state)
        report["applied_decision"] = decision
        write_blocker_report(slug, report)
        append_manager_decision(slug, decision, report)
        state = apply_manager_decision(state, decision, report)
        print(
            f"  [budget_ladder] BE3 '{slug}' class={report.get('blocker_class')} "
            f"decision={decision} → {state.get('status')}"
        )
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state

    # Locked projects: always allow clean retry
    if state.get("budget_lock") and be1_auto_retry_enabled():
        state = auto_retry_clean(state, reason="LOCKED_AUTO_RETRY")
        print(f"  [budget_ladder] locked auto-retry '{slug}' → {state.get('status')}")
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state

    return state


def tick_process_budget_yields(pipeline_dir: Path | None = None) -> int:
    """Scan projects; process budget_exceeded via ladder. Returns count processed."""
    root = (pipeline_dir or get_pipeline_dir()) / "projects"
    if not root.is_dir():
        return 0
    n = 0
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        sf = d / "state" / "current_idea.json"
        if not sf.is_file():
            continue
        try:
            st = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if st.get("status") != "budget_exceeded":
            continue
        before = json.dumps(st, sort_keys=True)
        st2 = process_budget_exceeded_project(d.name, st, sf)
        after = json.dumps(st2, sort_keys=True)
        if before != after:
            n += 1
    return n


def try_reset_be_prereq(dep_slug: str, *, waiter: str = "") -> bool:
    """If dep is unlocked budget_exceeded, reset once for dependents (BE prereq)."""
    if not prereq_reset_enabled():
        return False
    sf = projects_dir() / dep_slug / "state" / "current_idea.json"
    if not sf.is_file():
        return False
    try:
        st = json.loads(sf.read_text(encoding="utf-8"))
    except Exception:
        return False
    if st.get("status") != "budget_exceeded":
        return False
    if st.get("prereq_reset_once"):
        return False
    st["prereq_reset_once"] = True
    st["prereq_reset_for"] = waiter
    # Prefer ladder process so strikes still count
    if get_strikes(st) == 0:
        st["budget_strikes"] = 1
    st = process_budget_exceeded_project(dep_slug, st, sf)
    # If still exceeded (parked), force one clean retry for prereq unblock
    if st.get("status") == "budget_exceeded" and not st.get("awaiting_operator"):
        st = auto_retry_clean(st, reason="PREREQ_RESET")
        st["prereq_reset_once"] = True
        sf.write_text(json.dumps(st, indent=2), encoding="utf-8")
    print(
        f"  [budget_ladder] prereq reset '{dep_slug}' "
        f"(for waiter={waiter or '?'}) → {st.get('status')}"
    )
    return True
