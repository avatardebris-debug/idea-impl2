"""Tests for cloud classic pipeline improvements (parallel defaults, bus wake, llm metrics, sidecar)."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest


def test_resolve_parallelism_local_default(monkeypatch):
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)
    monkeypatch.delenv("PIPELINE_CLOUD_PARALLEL_SEEDS", raising=False)
    monkeypatch.delenv("PIPELINE_CLOUD_EXECUTORS", raising=False)
    from pipeline.cloud_defaults import resolve_parallelism

    s, e = resolve_parallelism(
        parallel_seeds=None, num_executors=None, seeds_explicit=False, executors_explicit=False
    )
    assert s == 1 and e == 1


def test_resolve_parallelism_cloud_defaults(monkeypatch):
    monkeypatch.setenv("PIPELINE_CLOUD", "1")
    monkeypatch.delenv("PIPELINE_CLOUD_PARALLEL_SEEDS", raising=False)
    monkeypatch.delenv("PIPELINE_CLOUD_EXECUTORS", raising=False)
    from pipeline.cloud_defaults import resolve_parallelism

    s, e = resolve_parallelism(
        parallel_seeds=None, num_executors=None, seeds_explicit=False, executors_explicit=False
    )
    assert s == 2 and e == 2


def test_resolve_parallelism_cloud_env_override(monkeypatch):
    monkeypatch.setenv("PIPELINE_CLOUD", "1")
    monkeypatch.setenv("PIPELINE_CLOUD_PARALLEL_SEEDS", "3")
    monkeypatch.setenv("PIPELINE_CLOUD_EXECUTORS", "4")
    from pipeline.cloud_defaults import resolve_parallelism

    s, e = resolve_parallelism(
        parallel_seeds=None, num_executors=None, seeds_explicit=False, executors_explicit=False
    )
    assert s == 3 and e == 4


def test_resolve_parallelism_cli_wins(monkeypatch):
    monkeypatch.setenv("PIPELINE_CLOUD", "1")
    from pipeline.cloud_defaults import resolve_parallelism

    s, e = resolve_parallelism(
        parallel_seeds=1,
        num_executors=1,
        seeds_explicit=True,
        executors_explicit=True,
    )
    assert s == 1 and e == 1


def test_bus_wake_touch_and_wait(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.setenv("PIPELINE_BUS_WAKE", "1")
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.bus_wake import read_wake_token, touch_bus_wake, wait_for_bus_wake, wake_path

    (tmp_path / "state").mkdir(parents=True, exist_ok=True)
    touch_bus_wake()
    assert wake_path().is_file()
    tok0 = read_wake_token()
    assert tok0 >= 1
    mt0 = wake_path().stat().st_mtime
    t0 = time.time()
    mt1 = wait_for_bus_wake(last_mtime=mt0, last_token=tok0, timeout_s=0.15)
    assert time.time() - t0 < 1.0
    assert mt1 >= mt0


def test_bus_wake_disabled_sleeps(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.setenv("PIPELINE_BUS_WAKE", "0")
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline.bus_wake import bus_wake_enabled, wait_for_bus_wake

    assert bus_wake_enabled() is False
    t0 = time.time()
    wait_for_bus_wake(timeout_s=0.12)
    elapsed = time.time() - t0
    assert elapsed >= 0.08


def test_llm_metrics_record_and_summarize(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    from pipeline import llm_metrics

    llm_metrics.record_llm_call(
        duration_ms=100.0,
        wait_ms=20.0,
        provider="ollama",
        model="test",
        role="executor",
        slug="s1",
        kind="react",
        ok=True,
    )
    llm_metrics.record_llm_call(
        duration_ms=200.0,
        wait_ms=50.0,
        provider="ollama",
        model="test",
        role="validator",
        kind="direct",
        ok=True,
    )
    s = llm_metrics.summarize(last_n=10)
    assert s["count"] == 2
    assert s["duration_ms"]["p50"] > 0
    assert "executor" in s["by_role"]
    # wait stats present (react path is responsible for non-zero wait in prod)
    assert s["wait_ms"]["max"] >= 20.0


def test_sidecar_disabled_by_default(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("PIPELINE_GROK_SIDECAR", raising=False)
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    proj = tmp_path / "projects" / "demo"
    (proj / "state").mkdir(parents=True)
    (proj / "state" / "current_idea.json").write_text(
        json.dumps({"status": "phase_1_executing", "engine": "classic"}),
        encoding="utf-8",
    )
    from pipeline.grok_sidecar import maybe_run_sidecar_fix, sidecar_enabled

    assert sidecar_enabled() is False
    assert maybe_run_sidecar_fix("demo", 1, reason="test", retry_count=5) is None


def test_sidecar_respects_once_per_phase_and_keeps_engine(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.setenv("PIPELINE_GROK_SIDECAR", "1")
    monkeypatch.setenv("GROK_BUILD_DRY_RUN", "1")
    monkeypatch.setenv("GROK_BUILD_CMD", 'echo skill={skill} >> {log_file}')
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    proj = tmp_path / "projects" / "demo2"
    (proj / "state").mkdir(parents=True)
    (proj / "phases" / "phase_1").mkdir(parents=True)
    (proj / "workspace").mkdir(parents=True)
    state_path = proj / "state" / "current_idea.json"
    state_path.write_text(
        json.dumps({"status": "phase_1_executing", "engine": "classic"}),
        encoding="utf-8",
    )
    from pipeline.grok_sidecar import maybe_run_sidecar_fix

    r1 = maybe_run_sidecar_fix("demo2", 1, reason="stuck", retry_count=5, step="implement")
    assert r1 is not None
    st = json.loads(state_path.read_text(encoding="utf-8"))
    assert st.get("engine") == "classic"
    r2 = maybe_run_sidecar_fix("demo2", 1, reason="stuck again", retry_count=5)
    assert r2 is None  # once per phase


def test_project_lock_acquire_release(tmp_path: Path, monkeypatch):
    import os

    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.setenv("PIPELINE_PROJECT_LOCK", "1")
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    proj = tmp_path / "projects" / "locked"
    (proj / "state").mkdir(parents=True)
    from pipeline.project_lock import (
        try_acquire_project_lock,
        release_project_lock,
        lock_path_for,
    )

    holder_a = f"executor:{os.getpid()}"
    assert try_acquire_project_lock("locked", holder=holder_a) is True
    assert lock_path_for("locked").is_file()
    # Strict: no same-PID re-entry / second holder while held
    assert try_acquire_project_lock("locked", holder="other", timeout_s=0) is False
    assert try_acquire_project_lock("locked", holder=holder_a, timeout_s=0) is False
    release_project_lock("locked", holder=holder_a)
    assert not lock_path_for("locked").exists()
    assert try_acquire_project_lock("locked", holder="b") is True
    release_project_lock("locked", holder="b")
    assert not lock_path_for("locked").exists()


def test_project_lock_dead_pid_reclaim(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.setenv("PIPELINE_PROJECT_LOCK", "1")
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    proj = tmp_path / "projects" / "deadlock"
    (proj / "state").mkdir(parents=True)
    lock = proj / "state" / "project.lock"
    # Impossible PID on most systems
    lock.write_text("executor:99999999\n0\n99999999\n", encoding="utf-8")
    from pipeline.project_lock import is_lock_stale, try_acquire_project_lock, release_project_lock

    assert is_lock_stale(lock) is True
    assert try_acquire_project_lock("deadlock", holder="live") is True
    release_project_lock("deadlock", holder="live")


def test_zombie_lock_reaper_releases(tmp_path: Path, monkeypatch):
    """Timed-out handle finishing triggers reaper release of the lock file."""
    import os
    import threading
    import time

    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.setenv("PIPELINE_PROJECT_LOCK", "1")
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()
    proj = tmp_path / "projects" / "zom"
    (proj / "state").mkdir(parents=True)
    from pipeline.project_lock import (
        lock_path_for,
        register_zombie_lock,
        slug_has_zombie_lock,
        try_acquire_project_lock,
    )

    holder = f"executor:{os.getpid()}"
    assert try_acquire_project_lock("zom", holder=holder) is True
    assert lock_path_for("zom").is_file()

    done = threading.Event()

    def slow():
        time.sleep(0.15)
        done.set()

    t = threading.Thread(target=slow, daemon=True)
    t.start()
    register_zombie_lock("zom", t, holder=holder, hard_timeout_s=5.0)
    assert slug_has_zombie_lock("zom") is True
    # Cannot re-acquire while zombie active
    assert try_acquire_project_lock("zom", holder="other", timeout_s=0) is False
    t.join(timeout=2.0)
    # Wait for reaper to release
    deadline = time.time() + 2.0
    while time.time() < deadline and lock_path_for("zom").exists():
        time.sleep(0.05)
    assert not lock_path_for("zom").exists()
    assert slug_has_zombie_lock("zom") is False
    assert try_acquire_project_lock("zom", holder="next") is True
