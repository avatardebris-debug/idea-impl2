"""Smoke tests for live pipeline path resolution."""

from __future__ import annotations

import os
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_projects_dir_resolves_under_pipeline_root(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    pipeline = tmp_path / "out"
    (pipeline / "projects").mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir
    from pipeline.paths import get_pipeline_dir, projects_dir

    reload_pipeline_dir()
    root = get_pipeline_dir()
    assert root == pipeline.resolve()
    assert projects_dir() == pipeline.resolve() / "projects"
    assert projects_dir().name == "projects"


def test_paths_helpers_follow_pipeline_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    pipeline = tmp_path / "thepipeline"
    for sub in ("projects", "state", "goals", "logs", "finetune_corpus", "memory"):
        (pipeline / sub).mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir
    from pipeline.paths import (
        finetune_corpus_dir,
        goals_dir,
        logs_dir,
        memory_dir,
        state_dir,
    )

    reload_pipeline_dir()
    assert state_dir() == pipeline.resolve() / "state"
    assert goals_dir() == pipeline.resolve() / "goals"
    assert logs_dir() == pipeline.resolve() / "logs"
    assert memory_dir() == pipeline.resolve() / "memory"
    assert finetune_corpus_dir() == pipeline.resolve() / "finetune_corpus"


def test_registry_db_updates_after_reload(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    pipeline_a = tmp_path / "a"
    (pipeline_a / "state").mkdir(parents=True)
    pipeline_b = tmp_path / "b"
    (pipeline_b / "state").mkdir(parents=True)

    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir
    from pipeline.paths import registry_db

    monkeypatch.setenv("PIPELINE_DIR", str(pipeline_a))
    reload_pipeline_dir()
    assert registry_db() == pipeline_a.resolve() / "state" / "capability_registry.sqlite"

    monkeypatch.setenv("PIPELINE_DIR", str(pipeline_b))
    reload_pipeline_dir()
    assert registry_db() == pipeline_b.resolve() / "state" / "capability_registry.sqlite"


def test_capability_graph_connects_to_live_registry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path,
) -> None:
    pipeline = tmp_path / "out"
    (pipeline / "state").mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir
    from pipeline.paths import registry_db

    reload_pipeline_dir()
    db = registry_db()
    db.parent.mkdir(parents=True, exist_ok=True)
    db.write_bytes(b"")

    from pipeline.capability_graph import _connect

    conn = _connect()
    try:
        assert pathlib.Path(conn.execute("PRAGMA database_list").fetchone()[2]) == db
    finally:
        conn.close()


def test_state_path_helpers(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    pipeline = tmp_path / "out"
    (pipeline / "state").mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir
    from pipeline.paths import (
        activity_jsonl,
        completions_jsonl,
        message_bus_db,
        pipeline_status_json,
        project_state_file,
        throughput_json,
    )

    reload_pipeline_dir()
    assert message_bus_db() == pipeline.resolve() / "state" / "message_bus.db"
    assert throughput_json() == pipeline.resolve() / "state" / "throughput.json"
    assert pipeline_status_json() == pipeline.resolve() / "state" / "pipeline_status.json"
    assert completions_jsonl() == pipeline.resolve() / "state" / "completions.jsonl"
    assert activity_jsonl() == pipeline.resolve() / "state" / "activity.jsonl"
    assert project_state_file("foo") == pipeline.resolve() / "projects" / "foo" / "state" / "current_idea.json"
