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
  BUDGET_BE1_AUTO_RETRY=1        strike-1 auto resume (only strikes==1, not fossils)
  BUDGET_BE2=1                   strike-2 → systematic-debug or thin_field
  BUDGET_BE3_BLOCKER=1           strike-3 → blocker_report + manager decision
  BUDGET_PREREQ_RESET=1          reset unlocked BE prereq once when deps block seed
  BUDGET_LADDER_SERIAL=1         one BE recovery at a time (no mass revive)
  BUDGET_LADDER_FOCUS_TTL_HOURS=4 clear stale serial focus so queue unsticks
  BUDGET_THIN_FIELD_TICK=1       consume prefer_thin_field → run_thin_field_ship

Note: "1000 retries" in budget_note is lifetime phase_retries sum corruption /
cap path — not wall-clock minutes of a short overnight.
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


def ladder_serial_enabled() -> bool:
    """Only one BE recovery in flight; never mass-revive the graveyard."""
    return env_bool("BUDGET_LADDER_SERIAL", default=True)


def thin_field_tick_enabled() -> bool:
    """Consume prefer_thin_field via thin field ship on the health tick."""
    return env_bool("BUDGET_THIN_FIELD_TICK", default=True)


def prefer_thin_field_ready(state: dict[str, Any]) -> bool:
    """True when BE2 thin_field flag is set and project is ready to field-prove.

    Ready if complete/complete_with_bugs, or near-done (phases finished) and not
    still budget_exceeded / dep_waiting.
    """
    if not state.get("prefer_thin_field"):
        return False
    if state.get("prefer_thin_field_shipped"):
        return False
    status = str(state.get("status") or "")
    if status in ("field_proven", "ship_insufficient", "deeper_work_needed"):
        return False
    if status in ("complete", "complete_with_bugs"):
        return True
    if status in ("budget_exceeded", "dep_waiting", "evicted", ""):
        return False
    # Near-done after BE2 resume (e.g. phase_3_validating with phase>=total)
    return is_near_done(state)


def focus_ttl_hours() -> float:
    """Hours after which serial ladder focus is cleared (default 4)."""
    return max(0.25, env_float("BUDGET_LADDER_FOCUS_TTL_HOURS", default=4.0))


def focus_is_expired(focus: dict[str, Any] | None) -> bool:
    if not focus:
        return False
    since = _parse_iso(focus.get("since") if isinstance(focus.get("since"), str) else None)
    if since is None:
        return False
    age_h = (_now() - since).total_seconds() / 3600.0
    return age_h >= focus_ttl_hours()


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
        # Re-arm a new systematic-debug pass (prior BE2 may have left these True)
        state["be2_debug_enqueued"] = False
        state["be2_debug_attempted"] = False
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


_LADDER_DONE = frozenset({
    "complete",
    "complete_with_bugs",
    "field_proven",
    "mvp_complete",
    "deeper_work_needed",
    "ship_insufficient",
    "evicted",
})


def is_lifetime_retry_fossil(state: dict[str, Any]) -> bool:
    """True if note is the lifetime-retry cap (often inflated counters, not real work)."""
    note = str(state.get("budget_note") or "")
    return "total retries across all phases" in note.lower() or "lifetime" in note.lower()


def is_ladder_eligible(state: dict[str, Any]) -> bool:
    """Whether this BE may be advanced by the serial ladder.

    Fossils (strikes==0, never yielded by active-clock ladder) stay parked.
    Real yields set budget_strikes via apply_budget_yield.
    """
    if state.get("status") != "budget_exceeded":
        return False
    if state.get("awaiting_operator") or state.get("budget_archived"):
        return False
    # BE3 parked (BYPASS/ARCHIVE/IGNORE) — no further auto ladder step
    if state.get("be3_consumed"):
        return False
    strikes = get_strikes(state)
    if strikes >= 1:
        return True
    if state.get("budget_lock"):
        return True
    if state.get("budget_yielded") and state.get("budget_yielded_at"):
        return True
    # Explicit prereq path may set this
    if state.get("prereq_reset_for") or state.get("force_ladder"):
        return True
    return False


def ladder_focus_path(pipeline_dir: Path | None = None) -> Path:
    root = pipeline_dir or get_pipeline_dir()
    return root / "state" / "budget_ladder_focus.json"


def read_ladder_focus(pipeline_dir: Path | None = None) -> dict[str, Any] | None:
    p = ladder_focus_path(pipeline_dir)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def write_ladder_focus(
    slug: str,
    *,
    stage: str,
    pipeline_dir: Path | None = None,
) -> None:
    p = ladder_focus_path(pipeline_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps({"slug": slug, "stage": stage, "since": _iso()}, indent=2),
        encoding="utf-8",
    )


def clear_ladder_focus(pipeline_dir: Path | None = None, *, slug: str | None = None) -> None:
    p = ladder_focus_path(pipeline_dir)
    if not p.is_file():
        return
    if slug:
        cur = read_ladder_focus(pipeline_dir)
        if cur and cur.get("slug") != slug:
            return
    try:
        p.unlink()
    except OSError:
        pass


def seed_serial_blocked(
    slug: str,
    focus: dict[str, Any] | None = None,
    *,
    pipeline_dir: Path | None = None,
    clear_expired: bool = True,
) -> bool:
    """True if seed must not advance *slug* because another serial focus is in-flight.

    Expired focus (TTL) does not block; when *clear_expired* it is cleared on disk.
    If *focus* is omitted, reads current ladder focus from *pipeline_dir*.
    """
    if not ladder_serial_enabled():
        return False
    if focus is None:
        focus = read_ladder_focus(pipeline_dir)
    if not focus or not focus.get("slug"):
        return False
    if focus_is_expired(focus):
        if clear_expired:
            clear_ladder_focus(pipeline_dir, slug=str(focus.get("slug")))
        return False
    return str(focus.get("slug")) != slug


def try_seed_process_budget_exceeded(
    slug: str,
    state: dict[str, Any],
    state_file: Path,
    *,
    pipeline_dir: Path | None = None,
    bus: Any | None = None,
) -> dict[str, Any]:
    """Seed-path BE advance used by list seeding.

    - Honors serial focus + TTL (never parallel with another in-flight recovery).
    - Advances only BE1 (strikes==1); BE2/BE3 need bus via tick.
    - Locked resume (budget_lock, be1 not consumed) also honors serial_block.
    """
    if state.get("status") != "budget_exceeded":
        return state
    serial_block = seed_serial_blocked(slug, pipeline_dir=pipeline_dir)
    # Seed only advances BE1 (strikes==1). BE2 needs bus via tick;
    # BE3 is manager path — both must not race seed without bus.
    if (
        is_ladder_eligible(state)
        and not serial_block
        and get_strikes(state) == 1
    ):
        return process_budget_exceeded_project(
            slug, state, state_file, bus=bus, pipeline_dir=pipeline_dir
        )
    if (
        state.get("budget_lock")
        and not state.get("be1_consumed")
        and not serial_block
    ):
        # Locked: one resume even if strike metadata missing
        # (still honor serial — never parallel with another focus)
        state["force_ladder"] = True
        return process_budget_exceeded_project(
            slug,
            state,
            state_file,
            bus=bus,
            allow_ineligible=True,
            pipeline_dir=pipeline_dir,
        )
    return state


def _ladder_fully_consumed_parked(st: dict[str, Any]) -> bool:
    """True when no further ladder step can run (BE3 done / parked decisions)."""
    if st.get("awaiting_operator") or st.get("budget_archived"):
        return True
    if st.get("be3_consumed") and st.get("status") == "budget_exceeded":
        # BYPASS_RETURN / ARCHIVE / IGNORE leave BE parked — not mid-flight
        return True
    if (
        st.get("be1_consumed")
        and st.get("be2_consumed")
        and st.get("be3_consumed")
        and st.get("status") == "budget_exceeded"
    ):
        return True
    return False


def _project_still_ladder_inflight(st: dict[str, Any]) -> bool:
    """True if we already started BE1/BE2 on this project and it is not done/BE again."""
    if st.get("status") in _LADDER_DONE:
        return False
    if _ladder_fully_consumed_parked(st):
        return False
    if st.get("status") == "budget_exceeded":
        # Waiting for next strike step — still the focus (BE1/BE2 done, more strikes later)
        return bool(st.get("be1_consumed") or st.get("be2_consumed"))
    # Mid-flight after clean retry
    return bool(
        st.get("be1_consumed")
        or st.get("be2_pending")
        or st.get("be2_consumed")
        or st.get("ladder_focus")
    )


def try_enqueue_be2_debug(slug: str, state: dict[str, Any], bus: Any | None) -> bool:
    """Enqueue one systematic-debug executor pass for BE2 debug path. Returns True if sent.

    Does **not** call try_enqueue_pre_force_debug (avoids mid-step disk write /
    mark_attempted race on current_idea.json). Builds payload in-memory only;
    caller sets be2_debug_attempted / be2_debug_enqueued and does a single write.
    """
    if bus is None:
        return False
    if state.get("be2_path") != "debug" or not state.get("be2_pending"):
        return False
    if state.get("be2_debug_enqueued") or state.get("be2_debug_attempted"):
        return False
    phase = int(state.get("phase") or 1)
    try:
        from pipeline.pre_force_debug import build_systematic_debug_instructions
        from pipeline.message_bus import Message

        instructions = build_systematic_debug_instructions(
            idea_slug=slug,
            phase=phase,
            validation_excerpt=(state.get("budget_note") or "")[:2000],
        )
        proj = project_dir(slug)
        payload = {
            "phase": phase,
            "tasks_path": f"phases/phase_{phase}/tasks.md",
            "workspace_path": str(proj / "workspace"),
            "fix_required": True,
            "fix_report_path": f"phases/phase_{phase}/fix_report.md",
            "fix_instructions": (
                "# BE2 SYSTEMATIC DEBUG (budget ladder strike 2)\n\n" + instructions
            ),
            "idea_slug": slug,
            "retry_count": get_strikes(state),
            "systematic_debug": True,
            "be2_debug": True,
        }
        bus.send(
            Message.create(
                from_agent="manager",
                to_agent="executor",
                type="task",
                payload=payload,
            )
        )
        return True
    except Exception as exc:
        print(f"  [budget_ladder] BE2 debug enqueue failed for '{slug}': {exc}")
        return False


def _try_complete_pending_be2_enqueue(
    slug: str,
    state: dict[str, Any],
    state_file: Path,
    bus: Any | None,
) -> bool:
    """If BE2 already resumed with pending debug and bus is available, enqueue once."""
    if bus is None:
        return False
    if state.get("status") == "budget_exceeded":
        return False
    if state.get("be2_path") != "debug":
        return False
    if not state.get("be2_pending") or state.get("be2_debug_enqueued"):
        return False
    enq = try_enqueue_be2_debug(slug, state, bus)
    if not enq:
        return False
    state["be2_debug_enqueued"] = True
    state["be2_debug_attempted"] = True
    state["be2_pending"] = False
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"  [budget_ladder] BE2 systematic-debug enqueued (late) for '{slug}'")
    return True


def process_budget_exceeded_project(
    slug: str,
    state: dict[str, Any],
    state_file: Path,
    *,
    bus: Any | None = None,
    pipeline_dir: Path | None = None,
    allow_ineligible: bool = False,
) -> dict[str, Any]:
    """Advance one yielded project one ladder step (BE1 or BE2 or BE3).

    Does **not** revive strike-0 fossils unless allow_ineligible / lock / prereq.
    """
    if state.get("status") != "budget_exceeded":
        return state
    if state.get("awaiting_operator") or state.get("budget_archived"):
        return state
    if state.get("next_policy") == "ignore_next" and int(state.get("seed_skip_cycles") or 0) > 0:
        state["seed_skip_cycles"] = max(0, int(state.get("seed_skip_cycles") or 0) - 1)
        if state["seed_skip_cycles"] == 0:
            state["next_policy"] = "remain_queue"
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state

    strikes = get_strikes(state)

    # --- Eligibility: never mass-revive strike-0 classic graveyard ---
    if not allow_ineligible and not is_ladder_eligible(state):
        # Stay budget_exceeded; overnight ignores
        return state

    # Normalize: first real entry into ladder without strikes (lock / prereq)
    if strikes < 1 and (state.get("budget_lock") or allow_ineligible or state.get("force_ladder")):
        state["budget_strikes"] = 1
        strikes = 1

    # BE1: exactly strike 1, clean retry only (not strikes==0 fossils)
    if (
        strikes == 1
        and be1_auto_retry_enabled()
        and not state.get("be1_consumed")
    ):
        state["be1_consumed"] = True
        state["ladder_focus"] = True
        state = auto_retry_clean(state, reason="AUTO_RETRY_CLEAN")
        write_ladder_focus(slug, stage="be1", pipeline_dir=pipeline_dir)
        print(f"  [budget_ladder] BE1 AUTO_RETRY_CLEAN '{slug}' → {state.get('status')}")
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state

    # BE2: strike 2 → systematic-debug or thin_field (real work, not just a flag)
    if strikes == 2 and be2_enabled() and not state.get("be2_consumed"):
        path = "thin_field" if is_near_done(state) else "debug"
        # Debug path needs a bus to enqueue real work. Without bus, do not
        # consume BE2 so a later tick (with bus) can retry. thin_field is
        # flag-only and may proceed without bus.
        if path == "debug" and bus is None:
            print(
                f"  [budget_ladder] BE2 path=debug for '{slug}' deferred "
                f"(no bus — leave budget_exceeded for tick)"
            )
            return state

        state["be2_consumed"] = True
        state["ladder_focus"] = True
        state = auto_retry_clean(state, reason="BE2_" + path.upper())
        state["be2_path"] = path
        state["be2_pending"] = True
        if path == "thin_field":
            state["prefer_thin_field"] = True
        write_ladder_focus(slug, stage="be2", pipeline_dir=pipeline_dir)
        enq = False
        if path == "debug":
            enq = try_enqueue_be2_debug(slug, state, bus)
            if enq:
                state["be2_debug_enqueued"] = True
                state["be2_debug_attempted"] = True
                state["be2_pending"] = False  # hand off to executor
        print(
            f"  [budget_ladder] BE2 path={path} for '{slug}' → {state.get('status')}"
            + (" (systematic-debug enqueued)" if enq else "")
        )
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state

    # BE3: strike ≥3 → report + manager
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
        # BE3 DEBUG_AGAIN re-arms debug; enqueue immediately when bus available
        enq = False
        if (
            decision == "DEBUG_AGAIN"
            and state.get("be2_path") == "debug"
            and state.get("be2_pending")
            and bus is not None
        ):
            enq = try_enqueue_be2_debug(slug, state, bus)
            if enq:
                state["be2_debug_enqueued"] = True
                state["be2_debug_attempted"] = True
                state["be2_pending"] = False
        write_ladder_focus(slug, stage="be3", pipeline_dir=pipeline_dir)
        # Clear focus when parked / no further ladder step (not mid-resume work)
        if (
            state.get("status") in _LADDER_DONE
            or state.get("awaiting_operator")
            or state.get("budget_archived")
            or state.get("status") == "budget_exceeded"
        ):
            clear_ladder_focus(pipeline_dir, slug=slug)
            state["ladder_focus"] = False
        print(
            f"  [budget_ladder] BE3 '{slug}' class={report.get('blocker_class')} "
            f"decision={decision} → {state.get('status')}"
            + (" (systematic-debug enqueued)" if enq else "")
        )
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state

    # Locked, strike still 0 after normalize failed: one locked wake only
    if state.get("budget_lock") and be1_auto_retry_enabled() and not state.get("be1_consumed"):
        state["budget_strikes"] = max(1, strikes)
        state["be1_consumed"] = True
        state = auto_retry_clean(state, reason="LOCKED_AUTO_RETRY")
        write_ladder_focus(slug, stage="be1_lock", pipeline_dir=pipeline_dir)
        print(f"  [budget_ladder] locked auto-retry '{slug}' → {state.get('status')}")
        state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state

    return state


def _priority_key(slug: str, st: dict[str, Any]) -> tuple:
    """Higher priority first: open dependents, non-fossil, recent yield."""
    deps = _open_dependents(slug)
    has_deps = 1 if deps else 0
    fossil = 0 if is_lifetime_retry_fossil(st) else 1
    strikes = get_strikes(st)
    # Prefer higher strikes already mid-ladder (BE2 before new BE1 of others)
    return (-has_deps, -strikes, -fossil, slug)


def tick_process_budget_yields(
    pipeline_dir: Path | None = None,
    bus: Any | None = None,
) -> int:
    """Process **at most one** eligible budget_exceeded project per tick.

    Serial by default: if a ladder focus is already in-flight, do not revive others.
    """
    root = Path(pipeline_dir) if pipeline_dir else get_pipeline_dir()
    projects = root / "projects"
    if not projects.is_dir():
        return 0

    # Clear focus if target finished, parked, TTL expired, or cannot advance
    focus = read_ladder_focus(root)
    if focus and focus.get("slug"):
        fslug = str(focus["slug"])
        if focus_is_expired(focus):
            clear_ladder_focus(root, slug=fslug)
            print(f"  [budget_ladder] focus TTL expired for '{fslug}' — cleared")
            focus = None
        else:
            fsf = projects / fslug / "state" / "current_idea.json"
            if fsf.is_file():
                try:
                    fst = json.loads(fsf.read_text(encoding="utf-8"))
                    if (
                        fst.get("status") in _LADDER_DONE
                        or _ladder_fully_consumed_parked(fst)
                        or not _project_still_ladder_inflight(fst)
                    ):
                        clear_ladder_focus(root, slug=fslug)
                        focus = None
                    elif ladder_serial_enabled() and _project_still_ladder_inflight(fst):
                        # Late BE2 enqueue if already resumed without bus
                        if _try_complete_pending_be2_enqueue(fslug, fst, fsf, bus):
                            return 1
                        # Only advance this slug if it is BE again (strike 2/3)
                        if fst.get("status") == "budget_exceeded":
                            before = json.dumps(fst, sort_keys=True)
                            fst2 = process_budget_exceeded_project(
                                fslug, fst, fsf, bus=bus, pipeline_dir=root
                            )
                            if json.dumps(fst2, sort_keys=True) != before:
                                return 1
                            # Unchanged — release focus so other eligible BE can proceed
                            clear_ladder_focus(root, slug=fslug)
                            focus = None
                        else:
                            # Still working mid-phase — do not start other BE recoveries
                            return 0
                except Exception as _focus_exc:
                    # Fail closed under serial: do not advance another BE while
                    # the focus target is unreadable / process blew up.
                    print(
                        f"  [budget_ladder] focus error for '{fslug}': {_focus_exc}"
                        + (" — hold serial" if ladder_serial_enabled() else " — clear focus")
                    )
                    if ladder_serial_enabled():
                        return 0
                    clear_ladder_focus(root, slug=fslug)
                    focus = None
            else:
                # Focus target missing — clear stale lock
                clear_ladder_focus(root, slug=fslug)
                focus = None

    candidates: list[tuple[tuple, str, Path, dict[str, Any]]] = []
    for d in projects.iterdir():
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
        if not is_ladder_eligible(st):
            continue
        candidates.append((_priority_key(d.name, st), d.name, sf, st))

    if not candidates:
        return 0

    candidates.sort(key=lambda x: x[0])
    _prio, slug, sf, st = candidates[0]
    before = json.dumps(st, sort_keys=True)
    st2 = process_budget_exceeded_project(
        slug, st, sf, bus=bus, pipeline_dir=root
    )
    return 1 if json.dumps(st2, sort_keys=True) != before else 0


def try_reset_be_prereq(
    dep_slug: str,
    *,
    waiter: str = "",
    bus: Any | None = None,
) -> bool:
    """If dep is budget_exceeded, one serial ladder step for chain unblock.

    Honors BUDGET_LADDER_SERIAL: if another slug owns an in-flight focus, leave
    the waiter blocked (return False). Optional bus enables BE2 debug enqueue.
    """
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
    if st.get("prereq_reset_once") and st.get("be1_consumed"):
        return False

    # Serial: do not start a parallel recovery while another focus is in-flight
    if ladder_serial_enabled():
        focus = read_ladder_focus()
        if focus and focus.get("slug") and focus.get("slug") != dep_slug:
            if not focus_is_expired(focus):
                # Confirm the other focus is still meaningfully in-flight
                other = str(focus["slug"])
                other_sf = projects_dir() / other / "state" / "current_idea.json"
                still = True
                if other_sf.is_file():
                    try:
                        ost = json.loads(other_sf.read_text(encoding="utf-8"))
                        still = _project_still_ladder_inflight(ost)
                    except Exception:
                        still = True
                if still:
                    return False
                clear_ladder_focus(slug=other)
            else:
                clear_ladder_focus(slug=str(focus["slug"]))

    st["prereq_reset_for"] = waiter
    st["force_ladder"] = True
    if get_strikes(st) < 1:
        st["budget_strikes"] = 1
    before_status = st.get("status")
    before_consumed = (
        bool(st.get("be1_consumed")),
        bool(st.get("be2_consumed")),
        bool(st.get("be3_consumed")),
    )
    st = process_budget_exceeded_project(
        dep_slug,
        st,
        sf,
        bus=bus,
        allow_ineligible=True,
        pipeline_dir=get_pipeline_dir(),
    )
    advanced = (
        st.get("status") != before_status
        or (
            bool(st.get("be1_consumed")),
            bool(st.get("be2_consumed")),
            bool(st.get("be3_consumed")),
        )
        != before_consumed
    )
    if not advanced:
        # e.g. BE2 debug deferred without bus — do not burn prereq_reset_once
        print(
            f"  [budget_ladder] prereq ladder step '{dep_slug}' deferred "
            f"(for waiter={waiter or '?'}; no advance — leave for tick/bus)"
        )
        return False
    st["prereq_reset_once"] = True
    sf.write_text(json.dumps(st, indent=2), encoding="utf-8")
    print(
        f"  [budget_ladder] prereq ladder step '{dep_slug}' "
        f"(for waiter={waiter or '?'}) → {st.get('status')}"
    )
    return True


def tick_prefer_thin_field_ship(
    pipeline_dir: Path | None = None,
    *,
    limit: int = 1,
) -> int:
    """Run thin field ship for BE2 prefer_thin_field projects that are ready.

    At most *limit* projects per tick (default 1 — serial-friendly).
    Clears prefer_thin_field after a ship attempt (success or fail terminal).
    """
    if not thin_field_tick_enabled():
        return 0
    root = Path(pipeline_dir) if pipeline_dir else get_pipeline_dir()
    projects = root / "projects"
    if not projects.is_dir():
        return 0

    try:
        from pipeline.engines.field_ship import run_thin_field_ship
    except Exception as exc:
        print(f"  [budget_ladder] thin_field import failed: {exc}")
        return 0

    n = 0
    for d in sorted(projects.iterdir()):
        if n >= max(1, limit):
            break
        if not d.is_dir():
            continue
        sf = d / "state" / "current_idea.json"
        if not sf.is_file():
            continue
        try:
            st = json.loads(sf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not prefer_thin_field_ready(st):
            continue

        slug = d.name
        print(
            f"  [budget_ladder] BE2 thin_field ship '{slug}' "
            f"(status={st.get('status')} phase={st.get('phase')}/{st.get('total_phases')})"
        )
        try:
            # Ensure classic/unknown engines still allowed (prefer_thin_field in thin_ship_enabled)
            ship = run_thin_field_ship(d, st, slug=slug)
            # Reload state after ship mutates disk
            try:
                st2 = json.loads(sf.read_text(encoding="utf-8"))
            except Exception:
                st2 = dict(st)
            st2["prefer_thin_field_shipped"] = True
            st2["prefer_thin_field"] = False
            st2["be2_pending"] = False
            st2["last_decision"] = st2.get("last_decision") or "THIN_FIELD"
            st2["thin_field_ship_status"] = getattr(ship, "status", "") or ""
            st2["thin_field_ship_reason"] = (getattr(ship, "reason", "") or "")[:300]
            if getattr(ship, "ok", False) or st2.get("status") == "field_proven":
                clear_ladder_focus(root, slug=slug)
            sf.write_text(json.dumps(st2, indent=2), encoding="utf-8")
            print(
                f"  [budget_ladder] thin_field ship '{slug}' → "
                f"status={st2.get('status')} ship={getattr(ship, 'status', '?')} "
                f"ok={getattr(ship, 'ok', False)}"
            )
            n += 1
        except Exception as exc:
            print(f"  [budget_ladder] thin_field ship '{slug}' failed: {exc}")
            try:
                st["prefer_thin_field_shipped"] = True
                st["prefer_thin_field_error"] = str(exc)[:300]
                sf.write_text(json.dumps(st, indent=2), encoding="utf-8")
            except Exception:
                pass
            n += 1
    return n
