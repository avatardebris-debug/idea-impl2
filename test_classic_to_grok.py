"""Unit tests for classic BE → sticky grok_build conversion."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from pipeline.budget_ladder import (
    apply_budget_yield,
    is_ladder_eligible,
    is_near_done,
    prefer_thin_field_ready,
    tick_process_budget_yields,
)
from pipeline.classic_to_grok import (
    apply_classic_to_grok,
    convert_state,
    is_classic_to_grok_parked,
    is_eligible_for_classic_to_grok,
    is_junk_slug,
    maybe_classic_to_grok_after_yield,
    note_class,
    unpark_classic_to_grok,
)


def _near_done_be(**extra):
    st = {
        "status": "budget_exceeded",
        "engine": "classic",
        "phase": 3,
        "total_phases": 3,
        "pre_budget_status": "phase_3_validating",
        "budget_strikes": 1,
        "budget_yielded": True,
        "budget_note": (
            "Yielded after 100 active-min (budget: 90 min for 3-phase project; strike=1)"
        ),
    }
    st.update(extra)
    return st


def test_is_junk_slug():
    assert is_junk_slug("test_foo") is True
    assert is_junk_slug("smoke_bar") is True
    assert is_junk_slug("fake_x") is True
    assert is_junk_slug("tmp_y") is True
    assert is_junk_slug("test_idea") is True
    assert is_junk_slug("proj") is True
    assert is_junk_slug("supportagent_workflow_builder") is False
    assert is_junk_slug("real_project") is False


def test_eligible_ok_near_done():
    ok, reason = is_eligible_for_classic_to_grok(
        _near_done_be(), "real_project", near_done_only=True
    )
    assert ok is True
    assert reason == "ok"


def test_eligible_refuse_junk():
    ok, reason = is_eligible_for_classic_to_grok(
        _near_done_be(), "test_junk", near_done_only=False
    )
    assert ok is False
    assert reason == "junk_slug"
    ok2, _ = is_eligible_for_classic_to_grok(
        _near_done_be(), "test_junk", force=True, near_done_only=False
    )
    assert ok2 is True


def test_eligible_refuse_lifetime():
    st = _near_done_be(
        budget_note=(
            "Force-completed: exceeded 1000 total retries across all phases "
            "(actual: 1200); strike=1"
        )
    )
    assert note_class(st) == "lifetime"
    ok, reason = is_eligible_for_classic_to_grok(
        st, "real_project", near_done_only=False
    )
    assert ok is False
    assert reason == "lifetime_fossil"
    ok2, _ = is_eligible_for_classic_to_grok(
        st, "real_project", force_lifetime=True, near_done_only=False
    )
    assert ok2 is True


def test_eligible_already_grok():
    st = _near_done_be(engine="grok_build")
    ok, reason = is_eligible_for_classic_to_grok(st, "real_project")
    assert ok is False
    assert reason == "already_grok_build"


def test_eligible_near_done_only():
    st = _near_done_be(phase=1, total_phases=3, pre_budget_status="phase_1_executing")
    ok, reason = is_eligible_for_classic_to_grok(
        st, "real_project", near_done_only=True
    )
    assert ok is False
    assert reason == "not_near_done"
    ok2, _ = is_eligible_for_classic_to_grok(
        st, "real_project", near_done_only=False
    )
    assert ok2 is True


def test_is_near_done_penultimate_review():
    """total-1 + validating/reviewing counts as near_done (fixed dead total-0 branch)."""
    st = {
        "phase": 2,
        "total_phases": 3,
        "pre_budget_status": "phase_2_validating",
    }
    assert is_near_done(st) is True
    st2 = {
        "phase": 2,
        "total_phases": 3,
        "pre_budget_status": "phase_2_executing",
    }
    assert is_near_done(st2) is False
    st3 = {"phase": 3, "total_phases": 3, "pre_budget_status": "phase_3_executing"}
    assert is_near_done(st3) is True


def test_convert_state_park_not_runnable():
    """Park: sticky grok, stay BE, prefer_thin deferred — not thin-ship ready."""
    st = _near_done_be()
    out = convert_state(st, mode="park")
    assert out["engine"] == "grok_build"
    assert out["status"] == "budget_exceeded"
    assert out.get("classic_to_grok_parked") is True
    assert out.get("prefer_thin_field") is not True
    assert out.get("classic_to_grok_prefer_thin") is True
    assert out["classic_to_grok_consumed"] is True
    assert out["classic_to_grok_at"]
    assert out["classic_to_grok_from"]["note_class"] == "active_yield"
    assert out["budget_strikes"] == 0
    assert out["last_decision"] == "CLASSIC_TO_GROK"
    assert out.get("budget_yielded") is True
    assert is_classic_to_grok_parked(out) is True
    assert prefer_thin_field_ready(out) is False


def test_convert_state_run_now_arms_thin():
    st = _near_done_be()
    out = convert_state(st, mode="run_now")
    assert out["engine"] == "grok_build"
    assert out["status"] == "phase_3_validating"
    assert out.get("classic_to_grok_parked") is not True
    assert out.get("prefer_thin_field") is True
    assert prefer_thin_field_ready(out) is True


def test_unpark_from_parked():
    parked = convert_state(_near_done_be(), mode="park")
    assert prefer_thin_field_ready(parked) is False
    live = unpark_classic_to_grok(parked)
    assert live["status"] == "phase_3_validating"
    assert live.get("classic_to_grok_parked") is not True
    assert live.get("prefer_thin_field") is True
    assert prefer_thin_field_ready(live) is True


def test_apply_idempotent_already_grok(tmp_path):
    slug = "already_grok_proj"
    pd = tmp_path / slug
    (pd / "state").mkdir(parents=True)
    st = {
        "status": "phase_2_executing",
        "engine": "grok_build",
        "phase": 2,
        "total_phases": 3,
    }
    (pd / "state" / "current_idea.json").write_text(
        json.dumps(st), encoding="utf-8"
    )
    res = apply_classic_to_grok(pd, dry_run=False, near_done_only=False)
    assert res["ok"] is True
    assert res["reason"] == "already_grok_build"
    assert res.get("idempotent") is True
    assert res["wrote"] is False


def test_apply_writes_bak_and_parked_state(tmp_path):
    slug = "canary_near_done"
    pd = tmp_path / slug
    (pd / "state").mkdir(parents=True)
    st = _near_done_be()
    sf = pd / "state" / "current_idea.json"
    sf.write_text(json.dumps(st), encoding="utf-8")
    res = apply_classic_to_grok(
        pd, dry_run=False, near_done_only=False, mode="park"
    )
    assert res["ok"] is True
    assert res["wrote"] is True
    assert res["bak"]
    assert Path(res["bak"]).is_file()
    written = json.loads(sf.read_text(encoding="utf-8"))
    assert written["engine"] == "grok_build"
    assert written["classic_to_grok_at"]
    assert written["status"] == "budget_exceeded"
    assert written.get("classic_to_grok_parked") is True
    assert written.get("prefer_thin_field") is not True


def test_maybe_auto_after_yield_park(monkeypatch):
    monkeypatch.setenv("CLASSIC_TO_GROK_ON_YIELD", "1")
    monkeypatch.setenv("CLASSIC_TO_GROK_AUTO_RUN", "0")
    monkeypatch.setenv("CLASSIC_TO_GROK_NEAR_DONE_ONLY", "1")
    st = _near_done_be()
    out = maybe_classic_to_grok_after_yield(st, slug="real_project")
    assert out["engine"] == "grok_build"
    assert out["classic_to_grok_mode"] == "park"
    assert out["status"] == "budget_exceeded"
    assert out.get("classic_to_grok_parked") is True
    assert out.get("ladder_focus") is not True
    assert prefer_thin_field_ready(out) is False


def test_maybe_auto_skips_not_near_done(monkeypatch):
    monkeypatch.setenv("CLASSIC_TO_GROK_ON_YIELD", "1")
    monkeypatch.setenv("CLASSIC_TO_GROK_NEAR_DONE_ONLY", "1")
    st = _near_done_be(phase=1, total_phases=3, pre_budget_status="phase_1_executing")
    out = maybe_classic_to_grok_after_yield(st, slug="real_project")
    assert out["status"] == "budget_exceeded"
    assert out.get("engine") == "classic"


def test_maybe_auto_disabled(monkeypatch):
    monkeypatch.setenv("CLASSIC_TO_GROK_ON_YIELD", "0")
    st = _near_done_be()
    out = maybe_classic_to_grok_after_yield(st, slug="real_project")
    assert out["status"] == "budget_exceeded"
    assert out.get("engine") == "classic"


def test_maybe_consumed_blocks_second(monkeypatch):
    monkeypatch.setenv("CLASSIC_TO_GROK_ON_YIELD", "1")
    monkeypatch.setenv("CLASSIC_TO_GROK_NEAR_DONE_ONLY", "1")
    st = _near_done_be()
    out1 = maybe_classic_to_grok_after_yield(st, slug="real_project")
    assert out1.get("classic_to_grok_consumed") is True
    # Second call is no-op (already consumed; still parked)
    out2 = maybe_classic_to_grok_after_yield(out1, slug="real_project")
    assert out2 is out1 or out2.get("classic_to_grok_parked") is True


def test_apply_budget_yield_auto_converts_classic_parked(monkeypatch):
    """classic yield → sticky grok park (status stays BE)."""
    monkeypatch.setenv("CLASSIC_TO_GROK_ON_YIELD", "1")
    monkeypatch.setenv("CLASSIC_TO_GROK_AUTO_RUN", "0")
    monkeypatch.setenv("CLASSIC_TO_GROK_NEAR_DONE_ONLY", "1")
    st = {
        "status": "phase_3_validating",
        "engine": "classic",
        "phase": 3,
        "total_phases": 3,
        "budget_strikes": 0,
    }
    out = apply_budget_yield(
        st,
        elapsed_min=100,
        phase_budget=90,
        total_phases=3,
        slug="real_near_done_project",
    )
    assert out["engine"] == "grok_build"
    assert out["classic_to_grok_consumed"] is True
    assert out["status"] == "budget_exceeded"
    assert out.get("classic_to_grok_parked") is True
    assert out.get("classic_to_grok_mode") == "park"
    assert prefer_thin_field_ready(out) is False


def test_apply_budget_yield_no_slug_no_convert(monkeypatch):
    monkeypatch.setenv("CLASSIC_TO_GROK_ON_YIELD", "1")
    st = {
        "status": "phase_3_validating",
        "engine": "classic",
        "phase": 3,
        "total_phases": 3,
    }
    out = apply_budget_yield(
        st, elapsed_min=100, phase_budget=90, total_phases=3
    )
    assert out["status"] == "budget_exceeded"
    assert out.get("engine") == "classic"
    assert out["budget_strikes"] == 1


def test_apply_budget_yield_classic_to_grok_false(monkeypatch):
    """Health lifetime contract: classic_to_grok=False never converts."""
    monkeypatch.setenv("CLASSIC_TO_GROK_ON_YIELD", "1")
    monkeypatch.setenv("CLASSIC_TO_GROK_NEAR_DONE_ONLY", "0")
    st = {
        "status": "phase_3_validating",
        "engine": "classic",
        "phase": 3,
        "total_phases": 3,
    }
    out = apply_budget_yield(
        st,
        elapsed_min=1000,
        phase_budget=80,
        total_phases=3,
        slug="lifetime_health_proj",
        classic_to_grok=False,
    )
    assert out["status"] == "budget_exceeded"
    assert out.get("engine") == "classic"
    assert out.get("classic_to_grok_at") is None
    assert out["budget_strikes"] == 1


def test_lifetime_note_refused_on_maybe(monkeypatch):
    monkeypatch.setenv("CLASSIC_TO_GROK_ON_YIELD", "1")
    monkeypatch.setenv("CLASSIC_TO_GROK_NEAR_DONE_ONLY", "0")
    st2 = _near_done_be(
        budget_note="Force-completed: exceeded 1000 total retries across all phases"
    )
    out = maybe_classic_to_grok_after_yield(st2, slug="lifetime_proj")
    assert out.get("engine") == "classic"
    assert out["status"] == "budget_exceeded"


def test_missing_engine_convertible(monkeypatch):
    monkeypatch.setenv("CLASSIC_TO_GROK_ON_YIELD", "1")
    monkeypatch.setenv("CLASSIC_TO_GROK_NEAR_DONE_ONLY", "1")
    st = {
        "status": "budget_exceeded",
        "phase": 3,
        "total_phases": 3,
        "pre_budget_status": "phase_3_reviewing",
        "budget_note": "Yielded after 50 active-min (budget: 40 min; strike=1)",
        "budget_strikes": 1,
    }
    ok, reason = is_eligible_for_classic_to_grok(
        st, "missing_engine_proj", near_done_only=True
    )
    assert ok is True, reason
    out = convert_state(st, mode="park")
    assert out["engine"] == "grok_build"
    assert out["status"] == "budget_exceeded"


def test_hermes_not_converted(monkeypatch):
    monkeypatch.setenv("CLASSIC_TO_GROK_ON_YIELD", "1")
    st = _near_done_be(engine="hermes")
    ok, reason = is_eligible_for_classic_to_grok(st, "hermes_proj")
    assert ok is False
    assert "engine_not_convertible" in reason


def test_run_now_focus_blocked_parks(tmp_path, monkeypatch):
    monkeypatch.setenv("BUDGET_LADDER_SERIAL", "1")
    slug = "focus_block_proj"
    pd = tmp_path / slug
    (pd / "state").mkdir(parents=True)
    sf = pd / "state" / "current_idea.json"
    sf.write_text(json.dumps(_near_done_be()), encoding="utf-8")
    # Pretend serial focus is busy
    with patch(
        "pipeline.classic_to_grok._serial_focus_free", return_value=False
    ):
        res = apply_classic_to_grok(
            pd,
            dry_run=False,
            near_done_only=False,
            mode="run_now",
            projects_root=tmp_path,
        )
    assert res["ok"] is True
    assert res.get("focus_blocked") is True
    assert res["mode"] == "park"
    written = json.loads(sf.read_text(encoding="utf-8"))
    assert written["status"] == "budget_exceeded"
    assert written.get("classic_to_grok_parked") is True


def test_auto_soft_resets_phase_retries(tmp_path, monkeypatch):
    monkeypatch.setenv("CLASSIC_TO_GROK_ON_YIELD", "1")
    monkeypatch.setenv("CLASSIC_TO_GROK_AUTO_RUN", "0")
    monkeypatch.setenv("CLASSIC_TO_GROK_NEAR_DONE_ONLY", "1")
    slug = "retry_reset_proj"
    pd = tmp_path / slug
    (pd / "state").mkdir(parents=True)
    pr = pd / "state" / "phase_retries.json"
    pr.write_text(json.dumps({"1": 500, "2": 500, "3": 500}), encoding="utf-8")
    st = _near_done_be(lifetime_retry_capped=True)
    out = maybe_classic_to_grok_after_yield(
        st, slug=slug, pipeline_dir=tmp_path, project_dir=pd
    )
    assert out["engine"] == "grok_build"
    assert out.get("classic_to_grok_parked") is True
    # Soft-reset succeeded → cap cleared
    assert out.get("lifetime_retry_capped") is not True
    data = json.loads(pr.read_text(encoding="utf-8"))
    assert data == {}


def test_find_grok_candidates_skips_parked(tmp_path):
    from pipeline.engines.hook import find_grok_build_candidates

    slug = "parked_hook_proj"
    pd = tmp_path / slug
    (pd / "state").mkdir(parents=True)
    st = convert_state(_near_done_be(pre_budget_status="phase_3_executing"), mode="park")
    # Even if someone forced status executing while parked flag set
    st["status"] = "phase_3_executing"
    st["classic_to_grok_parked"] = True
    (pd / "state" / "current_idea.json").write_text(json.dumps(st), encoding="utf-8")
    (pd / "phases" / "phase_3").mkdir(parents=True)
    (pd / "phases" / "phase_3" / "tasks.md").write_text(
        "# tasks\n- [ ] do stuff\n" + ("x" * 50), encoding="utf-8"
    )
    cands = find_grok_build_candidates(tmp_path)
    assert all(c[3] != slug for c in cands)


def test_eligible_consumed_blocks():
    st = _near_done_be(classic_to_grok_consumed=True)
    ok, reason = is_eligible_for_classic_to_grok(st, "real_project")
    assert ok is False
    assert reason == "already_consumed_episode"


def test_parked_not_ladder_eligible_when_drain_off(monkeypatch):
    """Parked classic→grok must not be ladder-eligible under default DRAIN=0."""
    monkeypatch.setenv("CLASSIC_TO_GROK_DRAIN", "0")
    monkeypatch.setenv("CLASSIC_TO_GROK_AUTO_RUN", "0")
    parked = convert_state(_near_done_be(), mode="park")
    assert parked.get("classic_to_grok_parked") is True
    assert parked.get("budget_yielded") is True
    assert is_ladder_eligible(parked) is False


def test_parked_ladder_eligible_when_drain_on(monkeypatch):
    monkeypatch.setenv("CLASSIC_TO_GROK_DRAIN", "1")
    monkeypatch.setenv("CLASSIC_TO_GROK_AUTO_RUN", "0")
    parked = convert_state(_near_done_be(), mode="park")
    assert is_ladder_eligible(parked) is True


def test_parked_does_not_starve_be1_tick(tmp_path, monkeypatch):
    """Parked no-op must not occupy the single ladder tick when DRAIN off.

    Regression: parked had budget_yielded → is_ladder_eligible True →
    tick_process_budget_yields selected it first (esp. with open dependents /
    alpha order) and returned 0 without advancing real BE1.
    """
    monkeypatch.setenv("BUDGET_BE1_AUTO_RETRY", "1")
    monkeypatch.setenv("BUDGET_LADDER_SERIAL", "1")
    monkeypatch.setenv("CLASSIC_TO_GROK_DRAIN", "0")
    monkeypatch.setenv("CLASSIC_TO_GROK_AUTO_RUN", "0")
    projects = tmp_path / "projects"

    # Alphabetically first + open dependents would win priority if eligible
    parked_name = "aaa_parked_grok"
    pd = projects / parked_name / "state"
    pd.mkdir(parents=True)
    parked = convert_state(
        _near_done_be(
            title=parked_name,
            budget_yielded=True,
            budget_yielded_at="2020-01-01T00:00:00+00:00",
        ),
        mode="park",
    )
    (pd / "current_idea.json").write_text(json.dumps(parked), encoding="utf-8")

    # Real BE1 classic recovery (alphabetically later)
    be1_name = "zzz_real_be1"
    bd = projects / be1_name / "state"
    bd.mkdir(parents=True)
    be1 = {
        "status": "budget_exceeded",
        "engine": "classic",
        "budget_strikes": 1,
        "pre_budget_status": "phase_2_executing",
        "phase": 2,
        "total_phases": 3,
        "budget_yielded": True,
        "budget_yielded_at": "2020-01-01T00:00:00+00:00",
    }
    (bd / "current_idea.json").write_text(json.dumps(be1), encoding="utf-8")

    # Even if parked would win open-deps priority, it must be ineligible
    with patch(
        "pipeline.budget_ladder._open_dependents",
        side_effect=lambda slug: (
            [{"title": "waiter"}] if slug == parked_name else []
        ),
    ):
        n = tick_process_budget_yields(tmp_path)

    assert n == 1
    parked_st = json.loads(
        (projects / parked_name / "state" / "current_idea.json").read_text(
            encoding="utf-8"
        )
    )
    be1_st = json.loads(
        (projects / be1_name / "state" / "current_idea.json").read_text(
            encoding="utf-8"
        )
    )
    # Parked stays parked BE; BE1 advanced
    assert parked_st.get("status") == "budget_exceeded"
    assert parked_st.get("classic_to_grok_parked") is True
    assert be1_st.get("status") == "phase_2_executing"
    assert be1_st.get("be1_consumed") is True
