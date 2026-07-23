"""Unit tests for budget_ladder + active clock."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from pipeline.budget_ladder import (
    apply_budget_yield,
    auto_retry_clean,
    classify_blocker,
    effective_elapsed_minutes,
    manager_decide,
    apply_manager_decision,
    process_budget_exceeded_project,
    maybe_refresh_stale_session,
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
