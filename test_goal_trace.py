"""goal_trace.v1 unit tests — closed outcomes + train_weight hygiene."""

from __future__ import annotations

from pathlib import Path

from pipeline import goal_trace
from pipeline.goal_trace import (
    CLOSED_OUTCOMES,
    FAILURE_BASELINE,
    FAILURE_EXTERNAL,
    FAILURE_PATH,
    FAILURE_SECRET,
    FAILURE_SMOKE,
    OUTCOME_DEEPER,
    OUTCOME_FAILED,
    OUTCOME_HUMAN_REJECTED,
    OUTCOME_PROVEN,
    OUTCOME_REVOKED,
    default_train_weight,
    legacy_status_for_outcome,
    map_legacy_status,
    normalize_outcome,
    set_outcome,
)


def test_sandbox_file_exists_goal(tmp_path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    try:
        from pipeline.paths import reload_pipeline_dir

        reload_pipeline_dir()
    except Exception:
        pass
    f = tmp_path / "proof.txt"
    f.write_text("x", encoding="utf-8")
    tr = goal_trace.sandbox_file_exists_goal(f)
    assert tr["schema"] == "goal_trace.v1"
    assert tr["status"] == "goal_proven"
    assert tr["outcome"] == OUTCOME_PROVEN
    assert tr["oracle"]["pass"] is True
    assert tr["train_weight"] >= 3.0
    assert (tmp_path / "goal_traces" / f"{tr['goal_id']}.json").is_file()


def test_append_and_finalize_failed(tmp_path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.delenv("KEEP_GOAL_TRACES", raising=False)
    try:
        from pipeline.paths import reload_pipeline_dir

        reload_pipeline_dir()
    except Exception:
        pass
    tr = goal_trace.start_trace("do thing", mode="sandbox")
    goal_trace.append_event(tr, type="think", content="planning")
    out = goal_trace.finalize_trace(tr, status="goal_failed", oracle={"name": "x", "pass": False})
    assert out["status"] == "goal_failed"
    assert out["outcome"] == OUTCOME_FAILED
    assert out["train_weight"] == 0.1


def test_keep_goal_traces_false_no_disk(tmp_path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.setenv("KEEP_GOAL_TRACES", "false")
    try:
        from pipeline.paths import reload_pipeline_dir

        reload_pipeline_dir()
    except Exception:
        pass
    assert goal_trace.keep_goal_traces() is False
    tr = goal_trace.start_trace("skip write", mode="sandbox")
    goal_trace.append_event(tr, type="think", content="x")
    goal_trace.finalize_trace(tr, status="goal_proven", oracle={"name": "x", "pass": True})
    assert tr["status"] == "goal_proven"
    assert tr["outcome"] == OUTCOME_PROVEN
    assert not (tmp_path / "goal_traces" / f"{tr['goal_id']}.json").is_file()
    # load/trace_path must not mkdir empty goal_traces/ when flag is off
    assert goal_trace.load_trace(tr["goal_id"]) is None
    assert not (tmp_path / "goal_traces").exists()


def test_closed_outcomes_and_legacy_map():
    assert CLOSED_OUTCOMES == {
        OUTCOME_PROVEN,
        OUTCOME_FAILED,
        OUTCOME_DEEPER,
        OUTCOME_REVOKED,
        OUTCOME_HUMAN_REJECTED,
    }
    assert map_legacy_status("goal_proven") == OUTCOME_PROVEN
    assert map_legacy_status("goal_failed") == OUTCOME_FAILED
    assert map_legacy_status("deeper_work_needed") == OUTCOME_DEEPER
    assert map_legacy_status("field_proven") == OUTCOME_PROVEN
    assert map_legacy_status("field_test_passed") == OUTCOME_DEEPER
    assert map_legacy_status("ship_insufficient") == OUTCOME_FAILED
    assert map_legacy_status("revoked") == OUTCOME_REVOKED
    assert map_legacy_status("human_rejected") == OUTCOME_HUMAN_REJECTED
    assert map_legacy_status("in_progress") is None
    assert normalize_outcome("proven") == OUTCOME_PROVEN
    assert legacy_status_for_outcome(OUTCOME_PROVEN) == "goal_proven"
    assert legacy_status_for_outcome(OUTCOME_DEEPER) == "deeper_work_needed"


def test_default_train_weight_rules():
    assert default_train_weight(OUTCOME_PROVEN) == 4.0
    assert default_train_weight(OUTCOME_FAILED) == 0.1
    assert default_train_weight(OUTCOME_DEEPER) == 0.0
    assert default_train_weight(OUTCOME_REVOKED) == 0.5
    assert default_train_weight(OUTCOME_HUMAN_REJECTED) == 0.0

    # External / untrusted never high weight even if "proven"
    assert default_train_weight(OUTCOME_PROVEN, trust="external") == 0.2
    assert default_train_weight(OUTCOME_PROVEN, trust="untrusted") == 0.2
    assert default_train_weight(OUTCOME_PROVEN, failure_class=FAILURE_EXTERNAL) == 0.2

    # Baseline-only field not high weight
    w_base = default_train_weight(OUTCOME_PROVEN, claim="field_baseline")
    assert w_base <= 0.5
    w_ftp = default_train_weight(OUTCOME_DEEPER, claim="field_test_passed")
    assert w_ftp <= 0.5
    assert default_train_weight(OUTCOME_DEEPER, failure_class=FAILURE_BASELINE) <= 0.5

    # Dual-gated field_proven high
    assert default_train_weight(OUTCOME_PROVEN, claim="field_proven") == 4.0
    assert default_train_weight(OUTCOME_PROVEN, claim="dual_gate") == 4.0

    # Structural / block promote not high
    assert default_train_weight(OUTCOME_PROVEN, claim="block_promote") == 0.0
    assert default_train_weight(OUTCOME_PROVEN, claim="mcp_smoke") == 1.0


def test_set_outcome_and_finalize_with_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.delenv("KEEP_GOAL_TRACES", raising=False)
    try:
        from pipeline.paths import reload_pipeline_dir

        reload_pipeline_dir()
    except Exception:
        pass

    tr = goal_trace.start_trace("prove thing", mode="sandbox")
    assert tr["outcome"] is None
    assert tr["failure_class"] is None

    set_outcome(
        tr,
        OUTCOME_FAILED,
        failure_class=FAILURE_SMOKE,
        claim="mcp_smoke",
    )
    assert tr["outcome"] == OUTCOME_FAILED
    assert tr["status"] == "goal_failed"
    assert tr["failure_class"] == FAILURE_SMOKE
    assert tr["train_weight"] == 0.1

    tr2 = goal_trace.start_trace("ok thing", mode="goal_policy")
    out = goal_trace.finalize_trace(
        tr2,
        outcome=OUTCOME_PROVEN,
        claim="capability_invoke",
        oracle={"name": "capability_invoke", "pass": True},
    )
    assert out["outcome"] == OUTCOME_PROVEN
    assert out["status"] == "goal_proven"
    assert out["train_weight"] == 4.0
    assert out["ended_at"]
    assert out["failure_class"] is None
    assert (tmp_path / "goal_traces" / f"{out['goal_id']}.json").is_file()


def test_finalize_legacy_status_maps_outcome(tmp_path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.delenv("KEEP_GOAL_TRACES", raising=False)
    try:
        from pipeline.paths import reload_pipeline_dir

        reload_pipeline_dir()
    except Exception:
        pass
    tr = goal_trace.start_trace("deeper path", mode="goal_policy")
    out = goal_trace.finalize_trace(
        tr,
        status="deeper_work_needed",
        oracle={"name": "policy_yield", "pass": False},
        train_weight=0.0,
    )
    assert out["status"] == "deeper_work_needed"
    assert out["outcome"] == OUTCOME_DEEPER
    assert out["train_weight"] == 0.0


def test_finalize_external_low_weight(tmp_path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.delenv("KEEP_GOAL_TRACES", raising=False)
    try:
        from pipeline.paths import reload_pipeline_dir

        reload_pipeline_dir()
    except Exception:
        pass
    tr = goal_trace.start_trace("external tool", mode="external")
    out = goal_trace.finalize_trace(
        tr,
        outcome=OUTCOME_PROVEN,
        trust="external",
        oracle={"name": "external_smoke", "pass": True},
    )
    assert out["outcome"] == OUTCOME_PROVEN
    assert out["train_weight"] == 0.2  # never high on external


def test_explicit_train_weight_clamped_for_external(tmp_path, monkeypatch):
    """Hard rule: train_weight override cannot bypass external max (≤0.2)."""
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.delenv("KEEP_GOAL_TRACES", raising=False)
    try:
        from pipeline.paths import reload_pipeline_dir

        reload_pipeline_dir()
    except Exception:
        pass
    tr = goal_trace.start_trace("external override", mode="external")
    out = goal_trace.finalize_trace(
        tr,
        outcome=OUTCOME_PROVEN,
        trust="external",
        train_weight=4.0,  # would be high if not clamped
        oracle={"name": "external_smoke", "pass": True},
    )
    assert out["train_weight"] == goal_trace.EXTERNAL_MAX_TRAIN_WEIGHT
    assert out["train_weight"] <= 0.2

    tr2 = goal_trace.start_trace("untrusted override", mode="external")
    set_outcome(
        tr2,
        OUTCOME_PROVEN,
        trust="untrusted",
        train_weight=99.0,
        save=False,
    )
    assert tr2["train_weight"] == goal_trace.EXTERNAL_MAX_TRAIN_WEIGHT

    tr3 = goal_trace.start_trace("fc external", mode="external")
    set_outcome(
        tr3,
        OUTCOME_PROVEN,
        failure_class=FAILURE_EXTERNAL,
        train_weight=3.0,
        save=False,
    )
    assert tr3["train_weight"] == goal_trace.EXTERNAL_MAX_TRAIN_WEIGHT

    # Trusted claims still allow high explicit override
    tr4 = goal_trace.start_trace("trusted high", mode="goal_policy")
    set_outcome(
        tr4,
        OUTCOME_PROVEN,
        claim="capability_invoke",
        train_weight=4.0,
        save=False,
    )
    assert tr4["train_weight"] == 4.0


def test_finalize_secret_fail(tmp_path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.delenv("KEEP_GOAL_TRACES", raising=False)
    try:
        from pipeline.paths import reload_pipeline_dir

        reload_pipeline_dir()
    except Exception:
        pass
    tr = goal_trace.start_trace("block sandbox", mode="block_promote")
    out = goal_trace.finalize_trace(
        tr,
        outcome=OUTCOME_FAILED,
        failure_class=FAILURE_SECRET,
        claim="block_promote",
        oracle={"name": "skill_sandbox_fixture", "pass": False},
    )
    assert out["outcome"] == OUTCOME_FAILED
    assert out["failure_class"] == FAILURE_SECRET
    assert out["train_weight"] == 0.1


def test_set_outcome_unknown_raises():
    tr = {"goal_id": "x", "status": "in_progress", "train_weight": 0.0}
    try:
        set_outcome(tr, "not_a_real_outcome", save=False)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "unknown outcome" in str(exc)
