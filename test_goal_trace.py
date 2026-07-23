"""goal_trace.v1 unit tests."""

from __future__ import annotations

from pathlib import Path

from pipeline import goal_trace


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
    assert tr["oracle"]["pass"] is True
    assert (tmp_path / "goal_traces" / f"{tr['goal_id']}.json").is_file()


def test_append_and_finalize_failed(tmp_path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    try:
        from pipeline.paths import reload_pipeline_dir

        reload_pipeline_dir()
    except Exception:
        pass
    tr = goal_trace.start_trace("do thing", mode="sandbox")
    goal_trace.append_event(tr, type="think", content="planning")
    out = goal_trace.finalize_trace(tr, status="goal_failed", oracle={"name": "x", "pass": False})
    assert out["status"] == "goal_failed"
    assert out["train_weight"] == 0.1
