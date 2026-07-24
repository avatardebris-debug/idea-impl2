"""
Classic budget_exceeded → sticky grok_build conversion.

Hybrid policy:
  - Always *convert* eligible classic/missing-engine yields to engine=grok_build
    when CLASSIC_TO_GROK_ON_YIELD is on (default True, strict eligibility).
  - *Run* only when CLASSIC_TO_GROK_AUTO_RUN=1 and serial ladder focus is free
    (default park: sticky engine + stay budget_exceeded until unpark/run_now/drain).

Park semantics (coherent, zip-safe):
  - engine=grok_build
  - status remains budget_exceeded
  - classic_to_grok_parked=True
  - pre_budget_status preserved for later resume
  - prefer_thin deferred via classic_to_grok_prefer_thin (not prefer_thin_field)
  - grok hook / thin-field tick skip parked projects

Unpark / run_now:
  - resume pre_budget_status, arm prefer_thin if deferred/near-done
  - clear classic_to_grok_parked
  - optional ladder focus

Manual CLI: scripts/classic_be_to_grok.py (thin wrapper over this library).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.env_flags import env_bool

JUNK_PREFIXES = ("test_", "smoke_", "fake_", "tmp_")
JUNK_SLUGS = frozenset({"test_idea", "test_exec", "proj", "plan_first"})

# Engines we will convert from (missing/empty treated as classic).
_CONVERTIBLE_ENGINES = frozenset({"", "classic"})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def classic_to_grok_on_yield_enabled() -> bool:
    """Auto-convert eligible classic BE on budget yield (default on)."""
    return env_bool("CLASSIC_TO_GROK_ON_YIELD", default=True)


def classic_to_grok_auto_run_enabled() -> bool:
    """When True, set ladder focus / resume so serial grok can pick up (default park)."""
    return env_bool("CLASSIC_TO_GROK_AUTO_RUN", default=False)


def classic_to_grok_near_done_only() -> bool:
    """Only convert near-done projects on auto path (default True)."""
    return env_bool("CLASSIC_TO_GROK_NEAR_DONE_ONLY", default=True)


def classic_to_grok_drain_enabled() -> bool:
    """When True, ladder tick may unpark parked classic→grok (default off).

    Overnight -NoFreshListOnly sets CLASSIC_TO_GROK_DRAIN=1.
    """
    return env_bool("CLASSIC_TO_GROK_DRAIN", default=False)


def is_junk_slug(slug: str) -> bool:
    """True for test/smoke/fake/tmp junk slugs."""
    if not slug:
        return True
    if slug in JUNK_SLUGS:
        return True
    return any(slug.startswith(p) for p in JUNK_PREFIXES)


def note_class(state: dict[str, Any]) -> str:
    """Classify budget_note for eligibility / inventory."""
    note = str(state.get("budget_note") or "").lower()
    if "total retries across all phases" in note:
        return "lifetime"
    if "active-min" in note:
        return "active_yield"
    if "force-completed after" in note:
        return "wall_or_force_min"
    if note.strip():
        return "other"
    return "empty"


def _strikes(state: dict[str, Any]) -> int:
    try:
        return max(0, int(state.get("budget_strikes") or 0))
    except (TypeError, ValueError):
        return 0


def ladder_stage(state: dict[str, Any]) -> str:
    if (state.get("status") or "") != "budget_exceeded":
        return "-"
    if state.get("budget_strikes") is None or _strikes(state) < 1:
        return "BE0"
    s = _strikes(state)
    if s == 1:
        return "BE1"
    if s == 2:
        return "BE2"
    return "BE3"


def _engine_key(state: dict[str, Any]) -> str:
    return str(state.get("engine") or "").strip().lower()


def is_already_grok(state: dict[str, Any]) -> bool:
    return _engine_key(state) == "grok_build"


def is_convertible_engine(state: dict[str, Any]) -> bool:
    """Classic or missing engine (not hermes / not already grok_build)."""
    return _engine_key(state) in _CONVERTIBLE_ENGINES


def is_classic_to_grok_parked(state: dict[str, Any]) -> bool:
    """True when sticky grok convert is parked (not runnable until unpark)."""
    if not state.get("classic_to_grok_parked"):
        return False
    if _engine_key(state) != "grok_build":
        return False
    return True


def _resume_pre(state: dict[str, Any]) -> str:
    pre = state.get("pre_budget_status") or ""
    phase = state.get("phase") or 1
    if not (isinstance(pre, str) and pre.startswith("phase_")):
        pre = f"phase_{phase}_executing"
    return pre


def _is_near_done_local(state: dict[str, Any]) -> bool:
    try:
        from pipeline.budget_ladder import is_near_done

        return bool(is_near_done(state))
    except Exception:
        try:
            ph = int(state.get("phase") or 0)
            tot = int(state.get("total_phases") or 1)
            if ph >= tot:
                return True
            pre = str(state.get("pre_budget_status") or "")
            # late penultimate/final review-validate
            if ph >= max(1, tot - 1) and any(
                x in pre for x in ("validating", "reviewing", "reviewed")
            ):
                return True
        except (TypeError, ValueError):
            return False
        return False


def is_eligible_for_classic_to_grok(
    state: dict[str, Any],
    slug: str,
    *,
    force: bool = False,
    force_lifetime: bool = False,
    near_done_only: bool | None = None,
) -> tuple[bool, str]:
    """Return (ok, reason). reason is short machine-ish string.

    Eligibility (auto path uses force=False, force_lifetime=False):
      - status budget_exceeded (or just-yielded before status rewrite)
      - engine classic or missing
      - not junk unless force
      - not lifetime-retry fossil unless force_lifetime
      - near_done when near_done_only
      - not already converted this yield episode (classic_to_grok_consumed)
        unless already parked (idempotent park is handled by is_already_grok)
    """
    if not slug:
        return False, "missing_slug"
    if is_already_grok(state):
        # Parked sticky grok is "already converted" — unpark via run_now, not re-convert
        if is_classic_to_grok_parked(state):
            return False, "already_parked_grok"
        return False, "already_grok_build"
    if not is_convertible_engine(state):
        return False, f"engine_not_convertible:{_engine_key(state) or 'empty'}"

    status = str(state.get("status") or "")
    if status != "budget_exceeded":
        return False, f"status_not_be:{status or 'empty'}"

    if is_junk_slug(slug) and not force:
        return False, "junk_slug"

    nc = note_class(state)
    if nc == "lifetime" and not force_lifetime:
        return False, "lifetime_fossil"

    # Also refuse via budget_ladder helper when present
    try:
        from pipeline.budget_ladder import is_lifetime_retry_fossil

        if is_lifetime_retry_fossil(state) and not force_lifetime:
            return False, "lifetime_fossil"
    except Exception:
        pass

    if state.get("classic_to_grok_consumed") and not force:
        return False, "already_consumed_episode"

    if near_done_only is None:
        near_done_only = False
    if near_done_only:
        if not _is_near_done_local(state):
            return False, "not_near_done"

    return True, "ok"


def convert_state(
    st: dict[str, Any],
    *,
    clear_ladder_flags: bool = True,
    keep_strikes: bool = False,
    mode: str = "park",
) -> dict[str, Any]:
    """Return a mutated copy of state for sticky grok_build convert.

    Park (default):
      engine=grok_build, status stays budget_exceeded, classic_to_grok_parked=True,
      prefer_thin deferred (classic_to_grok_prefer_thin), not immediately runnable.

    run_now:
      resume pre_budget_status, arm prefer_thin if near-done, clear parked.
    """
    out = dict(st)
    mode = mode if mode in ("park", "run_now") else "park"
    pre = _resume_pre(out)
    out["pre_budget_status"] = pre

    out["engine"] = "grok_build"
    out["last_decision"] = "CLASSIC_TO_GROK"
    out["classic_to_grok_at"] = _now()
    out["classic_to_grok_mode"] = mode
    out["classic_to_grok_consumed"] = True
    out["classic_to_grok_from"] = {
        "status": st.get("status") or "budget_exceeded",
        "pre_budget_status": st.get("pre_budget_status"),
        "budget_strikes": st.get("budget_strikes"),
        "note_class": note_class(st),
        "engine": st.get("engine"),
    }

    near = _is_near_done_local(out)

    if not keep_strikes:
        # Fresh Grok attempt: don't inherit BE1-done lockout mid-ladder
        out["budget_strikes"] = 0
        out.pop("be1_consumed", None)
        out.pop("be2_consumed", None)
        out.pop("be3_consumed", None)
        out.pop("be2_path", None)
        out.pop("be2_pending", None)
        out.pop("prefer_thin_field", None)
        out.pop("prefer_thin_field_shipped", None)
        # lifetime_retry_capped cleared only when caller soft-resets phase_retries
        # (see apply / maybe_auto). Default: keep cap until retries reset.
        out.pop("ladder_focus", None)

    if clear_ladder_flags and keep_strikes:
        out.pop("be1_consumed", None)

    if mode == "park":
        # Sticky convert only — not runnable by grok hook or thin-field tick
        out["status"] = "budget_exceeded"
        out["classic_to_grok_parked"] = True
        out["budget_yielded"] = True
        if not out.get("budget_yielded_at"):
            out["budget_yielded_at"] = _now()
        # Defer prefer_thin until unpark/run_now
        out.pop("prefer_thin_field", None)
        if near:
            out["classic_to_grok_prefer_thin"] = True
        # Note stays as yield note if present; annotate for inventory
        note = str(out.get("budget_note") or "").strip()
        if note and "classic_to_grok parked" not in note.lower():
            out["budget_note"] = (note + " | classic_to_grok parked")[:500]
        elif not note:
            out["budget_note"] = "classic_to_grok parked (sticky engine=grok_build)"
    else:
        # run_now: resume immediately
        out["status"] = pre
        out["classic_to_grok_parked"] = False
        out.pop("classic_to_grok_parked", None)
        out["session_started_at"] = _now()
        out["last_active_work_at"] = _now()
        out["budget_yielded"] = False
        out.pop("budget_note", None)
        out.pop("classic_to_grok_prefer_thin", None)
        if near:
            out["prefer_thin_field"] = True

    return out


def unpark_classic_to_grok(state: dict[str, Any]) -> dict[str, Any]:
    """Resume a parked sticky-grok project for serial run / thin ship."""
    out = dict(state)
    pre = _resume_pre(out)
    out["pre_budget_status"] = pre
    out["engine"] = "grok_build"
    out["status"] = pre
    out["classic_to_grok_parked"] = False
    out.pop("classic_to_grok_parked", None)
    out["classic_to_grok_mode"] = "run_now"
    out["session_started_at"] = _now()
    out["last_active_work_at"] = _now()
    out["budget_yielded"] = False
    out.pop("budget_note", None)
    out["last_decision"] = "CLASSIC_TO_GROK_UNPARK"
    near = _is_near_done_local(out) or bool(out.get("classic_to_grok_prefer_thin"))
    out.pop("classic_to_grok_prefer_thin", None)
    if near:
        out["prefer_thin_field"] = True
    return out


def _resolve_project(
    project_dir_or_slug: str | Path,
    *,
    projects_root: Path | None = None,
) -> tuple[str, Path, Path]:
    """Return (slug, project_dir, state_file)."""
    p = Path(project_dir_or_slug)
    if p.is_dir() and (p / "state" / "current_idea.json").is_file():
        project_dir = p
        slug = project_dir.name
    elif p.is_file() and p.name == "current_idea.json":
        project_dir = p.parent.parent
        slug = project_dir.name
    else:
        slug = str(project_dir_or_slug).strip().replace("\\", "/").split("/")[-1]
        if projects_root is None:
            from pipeline.paths import projects_dir

            projects_root = projects_dir()
        project_dir = Path(projects_root) / slug
    sf = project_dir / "state" / "current_idea.json"
    return slug, project_dir, sf


def _soft_reset_phase_retries(project_dir: Path) -> bool:
    """Soft-reset phase_retries.json so lifetime health does not re-yield immediately."""
    pr = project_dir / "state" / "phase_retries.json"
    if not pr.is_file():
        return False
    try:
        bak = pr.with_suffix(
            pr.suffix + f".bak_classic_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        bak.write_text(pr.read_text(encoding="utf-8-sig"), encoding="utf-8")
        pr.write_text("{}\n", encoding="utf-8")
        return True
    except Exception:
        return False


def _project_dir_for_slug(
    slug: str, pipeline_dir: Path | None = None
) -> Path | None:
    if not slug:
        return None
    try:
        if pipeline_dir is not None:
            return Path(pipeline_dir) / "projects" / slug
        from pipeline.paths import project_dir

        return project_dir(slug)
    except Exception:
        return None


def _serial_focus_free(pipeline_dir: Path | None = None) -> bool:
    try:
        from pipeline.budget_ladder import (
            focus_is_expired,
            ladder_serial_enabled,
            read_ladder_focus,
            clear_ladder_focus,
        )

        if not ladder_serial_enabled():
            return True
        focus = read_ladder_focus(pipeline_dir)
        if not focus or not focus.get("slug"):
            return True
        if focus_is_expired(focus):
            clear_ladder_focus(pipeline_dir, slug=str(focus.get("slug")))
            return True
        return False
    except Exception:
        return True


def _bak_state_file(sf: Path) -> Path | None:
    try:
        bak = sf.with_suffix(
            sf.suffix + f".bak_classic_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        bak.write_text(sf.read_text(encoding="utf-8-sig"), encoding="utf-8")
        return bak
    except Exception:
        return None


def apply_classic_to_grok(
    project_dir_or_slug: str | Path,
    *,
    dry_run: bool = False,
    force: bool = False,
    force_lifetime: bool = False,
    keep_strikes: bool = False,
    mode: str = "park",
    near_done_only: bool | None = None,
    projects_root: Path | None = None,
    pipeline_dir: Path | None = None,
    soft_reset_retries: bool = True,
) -> dict[str, Any]:
    """Convert one project classic BE → sticky grok_build (park or run_now).

    If already parked grok and mode=run_now, unparks instead of re-converting.
    """
    mode = mode if mode in ("park", "run_now") else "park"
    slug, project_dir, sf = _resolve_project(
        project_dir_or_slug, projects_root=projects_root
    )
    result: dict[str, Any] = {
        "ok": False,
        "reason": "",
        "slug": slug,
        "dry_run": dry_run,
        "mode": mode,
        "wrote": False,
        "bak": None,
        "state": None,
        "project_dir": str(project_dir),
        "from_engine": None,
        "from_status": None,
    }

    if not sf.is_file():
        result["reason"] = f"missing_state:{sf}"
        return result

    try:
        st = json.loads(sf.read_text(encoding="utf-8-sig"))
    except Exception as e:
        result["reason"] = f"unreadable_state:{e}"
        return result

    result["from_engine"] = st.get("engine")
    result["from_status"] = st.get("status")

    # Already parked sticky grok → unpark when run_now
    if is_classic_to_grok_parked(st):
        if mode != "run_now":
            result["ok"] = True
            result["reason"] = "already_parked_grok"
            result["state"] = st
            result["idempotent"] = True
            return result
        applied_mode = "run_now"
        if not _serial_focus_free(pipeline_dir):
            result["focus_blocked"] = True
            result["ok"] = True
            result["reason"] = "parked_focus_blocked"
            result["state"] = st
            result["mode"] = "park"
            return result
        new_st = unpark_classic_to_grok(st)
        result["mode"] = applied_mode
        result["state"] = new_st
        result["ok"] = True
        result["reason"] = "unparked"
        result["to_status"] = new_st.get("status")
        result["prefer_thin_field"] = new_st.get("prefer_thin_field")
        if dry_run:
            return result
        bak = _bak_state_file(sf)
        try:
            if bak:
                result["bak"] = str(bak)
            sf.write_text(json.dumps(new_st, indent=2) + "\n", encoding="utf-8")
            result["wrote"] = True
        except Exception as e:
            result["ok"] = False
            result["reason"] = f"write_failed:{e}"
            return result
        if soft_reset_retries:
            result["phase_retries_reset"] = _soft_reset_phase_retries(project_dir)
            if result.get("phase_retries_reset"):
                new_st.pop("lifetime_retry_capped", None)
                sf.write_text(json.dumps(new_st, indent=2) + "\n", encoding="utf-8")
                result["state"] = new_st
        try:
            from pipeline.budget_ladder import write_ladder_focus

            write_ladder_focus(
                slug, stage="classic_to_grok_unpark", pipeline_dir=pipeline_dir
            )
            new_st["ladder_focus"] = True
            sf.write_text(json.dumps(new_st, indent=2) + "\n", encoding="utf-8")
            result["state"] = new_st
            result["ladder_focus"] = True
        except Exception:
            result["ladder_focus"] = False
        try:
            from pipeline.pipeline_activity import log_activity

            log_activity(
                "classic_to_grok",
                slug=slug,
                mode="run_now",
                unpark=True,
                from_status=result.get("from_status"),
                to_status=result.get("to_status"),
            )
        except Exception:
            pass
        return result

    if is_already_grok(st):
        result["ok"] = True
        result["reason"] = "already_grok_build"
        result["state"] = st
        result["idempotent"] = True
        return result

    ok, reason = is_eligible_for_classic_to_grok(
        st,
        slug,
        force=force,
        force_lifetime=force_lifetime,
        near_done_only=near_done_only,
    )
    if not ok:
        result["reason"] = reason
        result["state"] = st
        return result

    # run_now requires free serial focus; otherwise park
    applied_mode = mode
    if mode == "run_now" and not _serial_focus_free(pipeline_dir):
        applied_mode = "park"
        result["focus_blocked"] = True

    new_st = convert_state(
        st, keep_strikes=keep_strikes, mode=applied_mode
    )
    result["mode"] = applied_mode
    result["state"] = new_st
    result["ok"] = True
    result["reason"] = "converted"
    result["to_status"] = new_st.get("status")
    result["prefer_thin_field"] = new_st.get("prefer_thin_field")
    result["parked"] = bool(new_st.get("classic_to_grok_parked"))

    if dry_run:
        return result

    bak = _bak_state_file(sf)
    try:
        if bak:
            result["bak"] = str(bak)
        sf.write_text(json.dumps(new_st, indent=2) + "\n", encoding="utf-8")
        result["wrote"] = True
    except Exception as e:
        result["ok"] = False
        result["reason"] = f"write_failed:{e}"
        return result

    if soft_reset_retries:
        reset = _soft_reset_phase_retries(project_dir)
        result["phase_retries_reset"] = reset
        if reset:
            new_st.pop("lifetime_retry_capped", None)
            sf.write_text(json.dumps(new_st, indent=2) + "\n", encoding="utf-8")
            result["state"] = new_st
        # If no reset, leave lifetime_retry_capped as-is (convert_state no longer pops it)

    if applied_mode == "run_now":
        try:
            from pipeline.budget_ladder import write_ladder_focus

            write_ladder_focus(
                slug, stage="classic_to_grok", pipeline_dir=pipeline_dir
            )
            new_st["ladder_focus"] = True
            sf.write_text(json.dumps(new_st, indent=2) + "\n", encoding="utf-8")
            result["state"] = new_st
            result["ladder_focus"] = True
        except Exception:
            result["ladder_focus"] = False

    try:
        from pipeline.pipeline_activity import log_activity

        log_activity(
            "classic_to_grok",
            slug=slug,
            mode=applied_mode,
            from_status=result.get("from_status"),
            to_status=result.get("to_status"),
            prefer_thin_field=bool(new_st.get("prefer_thin_field")),
            parked=bool(new_st.get("classic_to_grok_parked")),
            dry_run=False,
        )
    except Exception:
        pass

    return result


def maybe_classic_to_grok_after_yield(
    state: dict[str, Any],
    *,
    slug: str,
    pipeline_dir: Path | None = None,
    project_dir: Path | None = None,
    write_bak: bool = True,
) -> dict[str, Any]:
    """Auto-convert after apply_budget_yield.

    Park by default (status stays budget_exceeded). Soft-resets phase_retries
    when project_dir/slug resolves. Optional bak of on-disk state before caller
    overwrites. Once per yield episode via classic_to_grok_consumed.
    """
    if not classic_to_grok_on_yield_enabled():
        return state
    if not slug:
        return state
    if state.get("classic_to_grok_consumed"):
        return state

    near_only = classic_to_grok_near_done_only()
    ok, _reason = is_eligible_for_classic_to_grok(
        state,
        slug,
        force=False,
        force_lifetime=False,
        near_done_only=near_only,
    )
    if not ok:
        return state

    mode = "run_now" if classic_to_grok_auto_run_enabled() else "park"
    focus_blocked = False
    if mode == "run_now" and not _serial_focus_free(pipeline_dir):
        mode = "park"
        focus_blocked = True

    pd = project_dir or _project_dir_for_slug(slug, pipeline_dir)

    # Bak on-disk pre-convert state when available (auto path)
    bak_path = None
    if write_bak and pd is not None:
        sf = pd / "state" / "current_idea.json"
        if sf.is_file():
            bak_path = _bak_state_file(sf)

    new_st = convert_state(state, mode=mode)

    # Soft-reset phase_retries; only clear lifetime_retry_capped if reset worked
    if pd is not None:
        reset_ok = _soft_reset_phase_retries(pd)
        if reset_ok:
            new_st.pop("lifetime_retry_capped", None)
        elif state.get("lifetime_retry_capped"):
            # Keep durable cap when retries could not be cleared
            new_st["lifetime_retry_capped"] = True

    if mode == "run_now":
        try:
            from pipeline.budget_ladder import write_ladder_focus

            write_ladder_focus(
                slug, stage="classic_to_grok", pipeline_dir=pipeline_dir
            )
            new_st["ladder_focus"] = True
        except Exception:
            pass

    try:
        from pipeline.pipeline_activity import log_activity

        log_activity(
            "classic_to_grok",
            slug=slug,
            mode=mode,
            auto_yield=True,
            focus_blocked=focus_blocked,
            from_status="budget_exceeded",
            to_status=new_st.get("status"),
            prefer_thin_field=bool(new_st.get("prefer_thin_field")),
            parked=bool(new_st.get("classic_to_grok_parked")),
            bak=str(bak_path) if bak_path else None,
        )
    except Exception:
        pass

    return new_st


def try_unpark_for_drain(
    slug: str,
    state: dict[str, Any],
    state_file: Path,
    *,
    pipeline_dir: Path | None = None,
) -> dict[str, Any]:
    """Unpark one parked classic→grok when drain is enabled and focus free.

    Called from budget ladder tick. No-op if not parked / drain off / focus busy.
    """
    if not is_classic_to_grok_parked(state):
        return state
    if not classic_to_grok_drain_enabled() and not classic_to_grok_auto_run_enabled():
        return state
    if not _serial_focus_free(pipeline_dir):
        return state
    new_st = unpark_classic_to_grok(state)
    # Soft-reset retries on unpark so lifetime health stays calm
    pd = state_file.parent.parent if state_file else _project_dir_for_slug(slug, pipeline_dir)
    if pd is not None:
        if _soft_reset_phase_retries(pd):
            new_st.pop("lifetime_retry_capped", None)
    try:
        from pipeline.budget_ladder import write_ladder_focus

        write_ladder_focus(
            slug, stage="classic_to_grok_drain", pipeline_dir=pipeline_dir
        )
        new_st["ladder_focus"] = True
    except Exception:
        pass
    try:
        state_file.write_text(json.dumps(new_st, indent=2) + "\n", encoding="utf-8")
    except Exception:
        return state
    try:
        from pipeline.pipeline_activity import log_activity

        log_activity(
            "classic_to_grok",
            slug=slug,
            mode="run_now",
            drain_unpark=True,
            to_status=new_st.get("status"),
        )
    except Exception:
        pass
    print(
        f"  [classic_to_grok] drain unpark '{slug}' → {new_st.get('status')}",
        flush=True,
    )
    return new_st


def load_be_projects(root: Path) -> list[tuple[str, Path, dict[str, Any]]]:
    """Inventory budget_exceeded projects under projects root."""
    out: list[tuple[str, Path, dict[str, Any]]] = []
    if not root.is_dir():
        return out
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        sf = d / "state" / "current_idea.json"
        if not sf.is_file():
            continue
        try:
            st = json.loads(sf.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if (st.get("status") or "") != "budget_exceeded":
            continue
        out.append((d.name, sf, st))
    return out
