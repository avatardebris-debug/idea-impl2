"""Unit tests for pipeline.troubleshoot_consumer (ship_insufficient recovery)."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.troubleshoot_consumer import (
    process_troubleshoot_project,
    restorable_pre_budget_status,
    tick_troubleshoot_recovery,
    troubleshoot_consumer_enabled,
)
from pipeline.troubleshoot_gate import (
    ACTION_DEBUG_TARGETED,
    ACTION_FIELD_REPAIR_ONCE,
    ACTION_FIX_GATE_ONLY,
    ACTION_PARK,
    ACTION_REPLAN_MASTER,
    ACTION_THIN_FIELD_RETRY,
    CLASS_GATE_FALSE_BLOCK,
    CLASS_SPIN_NO_PROGRESS,
)


def _proj(
    tmp: Path,
    *,
    slug: str = "proj",
    status: str = "ship_insufficient",
    phase: int = 3,
    total: int = 3,
    action: str = ACTION_FIX_GATE_ONLY,
    primary: str = CLASS_GATE_FALSE_BLOCK,
    fingerprint: str = "fp_abc123",
    extra_state: dict | None = None,
) -> Path:
    p = tmp / "projects" / slug
    (p / "state").mkdir(parents=True)
    idea = {
        "title": slug,
        "status": status,
        "phase": phase,
        "total_phases": total,
        "engine": "grok_build",
        "slug": slug,
        "last_recovery_action": action,
        "last_recovery_class": primary,
    }
    if extra_state:
        idea.update(extra_state)
    (p / "state" / "current_idea.json").write_text(
        json.dumps(idea, indent=2), encoding="utf-8"
    )
    decision = {
        "schema": "recovery_decision.v1",
        "slug": slug,
        "status": status,
        "primary_class": primary,
        "recommended_action": action,
        "fail_fingerprint": fingerprint,
        "prompt_inject": f"hint for {action}",
        "confidence": "high",
        "evidence": ["test"],
    }
    (p / "state" / "recovery_decision.json").write_text(
        json.dumps(decision, indent=2), encoding="utf-8"
    )
    return p


def _load(p: Path) -> dict:
    return json.loads((p / "state" / "current_idea.json").read_text(encoding="utf-8"))


def test_consumer_enabled_default_on(monkeypatch):
    monkeypatch.delenv("TROUBLESHOOT_CONSUMER", raising=False)
    assert troubleshoot_consumer_enabled() is True
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "0")
    assert troubleshoot_consumer_enabled() is False


def test_consumer_writes_durable_history(tmp_path, monkeypatch):
    """Consume act appends recovery_history + pipeline metrics (reboot-safe)."""
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    try:
        from pipeline.paths import reload_pipeline_dir

        reload_pipeline_dir()
    except Exception:
        pass
    p = _proj(tmp_path, action=ACTION_THIN_FIELD_RETRY)
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    hist = p / "state" / "recovery_history.jsonl"
    assert hist.is_file()
    lines = [json.loads(x) for x in hist.read_text(encoding="utf-8").splitlines() if x.strip()]
    consume = [r for r in lines if r.get("schema") == "recovery_consume.v1"]
    assert consume, "expected recovery_consume.v1 line"
    assert consume[-1]["tag"] in ("acted", "yielded")
    pipe_hist = tmp_path / "metrics" / "troubleshoot_consumer_history.jsonl"
    assert pipe_hist.is_file()


def test_fix_gate_only_rearms_prefer_thin(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    p = _proj(tmp_path, action=ACTION_FIX_GATE_ONLY, fingerprint="fgate1")
    st = _load(p)
    st["complete_blocked_reason"] = "3 open task checkbox(es) on project"
    st["ship_outcome"] = "ship_insufficient"
    (p / "state" / "current_idea.json").write_text(json.dumps(st), encoding="utf-8")

    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    out = _load(p)
    assert out.get("prefer_thin_field") is True
    assert out.get("prefer_thin_field_shipped") is False
    assert out.get("status") == "complete"  # phase >= total
    assert out.get("recovery_act_count") == 1
    assert out.get("recovery_acted_fingerprint") == "fgate1"
    assert out.get("complete_blocked_waived") is True
    assert out.get("status") != "budget_exceeded"
    # Sticky ship outcome cleared so thin ship can re-stamp
    assert "ship_outcome" not in out or out.get("ship_outcome") is None


def test_thin_field_retry_rearms(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    p = _proj(
        tmp_path,
        action=ACTION_THIN_FIELD_RETRY,
        fingerprint="retry1",
        extra_state={"prefer_thin_field_shipped": True, "prefer_thin_field": False},
    )
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    out = _load(p)
    assert out.get("prefer_thin_field") is True
    assert out.get("prefer_thin_field_shipped") is False
    assert out.get("status") == "complete"
    assert out.get("recovery_act_count") == 1


def test_field_repair_once_then_yield(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    p = _proj(
        tmp_path,
        action=ACTION_FIELD_REPAIR_ONCE,
        fingerprint="repair_fp",
    )
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    out = _load(p)
    assert out.get("prefer_thin_field") is True
    assert out.get("recovery_field_repair_acts") == 1
    assert out.get("status") != "budget_exceeded"

    out["status"] = "ship_insufficient"
    out["prefer_thin_field"] = False
    out["prefer_thin_field_shipped"] = True
    (p / "state" / "current_idea.json").write_text(json.dumps(out), encoding="utf-8")

    n2 = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n2 == 1
    out2 = _load(p)
    assert out2.get("status") == "budget_exceeded"
    # Restorable phase_* for BE1 — not ship_insufficient alone
    assert str(out2.get("pre_budget_status") or "").startswith("phase_")
    assert out2.get("recovery_ship_status") == "ship_insufficient"
    assert "Ship recovery exhausted" in (out2.get("budget_note") or "")
    assert out2.get("budget_yielded") is True


def test_field_repair_once_second_without_fingerprint_match(tmp_path: Path, monkeypatch):
    """FIELD_REPAIR_ONCE with repair_acts already 1 yields even on new path."""
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    p = _proj(
        tmp_path,
        action=ACTION_FIELD_REPAIR_ONCE,
        fingerprint="new_fp_only",
        extra_state={
            "recovery_field_repair_acts": 1,
            "recovery_act_count": 0,
        },
    )
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    out = _load(p)
    assert out.get("status") == "budget_exceeded"
    assert "field_repair_once_exhausted" in (out.get("budget_note") or "")


def test_park_yields_budget_exceeded(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    p = _proj(
        tmp_path,
        action=ACTION_PARK,
        primary=CLASS_SPIN_NO_PROGRESS,
        fingerprint="park_fp",
    )
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    out = _load(p)
    assert out.get("status") == "budget_exceeded"
    assert str(out.get("pre_budget_status") or "").startswith("phase_")
    assert out.get("recovery_ship_status") == "ship_insufficient"
    note = out.get("budget_note") or ""
    assert "action=PARK" in note
    assert "spin_no_progress" in note or CLASS_SPIN_NO_PROGRESS in note
    assert "prior=ship_insufficient" in note
    assert out.get("budget_strikes", 0) >= 1


def test_replan_master_yields(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    p = _proj(tmp_path, action=ACTION_REPLAN_MASTER, fingerprint="replan1")
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    out = _load(p)
    assert out.get("status") == "budget_exceeded"
    assert "REPLAN_MASTER" in (out.get("budget_note") or "")


def test_debug_targeted_rearms_with_hint_no_be2(tmp_path: Path, monkeypatch):
    """DEBUG_TARGETED is pure thin re-arm; no be2_path/be2_pending pollution."""
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    p = _proj(tmp_path, action=ACTION_DEBUG_TARGETED, fingerprint="dbg1")
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    out = _load(p)
    assert out.get("prefer_thin_field") is True
    assert out.get("recovery_debug_hint")
    assert out.get("status") == "complete"
    assert out.get("be2_path") != "debug"
    assert not out.get("be2_pending")


def test_double_act_same_fingerprint_yields(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    p = _proj(
        tmp_path,
        action=ACTION_THIN_FIELD_RETRY,
        fingerprint="same_fp",
        extra_state={
            "recovery_acted_fingerprint": "same_fp",
            "recovery_act_count": 1,
            "recovery_episode_fingerprint": "same_fp",
        },
    )
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    out = _load(p)
    assert out.get("status") == "budget_exceeded"
    assert "same_fingerprint_after_act" in (out.get("budget_note") or "")


def test_max_acts_yields(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    monkeypatch.setenv("TROUBLESHOOT_MAX_ACTS", "2")
    p = _proj(
        tmp_path,
        action=ACTION_THIN_FIELD_RETRY,
        fingerprint="ep_fp",
        extra_state={
            "recovery_act_count": 2,
            "recovery_episode_fingerprint": "ep_fp",
            "recovery_acted_fingerprint": "other_old_fp",
        },
    )
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    out = _load(p)
    assert out.get("status") == "budget_exceeded"
    assert "max_acts" in (out.get("budget_note") or "")


def test_skips_field_proven(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    _proj(tmp_path, status="field_proven", action=ACTION_FIX_GATE_ONLY)
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 0


def test_skips_without_recovery_artifacts(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    p = tmp_path / "projects" / "bare"
    (p / "state").mkdir(parents=True)
    (p / "state" / "current_idea.json").write_text(
        json.dumps(
            {
                "status": "ship_insufficient",
                "phase": 2,
                "total_phases": 3,
            }
        ),
        encoding="utf-8",
    )
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 0


def test_disabled_returns_zero(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "0")
    _proj(tmp_path, action=ACTION_FIX_GATE_ONLY)
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 0


def test_serial_limit(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    _proj(tmp_path, slug="a", action=ACTION_PARK, fingerprint="fa")
    _proj(tmp_path, slug="b", action=ACTION_PARK, fingerprint="fb")
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    statuses = []
    for slug in ("a", "b"):
        st = json.loads(
            (tmp_path / "projects" / slug / "state" / "current_idea.json").read_text(
                encoding="utf-8"
            )
        )
        statuses.append(st.get("status"))
    assert statuses.count("budget_exceeded") == 1
    assert statuses.count("ship_insufficient") == 1


def test_deeper_work_needed_with_decision(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    p = _proj(
        tmp_path,
        status="deeper_work_needed",
        action=ACTION_PARK,
        fingerprint="dwn1",
    )
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    out = _load(p)
    assert out.get("status") == "budget_exceeded"
    assert out.get("recovery_ship_status") == "deeper_work_needed"
    assert str(out.get("pre_budget_status") or "").startswith("phase_")


def test_process_direct_fix_gate(tmp_path: Path):
    p = _proj(tmp_path, action=ACTION_FIX_GATE_ONLY, fingerprint="direct1")
    st = _load(p)
    new_st, tag = process_troubleshoot_project(p, st)
    assert tag == "acted"
    assert new_st.get("prefer_thin_field") is True
    assert new_st.get("status") == "complete"


def test_run_loop_import_ok():
    """run_loop import path must not break after consumer wiring."""
    from pipeline import run_loop  # noqa: F401
    from pipeline.troubleshoot_consumer import tick_troubleshoot_recovery as fn

    assert callable(fn)


def test_prefer_thin_ready_after_consumer(tmp_path: Path, monkeypatch):
    """After FIX_GATE_ONLY, prefer_thin_field_ready should accept the project."""
    from pipeline.budget_ladder import prefer_thin_field_ready

    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    p = _proj(tmp_path, action=ACTION_FIX_GATE_ONLY, fingerprint="ready1")
    tick_troubleshoot_recovery(tmp_path, limit=1)
    out = _load(p)
    assert prefer_thin_field_ready(out) is True


def test_mid_phase_cheap_act_yields_not_noop(tmp_path: Path, monkeypatch):
    """phase < total: cheap re-arm cannot satisfy prefer_thin_field_ready → yield."""
    from pipeline.budget_ladder import prefer_thin_field_ready

    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    p = _proj(
        tmp_path,
        action=ACTION_THIN_FIELD_RETRY,
        fingerprint="mid1",
        phase=2,
        total=3,
    )
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    out = _load(p)
    assert out.get("status") == "budget_exceeded"
    assert "mid_phase_not_thin_ready" in (out.get("budget_note") or "")
    assert out.get("pre_budget_status") == "phase_2_executing"
    assert prefer_thin_field_ready(out) is False


def test_restorable_pre_budget_phase_done():
    st = {
        "status": "ship_insufficient",
        "phase": 5,
        "total_phases": 5,
    }
    pre = restorable_pre_budget_status(st)
    assert pre == "phase_5_validating"
    assert pre.startswith("phase_")


def test_be1_after_consumer_yield_is_ship_adjacent(tmp_path: Path, monkeypatch):
    """Yield → process_budget_exceeded BE1 → near-done status, not blind re-exec."""
    from pipeline.budget_ladder import process_budget_exceeded_project

    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    monkeypatch.setenv("BUDGET_BE1_AUTO_RETRY", "1")
    p = _proj(
        tmp_path,
        action=ACTION_PARK,
        fingerprint="be1fp",
        phase=3,
        total=3,
    )
    tick_troubleshoot_recovery(tmp_path, limit=1)
    out = _load(p)
    assert out.get("status") == "budget_exceeded"
    assert out.get("budget_strikes") == 1
    pre = out.get("pre_budget_status")
    assert pre == "phase_3_validating"

    sf = p / "state" / "current_idea.json"
    resumed = process_budget_exceeded_project("proj", out, sf)
    assert resumed.get("status") == "phase_3_validating"
    assert resumed.get("be1_consumed") is True
    # Not demoted to executing
    assert resumed.get("status") != "phase_3_executing"


def test_new_fingerprint_resets_act_count(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    p = _proj(
        tmp_path,
        action=ACTION_FIX_GATE_ONLY,
        fingerprint="new_fp_xyz",
        extra_state={
            "recovery_act_count": 5,
            "recovery_episode_fingerprint": "old_fp",
            "recovery_acted_fingerprint": "old_fp",
            "recovery_field_repair_acts": 1,
        },
    )
    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    out = _load(p)
    # Episode reset allowed a cheap act again
    assert out.get("status") == "complete"
    assert out.get("prefer_thin_field") is True
    assert out.get("recovery_act_count") == 1
    assert out.get("recovery_episode_fingerprint") == "new_fp_xyz"


def test_acted_out_priority_for_thin_tick(tmp_path: Path, monkeypatch):
    """preferred_slugs from consumer win over another alphabetically-first ready project."""
    from pipeline.budget_ladder import tick_prefer_thin_field_ship

    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    monkeypatch.setenv("BUDGET_THIN_FIELD_TICK", "1")

    # Already-ready project sorts first ("aaa")
    aaa = tmp_path / "projects" / "aaa" / "state"
    aaa.mkdir(parents=True)
    (aaa / "current_idea.json").write_text(
        json.dumps(
            {
                "status": "complete",
                "prefer_thin_field": True,
                "phase": 3,
                "total_phases": 3,
                "engine": "classic",
            }
        ),
        encoding="utf-8",
    )
    # Consumer will re-arm zzz
    p = _proj(
        tmp_path,
        slug="zzz",
        action=ACTION_FIX_GATE_ONLY,
        fingerprint="prio1",
    )

    acted: list[str] = []
    n = tick_troubleshoot_recovery(tmp_path, limit=1, acted_out=acted)
    assert n == 1
    assert acted == ["zzz"]

    called: list[str] = []

    class FakeShip:
        ok = True
        status = "field_proven"
        reason = "mock"

    def fake_run(project_dir, state=None, slug="", **kw):
        called.append(slug or Path(project_dir).name)
        return FakeShip()

    monkeypatch.setattr(
        "pipeline.engines.field_ship.run_thin_field_ship",
        fake_run,
    )
    n_tf = tick_prefer_thin_field_ship(
        tmp_path, limit=1, preferred_slugs=acted
    )
    assert n_tf == 1
    assert called == ["zzz"]


def test_empty_fingerprint_max_acts_bound(tmp_path: Path, monkeypatch):
    """Missing fingerprint still bounds thrash via max_acts."""
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    monkeypatch.setenv("TROUBLESHOOT_MAX_ACTS", "1")
    p = _proj(
        tmp_path,
        action=ACTION_THIN_FIELD_RETRY,
        fingerprint="",
        extra_state={"recovery_act_count": 1},
    )
    # Empty fp in decision file
    dec = json.loads((p / "state" / "recovery_decision.json").read_text(encoding="utf-8"))
    dec["fail_fingerprint"] = ""
    (p / "state" / "recovery_decision.json").write_text(
        json.dumps(dec), encoding="utf-8"
    )
    st = _load(p)
    st["last_recovery_action"] = ACTION_THIN_FIELD_RETRY
    (p / "state" / "current_idea.json").write_text(json.dumps(st), encoding="utf-8")

    n = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n == 1
    out = _load(p)
    assert out.get("status") == "budget_exceeded"
    assert "max_acts" in (out.get("budget_note") or "")


def test_empty_fingerprint_synthesized_for_same_fp_anti_thrash(
    tmp_path: Path, monkeypatch,
):
    """Empty fail_fingerprint becomes no_fp:{slug}:{action}:... so second act yields."""
    monkeypatch.setenv("TROUBLESHOOT_CONSUMER", "1")
    monkeypatch.setenv("TROUBLESHOOT_MAX_ACTS", "5")
    p = _proj(
        tmp_path,
        slug="empty_fp_proj",
        action=ACTION_THIN_FIELD_RETRY,
        fingerprint="",
        primary=CLASS_SPIN_NO_PROGRESS,
    )
    dec = json.loads((p / "state" / "recovery_decision.json").read_text(encoding="utf-8"))
    dec["fail_fingerprint"] = ""
    (p / "state" / "recovery_decision.json").write_text(
        json.dumps(dec), encoding="utf-8"
    )

    # First tick: cheap act with synthesized fingerprint
    n1 = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n1 == 1
    out1 = _load(p)
    assert out1.get("prefer_thin_field") is True
    syn = out1.get("recovery_acted_fingerprint") or ""
    assert syn.startswith("no_fp:empty_fp_proj:")
    assert ACTION_THIN_FIELD_RETRY in syn
    assert out1.get("recovery_act_count") == 1

    # Simulate ship stall again with same empty decision → same synthetic key → yield
    out1["status"] = "ship_insufficient"
    out1["prefer_thin_field"] = False
    (p / "state" / "current_idea.json").write_text(json.dumps(out1), encoding="utf-8")

    n2 = tick_troubleshoot_recovery(tmp_path, limit=1)
    assert n2 == 1
    out2 = _load(p)
    assert out2.get("status") == "budget_exceeded"
    assert "same_fingerprint_after_act" in (out2.get("budget_note") or "")
