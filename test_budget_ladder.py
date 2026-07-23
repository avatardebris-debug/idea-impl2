"""Unit tests for budget_ladder + active clock."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from pipeline.budget_ladder import (
    apply_budget_yield,
    auto_retry_clean,
    classify_blocker,
    clear_ladder_focus,
    effective_elapsed_minutes,
    focus_is_expired,
    manager_decide,
    apply_manager_decision,
    process_budget_exceeded_project,
    maybe_refresh_stale_session,
    is_ladder_eligible,
    read_ladder_focus,
    seed_serial_blocked,
    tick_process_budget_yields,
    try_seed_process_budget_exceeded,
    write_ladder_focus,
    _project_still_ladder_inflight,
)


def test_effective_elapsed_pauses_on_idle_gap(monkeypatch):
    monkeypatch.setenv("BUDGET_ACTIVE_CLOCK", "1")
    monkeypatch.setenv("BUDGET_IDLE_GAP_MINUTES", "45")
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    last = start + timedelta(minutes=30)
    st = {
        "session_started_at": start.isoformat(),
        "last_active_work_at": last.isoformat(),
    }
    # "now" is years later — should only charge ~30m
    # effective_elapsed uses datetime.now — monkeypatch by freezing last far past
    eff = effective_elapsed_minutes(st)
    assert eff < 120, eff


def test_apply_budget_yield_increments_strikes():
    st = {"status": "phase_1_executing", "phase": 1, "total_phases": 3}
    st = apply_budget_yield(st, elapsed_min=100, phase_budget=90, total_phases=3)
    assert st["status"] == "budget_exceeded"
    assert st["budget_strikes"] == 1
    assert st["budget_yielded"] is True
    st = apply_budget_yield(st, elapsed_min=100, phase_budget=90, total_phases=3)
    assert st["budget_strikes"] == 2


def test_be1_auto_retry(tmp_path, monkeypatch):
    monkeypatch.setenv("BUDGET_BE1_AUTO_RETRY", "1")
    st = {
        "status": "budget_exceeded",
        "budget_strikes": 1,
        "pre_budget_status": "phase_2_validating",
        "phase": 2,
        "total_phases": 3,
    }
    sf = tmp_path / "current_idea.json"
    sf.write_text(json.dumps(st), encoding="utf-8")
    out = process_budget_exceeded_project("p", st, sf)
    assert out["status"] == "phase_2_validating"
    assert out.get("be1_consumed") is True
    assert out.get("last_decision") == "AUTO_RETRY_CLEAN"


def test_be2_thin_field_when_near_done(tmp_path, monkeypatch):
    monkeypatch.setenv("BUDGET_BE1_AUTO_RETRY", "1")
    monkeypatch.setenv("BUDGET_BE2", "1")
    st = {
        "status": "budget_exceeded",
        "budget_strikes": 2,
        "be1_consumed": True,
        "pre_budget_status": "phase_3_validating",
        "phase": 3,
        "total_phases": 3,
    }
    sf = tmp_path / "current_idea.json"
    sf.write_text(json.dumps(st), encoding="utf-8")
    out = process_budget_exceeded_project("p", st, sf)
    assert out["status"] == "phase_3_validating"
    assert out.get("be2_path") == "thin_field"
    assert out.get("prefer_thin_field") is True


def test_timer_glitch_manager_auto_retry():
    st = {
        "status": "budget_exceeded",
        "budget_strikes": 3,
        "phase": 3,
        "total_phases": 3,
        "pre_budget_status": "phase_3_validating",
        "budget_note": "Force-completed after 59317 min (budget: 135 min)",
        "session_started_at": "2020-01-01T00:00:00+00:00",
    }
    rep = classify_blocker(
        st, slug="sim", dependents_open=[{"title": "disc", "requires": ["sim"]}]
    )
    assert rep["blocker_class"] == "timer_glitch"
    assert rep["primary_recommendation"] == "AUTO_RETRY_CLEAN"
    dec = manager_decide(rep, st)
    assert dec == "AUTO_RETRY_CLEAN"
    out = apply_manager_decision(st, dec, rep)
    assert out["status"] == "phase_3_validating"


def test_maybe_refresh_stale_session(monkeypatch):
    monkeypatch.setenv("BUDGET_ACTIVE_CLOCK", "1")
    monkeypatch.setenv("BUDGET_IDLE_GAP_MINUTES", "45")
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    st = {
        "session_started_at": start.isoformat(),
        "last_active_work_at": start.isoformat(),
    }
    st2, refreshed = maybe_refresh_stale_session(st)
    assert refreshed is True
    assert st2["session_started_at"] != start.isoformat()


def test_fossil_strike0_not_eligible():
    st = {
        "status": "budget_exceeded",
        "budget_note": "Force-completed: exceeded 80 total retries (actual: 1000)",
    }
    assert not is_ladder_eligible(st)
    # process leaves parked
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as td:
        sf = Path(td) / "current_idea.json"
        sf.write_text(json.dumps(st), encoding="utf-8")
        out = process_budget_exceeded_project("fossil", dict(st), sf)
        assert out["status"] == "budget_exceeded"
        assert not out.get("be1_consumed")


def test_tick_processes_only_one(tmp_path, monkeypatch):
    monkeypatch.setenv("BUDGET_BE1_AUTO_RETRY", "1")
    monkeypatch.setenv("BUDGET_LADDER_SERIAL", "1")
    projects = tmp_path / "projects"
    for i, name in enumerate(("aaa_be", "bbb_be", "ccc_be")):
        d = projects / name / "state"
        d.mkdir(parents=True)
        st = {
            "status": "budget_exceeded",
            "budget_strikes": 1,
            "pre_budget_status": "phase_1_executing",
            "phase": 1,
            "total_phases": 3,
            "budget_yielded": True,
        }
        (d / "current_idea.json").write_text(json.dumps(st), encoding="utf-8")
    n = tick_process_budget_yields(tmp_path)
    assert n == 1
    resumed = 0
    still_be = 0
    for name in ("aaa_be", "bbb_be", "ccc_be"):
        st = json.loads(
            (projects / name / "state" / "current_idea.json").read_text(encoding="utf-8")
        )
        if st.get("status") == "budget_exceeded":
            still_be += 1
        else:
            resumed += 1
    assert resumed == 1
    assert still_be == 2


def test_be2_without_bus_does_not_consume(tmp_path, monkeypatch):
    """BE2 debug path with bus=None must not permanently consume (tick retries later)."""
    monkeypatch.setenv("BUDGET_BE2", "1")
    st = {
        "status": "budget_exceeded",
        "budget_strikes": 2,
        "be1_consumed": True,
        "pre_budget_status": "phase_1_executing",
        "phase": 1,
        "total_phases": 3,
    }
    sf = tmp_path / "current_idea.json"
    sf.write_text(json.dumps(st), encoding="utf-8")
    out = process_budget_exceeded_project("p", st, sf, bus=None)
    assert out["status"] == "budget_exceeded"
    assert not out.get("be2_consumed")
    # Later tick with bus can still advance
    bus = MagicMock()
    out2 = process_budget_exceeded_project("p", dict(out), sf, bus=bus)
    assert out2.get("be2_consumed") is True
    assert out2.get("be2_path") == "debug"
    assert out2["status"] == "phase_1_executing"
    assert out2.get("be2_debug_enqueued") is True
    bus.send.assert_called_once()


def test_be2_with_mock_bus_enqueues_once(tmp_path, monkeypatch):
    monkeypatch.setenv("BUDGET_BE2", "1")
    st = {
        "status": "budget_exceeded",
        "budget_strikes": 2,
        "be1_consumed": True,
        "pre_budget_status": "phase_1_executing",
        "phase": 1,
        "total_phases": 3,
    }
    sf = tmp_path / "current_idea.json"
    sf.write_text(json.dumps(st), encoding="utf-8")
    bus = MagicMock()
    out = process_budget_exceeded_project("p", st, sf, bus=bus)
    assert out.get("be2_path") == "debug"
    assert out.get("be2_consumed") is True
    assert out.get("be2_debug_enqueued") is True
    assert out.get("be2_debug_attempted") is True
    assert out.get("be2_pending") is False
    assert out["status"] == "phase_1_executing"
    bus.send.assert_called_once()
    # Second call must not re-enqueue
    bus2 = MagicMock()
    out2 = process_budget_exceeded_project("p", dict(out), sf, bus=bus2)
    # Already consumed and not budget_exceeded
    assert out2.get("status") == "phase_1_executing"
    bus2.send.assert_not_called()


def test_lifetime_retry_capped_no_cascade(tmp_path, monkeypatch):
    """After lifetime yield + BE1, flag blocks re-yield strike cascade."""
    monkeypatch.setenv("BUDGET_BE1_AUTO_RETRY", "1")
    st = {
        "status": "phase_1_executing",
        "phase": 1,
        "total_phases": 3,
        "budget_strikes": 0,
    }
    # Simulate health lifetime yield
    st = apply_budget_yield(st, elapsed_min=1000, phase_budget=80, total_phases=3)
    st["budget_note"] = (
        "Force-completed: exceeded 80 total retries across all phases "
        f"(actual: 1000); strike={st.get('budget_strikes')}"
    )
    st["lifetime_retry_capped"] = True
    assert st["budget_strikes"] == 1
    assert st["lifetime_retry_capped"] is True

    sf = tmp_path / "current_idea.json"
    sf.write_text(json.dumps(st), encoding="utf-8")
    out = process_budget_exceeded_project("life", st, sf)
    assert out.get("be1_consumed") is True
    assert out["status"] == "phase_1_executing"
    # Flag survives BE1 (auto_retry_clean does not clear it)
    assert out.get("lifetime_retry_capped") is True
    # Simulated second lifetime check: health skips when flag set
    # (mirrors run_loop_health condition)
    retries = 1000
    max_retries = 80
    would_re_yield = (
        retries >= max_retries
        and out.get("status") not in ("complete", "budget_exceeded", "", "dep_waiting")
        and not out.get("lifetime_retry_capped")
    )
    assert would_re_yield is False
    # Strikes must not advance without a new real yield
    assert out.get("budget_strikes") == 1


def test_be3_bypass_clears_focus(tmp_path, monkeypatch):
    """BE3 BYPASS_RETURN parks project and clears serial focus so others can run."""
    monkeypatch.setenv("BUDGET_BE3_BLOCKER", "1")
    monkeypatch.setenv("BUDGET_LADDER_SERIAL", "1")
    monkeypatch.setenv("BUDGET_BE1_AUTO_RETRY", "1")
    # Force parked decision (default manager may pick DEBUG_AGAIN for unknown)
    monkeypatch.setattr(
        "pipeline.budget_ladder.manager_decide",
        lambda report, state: "BYPASS_RETURN",
    )
    projects = tmp_path / "projects"
    d_a = projects / "parked_be" / "state"
    d_a.mkdir(parents=True)
    st_a = {
        "status": "budget_exceeded",
        "budget_strikes": 3,
        "be1_consumed": True,
        "be2_consumed": True,
        "pre_budget_status": "phase_1_executing",
        "phase": 1,
        "total_phases": 3,
        "budget_yielded": True,
    }
    (d_a / "current_idea.json").write_text(json.dumps(st_a), encoding="utf-8")
    # Second eligible candidate
    d_b = projects / "next_be" / "state"
    d_b.mkdir(parents=True)
    st_b = {
        "status": "budget_exceeded",
        "budget_strikes": 1,
        "pre_budget_status": "phase_1_executing",
        "phase": 1,
        "total_phases": 3,
        "budget_yielded": True,
    }
    (d_b / "current_idea.json").write_text(json.dumps(st_b), encoding="utf-8")

    write_ladder_focus("parked_be", stage="be2", pipeline_dir=tmp_path)
    # Process BE3 on parked — should clear focus
    sf_a = d_a / "current_idea.json"
    out = process_budget_exceeded_project(
        "parked_be", st_a, sf_a, pipeline_dir=tmp_path
    )
    assert out.get("be3_consumed") is True
    assert out.get("status") == "budget_exceeded"
    assert out.get("last_decision") == "BYPASS_RETURN"
    focus = read_ladder_focus(tmp_path)
    assert focus is None

    # Tick can now pick next candidate
    n = tick_process_budget_yields(tmp_path)
    assert n == 1
    st_b2 = json.loads((d_b / "current_idea.json").read_text(encoding="utf-8"))
    assert st_b2.get("status") == "phase_1_executing"
    assert st_b2.get("be1_consumed") is True


def test_midflight_focus_blocks_second_candidate(tmp_path, monkeypatch):
    monkeypatch.setenv("BUDGET_BE1_AUTO_RETRY", "1")
    monkeypatch.setenv("BUDGET_LADDER_SERIAL", "1")
    projects = tmp_path / "projects"
    d_a = projects / "focus_mid" / "state"
    d_a.mkdir(parents=True)
    st_a = {
        "status": "phase_1_executing",
        "budget_strikes": 1,
        "be1_consumed": True,
        "ladder_focus": True,
        "phase": 1,
        "total_phases": 3,
    }
    (d_a / "current_idea.json").write_text(json.dumps(st_a), encoding="utf-8")
    d_b = projects / "waiting_be" / "state"
    d_b.mkdir(parents=True)
    st_b = {
        "status": "budget_exceeded",
        "budget_strikes": 1,
        "pre_budget_status": "phase_1_executing",
        "phase": 1,
        "total_phases": 3,
        "budget_yielded": True,
    }
    (d_b / "current_idea.json").write_text(json.dumps(st_b), encoding="utf-8")
    write_ladder_focus("focus_mid", stage="be1", pipeline_dir=tmp_path)
    assert _project_still_ladder_inflight(st_a) is True
    n = tick_process_budget_yields(tmp_path)
    assert n == 0  # mid-flight blocks others
    st_b2 = json.loads((d_b / "current_idea.json").read_text(encoding="utf-8"))
    assert st_b2.get("status") == "budget_exceeded"


def test_seed_serial_block_for_lock_path(tmp_path, monkeypatch):
    """Locked resume must honor serial_block when another focus is in-flight.

    Uses shared seed helpers (same path seeding.py calls). Dropping
    ``not serial_block`` on the lock branch in try_seed_process_budget_exceeded
    would resume the locked project and fail this test.
    """
    monkeypatch.setenv("BUDGET_LADDER_SERIAL", "1")
    monkeypatch.setenv("BUDGET_BE1_AUTO_RETRY", "1")
    monkeypatch.setattr(
        "pipeline.budget_ladder.get_pipeline_dir",
        lambda: tmp_path,
    )

    projects = tmp_path / "projects"
    # In-flight focus owner (mid-recovery, not budget_exceeded)
    d_other = projects / "other_proj" / "state"
    d_other.mkdir(parents=True)
    (d_other / "current_idea.json").write_text(
        json.dumps({
            "status": "phase_1_executing",
            "be1_consumed": True,
            "budget_strikes": 1,
            "phase": 1,
            "total_phases": 3,
            "ladder_focus": True,
        }),
        encoding="utf-8",
    )
    write_ladder_focus("other_proj", stage="be1", pipeline_dir=tmp_path)
    assert seed_serial_blocked("locked_proj", pipeline_dir=tmp_path) is True

    d_lock = projects / "locked_proj" / "state"
    d_lock.mkdir(parents=True)
    st = {
        "status": "budget_exceeded",
        "budget_lock": True,
        "budget_strikes": 0,
        "pre_budget_status": "phase_1_executing",
        "phase": 1,
        "total_phases": 3,
    }
    sf = d_lock / "current_idea.json"
    sf.write_text(json.dumps(st), encoding="utf-8")

    # Shared seed path (same helper seeding.py uses): must not resume under serial
    out = try_seed_process_budget_exceeded(
        "locked_proj", dict(st), sf, pipeline_dir=tmp_path
    )
    assert out.get("status") == "budget_exceeded"
    assert not out.get("be1_consumed")
    disk = json.loads(sf.read_text(encoding="utf-8"))
    assert disk.get("status") == "budget_exceeded"
    assert not disk.get("be1_consumed")

    # Control: clear focus → same lock state is allowed to resume
    clear_ladder_focus(tmp_path)
    assert seed_serial_blocked("locked_proj", pipeline_dir=tmp_path) is False
    out2 = try_seed_process_budget_exceeded(
        "locked_proj", dict(st), sf, pipeline_dir=tmp_path
    )
    assert out2.get("be1_consumed") is True
    assert out2.get("status") == "phase_1_executing"


def test_be3_debug_again_reenqueues_after_be2(tmp_path, monkeypatch):
    """BE3 DEBUG_AGAIN must clear prior BE2 debug flags and enqueue again."""
    monkeypatch.setenv("BUDGET_BE3_BLOCKER", "1")
    monkeypatch.setattr(
        "pipeline.budget_ladder.manager_decide",
        lambda report, state: "DEBUG_AGAIN",
    )
    bus = MagicMock()
    st = {
        "status": "budget_exceeded",
        "budget_strikes": 3,
        "be1_consumed": True,
        "be2_consumed": True,
        "be2_path": "debug",
        "be2_debug_enqueued": True,
        "be2_debug_attempted": True,
        "be2_pending": False,
        "pre_budget_status": "phase_1_executing",
        "phase": 1,
        "total_phases": 3,
        "budget_yielded": True,
    }
    sf = tmp_path / "current_idea.json"
    sf.write_text(json.dumps(st), encoding="utf-8")
    out = process_budget_exceeded_project(
        "p", st, sf, bus=bus, pipeline_dir=tmp_path
    )
    assert out.get("last_decision") == "DEBUG_AGAIN"
    assert out.get("be3_consumed") is True
    assert out.get("be2_path") == "debug"
    assert out.get("status") == "phase_1_executing"
    # Re-armed and enqueued a fresh systematic-debug pass
    assert out.get("be2_debug_enqueued") is True
    assert out.get("be2_debug_attempted") is True
    assert out.get("be2_pending") is False
    bus.send.assert_called_once()


def test_try_reset_be_prereq_no_bus_does_not_burn_once(tmp_path, monkeypatch):
    """Strike-2 BE2 debug without bus must not set prereq_reset_once."""
    from pipeline.budget_ladder import try_reset_be_prereq

    monkeypatch.setenv("BUDGET_BE2", "1")
    monkeypatch.setenv("BUDGET_PREREQ_RESET", "1")
    monkeypatch.setenv("BUDGET_LADDER_SERIAL", "0")
    projects = tmp_path / "projects"
    d = projects / "dep_be2" / "state"
    d.mkdir(parents=True)
    st = {
        "status": "budget_exceeded",
        "budget_strikes": 2,
        "be1_consumed": True,
        "pre_budget_status": "phase_1_executing",
        "phase": 1,
        "total_phases": 3,
    }
    sf = d / "current_idea.json"
    sf.write_text(json.dumps(st), encoding="utf-8")
    monkeypatch.setattr(
        "pipeline.budget_ladder.projects_dir",
        lambda: projects,
    )
    monkeypatch.setattr(
        "pipeline.budget_ladder.get_pipeline_dir",
        lambda: tmp_path,
    )
    ok = try_reset_be_prereq("dep_be2", waiter="waiter", bus=None)
    assert ok is False
    disk = json.loads(sf.read_text(encoding="utf-8"))
    assert not disk.get("prereq_reset_once")
    assert not disk.get("be2_consumed")
    assert disk.get("status") == "budget_exceeded"


def test_focus_ttl_clears_stale_lock(tmp_path, monkeypatch):
    monkeypatch.setenv("BUDGET_LADDER_FOCUS_TTL_HOURS", "0.25")
    old = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
    focus = {"slug": "stale", "stage": "be1", "since": old}
    assert focus_is_expired(focus) is True
    # Write expired focus + mid-flight project; tick should clear and process other
    monkeypatch.setenv("BUDGET_BE1_AUTO_RETRY", "1")
    monkeypatch.setenv("BUDGET_LADDER_SERIAL", "1")
    projects = tmp_path / "projects"
    d_a = projects / "stale" / "state"
    d_a.mkdir(parents=True)
    (d_a / "current_idea.json").write_text(
        json.dumps({
            "status": "phase_1_executing",
            "be1_consumed": True,
            "budget_strikes": 1,
            "phase": 1,
            "total_phases": 3,
        }),
        encoding="utf-8",
    )
    d_b = projects / "fresh_be" / "state"
    d_b.mkdir(parents=True)
    (d_b / "current_idea.json").write_text(
        json.dumps({
            "status": "budget_exceeded",
            "budget_strikes": 1,
            "pre_budget_status": "phase_1_executing",
            "phase": 1,
            "total_phases": 3,
            "budget_yielded": True,
        }),
        encoding="utf-8",
    )
    p = tmp_path / "state" / "budget_ladder_focus.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(focus), encoding="utf-8")
    n = tick_process_budget_yields(tmp_path)
    assert n == 1
    st_b = json.loads((d_b / "current_idea.json").read_text(encoding="utf-8"))
    assert st_b.get("be1_consumed") is True


def test_prefer_thin_field_ready_complete_and_near_done():
    from pipeline.budget_ladder import prefer_thin_field_ready

    assert prefer_thin_field_ready({"prefer_thin_field": True, "status": "complete"})
    assert prefer_thin_field_ready({
        "prefer_thin_field": True,
        "status": "phase_3_validating",
        "phase": 3,
        "total_phases": 3,
    })
    assert not prefer_thin_field_ready({
        "prefer_thin_field": True,
        "status": "budget_exceeded",
        "phase": 3,
        "total_phases": 3,
    })
    assert not prefer_thin_field_ready({
        "prefer_thin_field": True,
        "prefer_thin_field_shipped": True,
        "status": "complete",
    })
    assert not prefer_thin_field_ready({"status": "complete"})


def test_be2_strike2_thin_field_when_near_done(tmp_path, monkeypatch):
    """Fixture: strike 2 + near-done → thin_field path (not debug)."""
    monkeypatch.setenv("BUDGET_BE2", "1")
    st = {
        "status": "budget_exceeded",
        "budget_strikes": 2,
        "be1_consumed": True,
        "pre_budget_status": "phase_3_validating",
        "phase": 3,
        "total_phases": 3,
    }
    sf = tmp_path / "current_idea.json"
    sf.write_text(json.dumps(st), encoding="utf-8")
    out = process_budget_exceeded_project("near", st, sf)
    assert out.get("be2_path") == "thin_field"
    assert out.get("prefer_thin_field") is True
    assert out.get("be2_consumed") is True
    assert out["status"] == "phase_3_validating"


def test_be2_strike2_debug_when_not_near_done(tmp_path, monkeypatch):
    """Fixture: strike 2 mid-phase → debug path (needs bus; no-bus defers)."""
    monkeypatch.setenv("BUDGET_BE2", "1")
    st = {
        "status": "budget_exceeded",
        "budget_strikes": 2,
        "be1_consumed": True,
        "pre_budget_status": "phase_1_executing",
        "phase": 1,
        "total_phases": 3,
    }
    sf = tmp_path / "current_idea.json"
    sf.write_text(json.dumps(st), encoding="utf-8")
    # Without bus: defer (not thin_field)
    deferred = process_budget_exceeded_project("mid", dict(st), sf)
    assert deferred.get("status") == "budget_exceeded"
    assert not deferred.get("prefer_thin_field")
    assert not deferred.get("be2_consumed")
    # With bus: debug path
    bus = MagicMock()
    out = process_budget_exceeded_project("mid", dict(st), sf, bus=bus)
    assert out.get("be2_path") == "debug"
    assert not out.get("prefer_thin_field")
    assert out.get("be2_consumed") is True


def test_tick_prefer_thin_field_ship_calls_run(tmp_path, monkeypatch):
    from pipeline.budget_ladder import tick_prefer_thin_field_ship

    monkeypatch.setenv("BUDGET_THIN_FIELD_TICK", "1")
    projects = tmp_path / "projects"
    d = projects / "ship_me" / "state"
    d.mkdir(parents=True)
    st = {
        "status": "complete",
        "prefer_thin_field": True,
        "phase": 3,
        "total_phases": 3,
        "engine": "classic",
    }
    sf = d / "current_idea.json"
    sf.write_text(json.dumps(st), encoding="utf-8")

    class FakeShip:
        ok = True
        status = "field_proven"
        reason = "mock"

    called = {}

    def fake_run(project_dir, state=None, slug="", **kw):
        called["slug"] = slug
        called["prefer"] = (state or {}).get("prefer_thin_field")
        # Simulate ship writing field_proven
        p = Path(project_dir) / "state" / "current_idea.json"
        cur = json.loads(p.read_text(encoding="utf-8"))
        cur["status"] = "field_proven"
        p.write_text(json.dumps(cur), encoding="utf-8")
        return FakeShip()

    monkeypatch.setattr(
        "pipeline.engines.field_ship.run_thin_field_ship",
        fake_run,
    )
    n = tick_prefer_thin_field_ship(tmp_path, limit=1)
    assert n == 1
    assert called.get("slug") == "ship_me"
    disk = json.loads(sf.read_text(encoding="utf-8"))
    assert disk.get("prefer_thin_field") is False
    assert disk.get("prefer_thin_field_shipped") is True
    assert disk.get("status") == "field_proven"


def test_thin_ship_enabled_for_prefer_thin_field():
    from pipeline.engines.field_ship import thin_ship_enabled

    assert thin_ship_enabled({"prefer_thin_field": True, "engine": "classic"}) is True
