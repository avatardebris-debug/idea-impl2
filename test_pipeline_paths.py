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


def test_agent_modules_importable() -> None:
    """Regression: executor/reviewer must not import removed agent_process helpers."""
    from pipeline.agents.executor import ExecutorAgent
    from pipeline.agents.reviewer import ReviewerAgent
    from pipeline.agents.validator import ValidatorAgent
    from pipeline.agents.manager import ManagerAgent
    from pipeline.agents.ideator import IdeatorAgent
    from pipeline.agents.phase_planner import PhasePlannerAgent
    from pipeline.agents.idea_planner import IdeaPlannerAgent

    assert ExecutorAgent.role == "executor"
    assert ReviewerAgent.role == "reviewer"
    assert ValidatorAgent.role == "validator"


def test_resolve_capability_workdir_under_pipeline_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path,
) -> None:
    """Legacy .pipeline/projects/... cwd_template must resolve under PIPELINE_DIR."""
    pipeline = tmp_path / "thepipeline"
    ws = pipeline / "projects" / "demo_tool" / "workspace"
    ws.mkdir(parents=True)
    (ws / "cli.py").write_text("print('ok')\n", encoding="utf-8")
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import PROJECT_ROOT, reload_pipeline_dir
    from pipeline.capability_tools import (
        _is_allowed_workdir,
        resolve_capability_workdir,
        rewrite_capability_entrypoint,
    )

    reload_pipeline_dir()

    # Prefer known slug workspace under pipeline even when template points at factory layout
    work = resolve_capability_workdir(
        slug="demo_tool",
        source_project="demo_tool",
        cwd_template=".pipeline/projects/demo_tool/workspace",
        kind="project",
    )
    assert work == ws.resolve()
    assert _is_allowed_workdir(work)

    # Template alone (no slug) rewrites .pipeline/projects → PIPELINE_DIR/projects
    work2 = resolve_capability_workdir(
        cwd_template=".pipeline/projects/demo_tool/workspace",
    )
    assert work2 == ws.resolve()

    # projects/... relative template
    work3 = resolve_capability_workdir(
        cwd_template="projects/demo_tool/workspace",
    )
    assert work3 == ws.resolve()

    # Entrypoint rewrite from factory-style path
    entry = rewrite_capability_entrypoint(
        "python .pipeline/projects/demo_tool/workspace/cli.py",
        work_dir=work,
    )
    assert str(ws).replace("\\", "/") in entry.replace("\\", "/") or "demo_tool" in entry
    assert ".pipeline/projects" not in entry.replace("\\", "/")

    # Explicit override relative to pipeline
    work4 = resolve_capability_workdir(
        slug="demo_tool",
        cwd_override="projects/demo_tool/workspace",
    )
    assert work4 == ws.resolve()

    # Factory PROJECT_ROOT alone must NOT be the only allowed root
    assert work != (PROJECT_ROOT / ".pipeline" / "projects" / "demo_tool" / "workspace")

    # shared_lib: honor absolute shared_libs cwd even when source_project workspace exists
    shared = pipeline / "shared_libs" / "util"
    shared.mkdir(parents=True)
    work_shared = resolve_capability_workdir(
        slug="shared_util",
        source_project="demo_tool",
        cwd_template=str(shared),
        kind="shared_lib",
    )
    assert work_shared == shared.resolve()

    # workspace-relative entrypoint unchanged
    assert rewrite_capability_entrypoint("python cli.py", work_dir=work) == "python cli.py"

    # absolute under PIPELINE_DIR not mangled
    abs_cli = (ws / "cli.py").resolve()
    entry_abs = rewrite_capability_entrypoint(f"python {abs_cli}", work_dir=work)
    assert str(abs_cli) in entry_abs or abs_cli.as_posix() in entry_abs.replace("\\", "/")

    # unrelated .../projects/... absolute path not rewritten into PIPELINE_DIR
    foreign = (tmp_path / "code" / "projects" / "other" / "cli.py").resolve()
    foreign.parent.mkdir(parents=True)
    foreign.write_text("x\n", encoding="utf-8")
    entry_foreign = rewrite_capability_entrypoint(f"python {foreign}")
    assert str(pipeline.resolve()) not in entry_foreign
    assert str(foreign) in entry_foreign or foreign.as_posix() in entry_foreign.replace("\\", "/")

    # disallowed absolute cwd
    outside = tmp_path / "outside_root"
    outside.mkdir()
    assert not _is_allowed_workdir(outside)


def test_resolve_pipeline_dir_prefers_home_factory_when_nested_empty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path,
) -> None:
    """When nested .pipeline has few projects but home factory has many, prefer home."""
    from pipeline import pipeline_config
    from pipeline.pipeline_config import resolve_pipeline_dir

    # Explicit env always wins
    out = tmp_path / "explicit"
    (out / "projects").mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(out))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)
    assert resolve_pipeline_dir() == out.resolve()

    # Controlled factory root: no real sibling thepipeline interference
    fake_root = tmp_path / "factory_repo"
    fake_root.mkdir()
    nested = fake_root / ".pipeline"
    (nested / "projects" / "lonely").mkdir(parents=True)  # nested_n = 1

    fake_home = tmp_path / "home"
    home_factory = fake_home / "aicompete" / "thepipeline"
    for name in ("a", "b", "c"):
        (home_factory / "projects" / name).mkdir(parents=True)  # home_n = 3

    monkeypatch.setattr(pipeline_config, "PROJECT_ROOT", fake_root.resolve())
    monkeypatch.setattr(
        pipeline_config.pathlib.Path,
        "home",
        lambda *a, **k: fake_home,
    )

    # Cloud mode forces nested .pipeline under (patched) PROJECT_ROOT
    monkeypatch.delenv("PIPELINE_DIR", raising=False)
    monkeypatch.setenv("PIPELINE_CLOUD", "1")
    assert resolve_pipeline_dir() == nested.resolve()

    # Home-factory preference when nested is empty-ish and cloud off
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)
    assert resolve_pipeline_dir() == home_factory.resolve()

    # Sibling thepipeline with projects still wins over home
    sibling = fake_root.parent / "thepipeline"
    (sibling / "projects" / "sib").mkdir(parents=True)
    assert resolve_pipeline_dir() == sibling.resolve()
