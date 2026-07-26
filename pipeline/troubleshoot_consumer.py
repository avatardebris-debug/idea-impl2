"""
Troubleshoot-gate recovery consumer (v0).

Serial health-tick consumer for projects stuck at ship_insufficient (or
deeper_work_needed with a recovery decision). Honors cheap recovery actions
or escalates to budget_exceeded so the BE ladder can pick up overnight.

Does **not** call an LLM. Does **not** spawn replan / idea-plan agents.

Env:
  TROUBLESHOOT_CONSUMER=1   (default on) — enable this tick
  TROUBLESHOOT_MAX_ACTS=2   max auto-acts per ship_outcome episode (fingerprint)

Policy notes:
  - Effective cheap re-arm is **1 per fail_fingerprint** (same-fp after act → yield).
    TROUBLESHOOT_MAX_ACTS is a backstop for missing/mismatched fingerprints.
  - Cheap re-arm only when phase >= total so prefer_thin_field_ready accepts the
    project (status forced to complete / complete_with_bugs). Mid-phase → yield.
  - Consumer yields set pre_budget_status to a restorable phase_* status so BE1
    auto_retry_clean does not demote via ship_insufficient → phase_N_executing.
  - BE yields created this tick wait until the next health cycle for ladder pickup
    (order: ladder → consumer → thin ship; thin re-arm same-cycle preferred).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.env_flags import env_bool, env_int
from pipeline.paths import get_pipeline_dir
from pipeline.troubleshoot_gate import (
    ACTION_AMBIGUOUS,
    ACTION_ASK_OPERATOR,
    ACTION_DEBUG_TARGETED,
    ACTION_FIELD_REPAIR_ONCE,
    ACTION_FIX_GATE_ONLY,
    ACTION_PARK,
    ACTION_REPLAN_MASTER,
    ACTION_REPLAN_PHASE,
    ACTION_THIN_FIELD_RETRY,
)

# Surface-only / not auto-implemented in v0 → escalate to budget_exceeded
ESCALATE_ACTIONS = frozenset(
    {
        ACTION_PARK,
        ACTION_ASK_OPERATOR,
        ACTION_AMBIGUOUS,
        ACTION_REPLAN_PHASE,
        ACTION_REPLAN_MASTER,
    }
)

# Cheap actions the consumer can re-arm for thin-field / gate recovery
CHEAP_ACTIONS = frozenset(
    {
        ACTION_FIX_GATE_ONLY,
        ACTION_THIN_FIELD_RETRY,
        ACTION_FIELD_REPAIR_ONCE,
        ACTION_DEBUG_TARGETED,
    }
)

ELIGIBLE_STATUSES = frozenset({"ship_insufficient", "deeper_work_needed"})


def troubleshoot_consumer_enabled() -> bool:
    """Default on — match BUDGET_* pattern via env_bool."""
    return env_bool("TROUBLESHOOT_CONSUMER", default=True)


def max_recovery_acts() -> int:
    return max(1, env_int("TROUBLESHOOT_MAX_ACTS", default=2))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_state(sf: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(sf.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _write_state(sf: Path, state: dict[str, Any]) -> None:
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _load_decision(project_dir: Path) -> dict[str, Any] | None:
    path = project_dir / "state" / "recovery_decision.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _phase_total(state: dict[str, Any]) -> tuple[int, int]:
    try:
        phase = int(state.get("phase") or 0)
        total = int(state.get("total_phases") or 1) or 1
    except (TypeError, ValueError):
        return 0, 1
    return phase, total


def _is_phase_done(state: dict[str, Any]) -> bool:
    phase, total = _phase_total(state)
    return total > 0 and phase >= total


def _is_eligible(state: dict[str, Any], project_dir: Path) -> bool:
    status = str(state.get("status") or "")
    if status == "field_proven":
        return False
    if status not in ELIGIBLE_STATUSES:
        return False
    has_action = bool(state.get("last_recovery_action"))
    has_decision = (project_dir / "state" / "recovery_decision.json").is_file()
    if not has_action and not has_decision:
        return False
    return True


def _resolve_action_and_meta(
    state: dict[str, Any],
    decision: dict[str, Any] | None,
) -> tuple[str, str, str, str]:
    """Return (action, primary_class, fail_fingerprint, prompt_inject)."""
    action = ""
    primary = ""
    fp = ""
    prompt = ""
    if decision:
        action = str(decision.get("recommended_action") or "").strip()
        primary = str(decision.get("primary_class") or "").strip()
        fp = str(decision.get("fail_fingerprint") or "").strip()
        prompt = str(decision.get("prompt_inject") or "").strip()
    if not action:
        action = str(state.get("last_recovery_action") or "").strip()
    if not primary:
        primary = str(state.get("last_recovery_class") or "").strip()
    if not fp:
        fp = str(state.get("recovery_acted_fingerprint") or "").strip()
    return action, primary, fp, prompt


def restorable_pre_budget_status(state: dict[str, Any]) -> str:
    """phase_* status BE1 auto_retry_clean can restore without demoting blindly.

    Ship terminals (ship_insufficient / deeper_work_needed) are not phase_*, so
    auto_retry_clean would otherwise invent phase_N_executing. Prefer ship-adjacent
    near-done statuses when phases are finished.
    """
    phase, total = _phase_total(state)
    ph = max(1, phase or 1)
    cur = str(state.get("status") or "")
    if isinstance(cur, str) and cur.startswith("phase_"):
        return cur
    if cur in ("complete", "complete_with_bugs"):
        # Keep complete-shaped resume when already there (auto_retry_clean demotes
        # non-phase_* to executing; map to near-done validating for ladder).
        return f"phase_{max(ph, total)}_validating"
    if total > 0 and phase >= total:
        # Near-done after ship stall — BE1 resumes here; BE2 thin_field if re-yielded
        return f"phase_{ph}_validating"
    return f"phase_{ph}_executing"


def _rearm_prefer_thin(
    state: dict[str, Any],
    *,
    reason: str,
    debug_hint: str = "",
) -> dict[str, Any]:
    """Set prefer_thin flags + thin-ready status for tick_prefer_thin_field_ship.

    Caller must only invoke when phase >= total. prefer_thin_field_ready accepts
    complete / complete_with_bugs (and is_near_done phase statuses); we force
    complete so the thin tick always sees a ready project after re-arm.
    """
    cur = str(state.get("status") or "")
    if cur not in ("complete", "complete_with_bugs"):
        state["status"] = "complete"

    state["prefer_thin_field"] = True
    state["prefer_thin_field_shipped"] = False
    state.pop("prefer_thin_field_error", None)
    # Do not set be2_pending / be2_path — ladder owns those; pure consumer re-arm
    state["last_decision"] = reason
    state["recovery_consumer_at"] = _utc_now()
    state["recovery_consumer_action"] = reason
    if debug_hint:
        state["recovery_debug_hint"] = debug_hint[:500]
    # Clear sticky ship outcome so a fresh thin ship can re-stamp it
    state.pop("ship_outcome", None)
    state.pop("ship_outcome_at", None)
    return state


def _yield_to_budget(
    state: dict[str, Any],
    *,
    action: str,
    primary: str,
    fingerprint: str,
    reason_detail: str = "",
    slug: str | None = None,
) -> dict[str, Any]:
    """Escalate stuck recovery to budget_exceeded via apply_budget_yield."""
    from pipeline.budget_ladder import apply_budget_yield

    try:
        total = int(state.get("total_phases") or 1) or 1
    except (TypeError, ValueError):
        total = 1

    ship_status = str(state.get("status") or "ship_insufficient")
    # Restorable for BE1 — not ship_insufficient alone
    pre = restorable_pre_budget_status(state)

    state = apply_budget_yield(
        state,
        elapsed_min=0.0,
        phase_budget=0.0,
        total_phases=total,
        slug=slug or state.get("slug") or state.get("_slug"),
        # Recovery must stay budget_exceeded for ladder — do not auto-convert
        classic_to_grok=False,
    )
    state["pre_budget_status"] = pre
    state["recovery_ship_status"] = ship_status
    note = (
        f"Ship recovery exhausted: action={action or 'none'} "
        f"class={primary or 'unknown'} fingerprint={fingerprint or 'none'} "
        f"prior={ship_status} resume={pre}"
    )
    if reason_detail:
        note = f"{note} ({reason_detail})"
    state["budget_note"] = note[:500]
    state["recovery_yielded"] = True
    state["recovery_yielded_at"] = _utc_now()
    state["recovery_yield_action"] = action or "none"
    # Do not leave prefer_thin armed on yield
    state["prefer_thin_field"] = False
    return state


def _append_consumer_trace(
    project_dir: Path,
    *,
    slug: str,
    tag: str,
    action: str,
    primary: str,
    fingerprint: str,
    state: dict[str, Any],
) -> None:
    """Durable consume event so reboot/shutdown can reconstruct recovery path.

    Appends to project recovery_history.jsonl and pipeline metrics history.
    Never deletes prior traces (KEEP_GOAL_TRACES / default keep).
    """
    event = {
        "schema": "recovery_consume.v1",
        "ts": _utc_now(),
        "slug": slug,
        "tag": tag,  # acted | yielded
        "action": action,
        "primary_class": primary,
        "fail_fingerprint": fingerprint,
        "status_after": state.get("status"),
        "prefer_thin_field": bool(state.get("prefer_thin_field")),
        "recovery_act_count": state.get("recovery_act_count"),
        "budget_note": (state.get("budget_note") or "")[:300],
    }
    try:
        state_dir = project_dir / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        hist = state_dir / "recovery_history.jsonl"
        with hist.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        print(
            f"[troubleshoot_consumer] warn: recovery_history write failed for {slug}: {e}",
            flush=True,
        )
    try:
        root = get_pipeline_dir()
        metrics = root / "metrics"
        metrics.mkdir(parents=True, exist_ok=True)
        pipe_hist = metrics / "troubleshoot_consumer_history.jsonl"
        with pipe_hist.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        print(
            f"[troubleshoot_consumer] warn: metrics history write failed for {slug}: {e}",
            flush=True,
        )


def process_troubleshoot_project(
    project_dir: Path,
    state: dict[str, Any],
    *,
    bus: Any = None,
) -> tuple[dict[str, Any], str]:
    """Act on one eligible project. Returns (new_state, result_tag).

    result_tag is one of: acted, yielded.
    """
    del bus  # reserved for future safe enqueue; unused in v0
    project_dir = Path(project_dir)
    # Ensure slug is available for classic→grok auto-convert on yield
    if not state.get("slug") and not state.get("_slug"):
        state["slug"] = project_dir.name
    decision = _load_decision(project_dir)
    action, primary, fp, prompt = _resolve_action_and_meta(state, decision)

    # Empty fingerprint thrash: synthesize stable episode key so same-fp
    # anti-thrash and act budget still work when gate omitted fail_fingerprint.
    if not fp:
        slug_key = str(state.get("slug") or state.get("_slug") or project_dir.name)
        fp = f"no_fp:{slug_key}:{action or 'none'}:{primary or 'none'}"

    # Episode tracking: new fingerprint → fresh act budget
    episode_fp = str(state.get("recovery_episode_fingerprint") or "")
    if fp and episode_fp and episode_fp != fp:
        state["recovery_act_count"] = 0
        state["recovery_field_repair_acts"] = 0
        # keep recovery_acted_fingerprint for double-act across same-fp only
    if fp:
        state["recovery_episode_fingerprint"] = fp

    act_count = 0
    try:
        act_count = max(0, int(state.get("recovery_act_count") or 0))
    except (TypeError, ValueError):
        act_count = 0

    acted_fp = str(state.get("recovery_acted_fingerprint") or "")
    max_acts = max_recovery_acts()

    # 1) Same fail_fingerprint after an auto-act already applied → yield (no thrash)
    if acted_fp and fp and acted_fp == fp and act_count > 0:
        state = _yield_to_budget(
            state,
            action=action,
            primary=primary,
            fingerprint=fp,
            reason_detail="same_fingerprint_after_act",
        )
        return state, "yielded"

    # 2) Act budget exhausted for this episode
    if act_count >= max_acts:
        state = _yield_to_budget(
            state,
            action=action,
            primary=primary,
            fingerprint=fp,
            reason_detail=f"max_acts={max_acts}",
        )
        return state, "yielded"

    # 3) Escalate surface-only / unknown actions
    if not action or action in ESCALATE_ACTIONS or action not in CHEAP_ACTIONS:
        state = _yield_to_budget(
            state,
            action=action or "none",
            primary=primary,
            fingerprint=fp,
            reason_detail="escalate_or_unknown",
        )
        return state, "yielded"

    # 4) Cheap acts require thin-ready phase (phase >= total). Mid-phase → yield.
    if not _is_phase_done(state):
        state = _yield_to_budget(
            state,
            action=action,
            primary=primary,
            fingerprint=fp,
            reason_detail="mid_phase_not_thin_ready",
        )
        return state, "yielded"

    # 5) FIELD_REPAIR_ONCE — only one re-arm; second time yields
    if action == ACTION_FIELD_REPAIR_ONCE:
        try:
            repair_acts = max(0, int(state.get("recovery_field_repair_acts") or 0))
        except (TypeError, ValueError):
            repair_acts = 0
        if repair_acts >= 1:
            state = _yield_to_budget(
                state,
                action=action,
                primary=primary,
                fingerprint=fp,
                reason_detail="field_repair_once_exhausted",
            )
            return state, "yielded"
        state = _rearm_prefer_thin(state, reason=ACTION_FIELD_REPAIR_ONCE)
        state["recovery_field_repair_acts"] = repair_acts + 1

    elif action == ACTION_FIX_GATE_ONLY:
        # Flag-based prefer_thin; waive checkbox complete-gate for re-complete paths
        state = _rearm_prefer_thin(state, reason=ACTION_FIX_GATE_ONLY)
        if state.get("complete_blocked_reason"):
            state["complete_blocked_waived"] = True
            state["complete_blocked_waived_reason"] = "FIX_GATE_ONLY consumer"

    elif action == ACTION_THIN_FIELD_RETRY:
        state = _rearm_prefer_thin(state, reason=ACTION_THIN_FIELD_RETRY)

    elif action == ACTION_DEBUG_TARGETED:
        # v0: pure thin re-arm + optional hint; no be2_path / no agent spawn
        state = _rearm_prefer_thin(
            state,
            reason=ACTION_DEBUG_TARGETED,
            debug_hint=prompt or primary,
        )

    else:
        # Defensive — should not reach
        state = _yield_to_budget(
            state,
            action=action,
            primary=primary,
            fingerprint=fp,
            reason_detail="unhandled_action",
        )
        return state, "yielded"

    # Mark act for anti double-act / episode budget
    if fp:
        state["recovery_acted_fingerprint"] = fp
    state["recovery_act_count"] = act_count + 1
    state["last_recovery_consumed_at"] = _utc_now()
    state["last_recovery_consumed_action"] = action
    return state, "acted"


def _record_consume(
    project_dir: Path,
    state: dict[str, Any],
    tag: str,
) -> None:
    slug = str(state.get("slug") or state.get("_slug") or project_dir.name)
    action = str(
        state.get("last_recovery_consumed_action")
        or state.get("recovery_yield_action")
        or state.get("last_recovery_action")
        or ""
    )
    primary = str(state.get("last_recovery_class") or "")
    fp = str(
        state.get("recovery_acted_fingerprint")
        or state.get("recovery_episode_fingerprint")
        or ""
    )
    _append_consumer_trace(
        project_dir,
        slug=slug,
        tag=tag,
        action=action,
        primary=primary,
        fingerprint=fp,
        state=state,
    )


def tick_troubleshoot_recovery(
    pipeline_dir: Path | None = None,
    bus: Any = None,
    limit: int = 1,
    *,
    acted_out: list[str] | None = None,
) -> int:
    """Serial consumer tick: honor cheap recovery actions or escalate.

    At most *limit* projects per tick (default 1). Returns number processed
    (acted or yielded).

    If *acted_out* is provided, appends slugs that were cheap-acted (prefer_thin
    re-armed) so the thin-field tick can prioritize them same-cycle.
    """
    if not troubleshoot_consumer_enabled():
        return 0

    root = Path(pipeline_dir) if pipeline_dir else get_pipeline_dir()
    projects = root / "projects"
    if not projects.is_dir():
        return 0

    n = 0
    lim = max(1, int(limit) if limit else 1)
    for d in sorted(projects.iterdir()):
        if n >= lim:
            break
        if not d.is_dir():
            continue
        sf = d / "state" / "current_idea.json"
        if not sf.is_file():
            continue
        st = _load_state(sf)
        if st is None:
            continue
        if not _is_eligible(st, d):
            continue

        slug = d.name
        try:
            new_st, tag = process_troubleshoot_project(d, st, bus=bus)
            _write_state(sf, new_st)
            # Durable consume trace (survives runner kill / reboot)
            try:
                _record_consume(d, new_st, tag)
            except Exception:
                pass
            action = (
                new_st.get("last_recovery_consumed_action")
                or new_st.get("recovery_yield_action")
                or new_st.get("last_recovery_action")
                or "?"
            )
            if tag == "acted":
                if acted_out is not None:
                    acted_out.append(slug)
                print(
                    f"  [troubleshoot-consumer] '{slug}' acted "
                    f"action={action} → status={new_st.get('status')} "
                    f"prefer_thin={bool(new_st.get('prefer_thin_field'))} "
                    f"acts={new_st.get('recovery_act_count')}",
                    flush=True,
                )
            else:
                print(
                    f"  [troubleshoot-consumer] '{slug}' yielded → budget_exceeded "
                    f"({(new_st.get('budget_note') or '')[:120]})",
                    flush=True,
                )
            n += 1
        except Exception as exc:
            print(
                f"  [troubleshoot-consumer] '{slug}' error: {exc}",
                flush=True,
            )
            continue
    return n
