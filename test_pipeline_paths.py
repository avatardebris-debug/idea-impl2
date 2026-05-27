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
