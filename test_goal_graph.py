"""Tests for goal graph store paths (and later graph.v1)."""

from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_graphs_and_mcps_dirs(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)

    from pipeline.pipeline_config import reload_pipeline_dir
    from pipeline.paths import get_pipeline_dir, graphs_dir, mcps_dir

    reload_pipeline_dir()
    root = get_pipeline_dir()
    assert root == pipeline.resolve()
    assert graphs_dir() == root / "graphs"
    assert mcps_dir() == root / "mcps"
    assert graphs_dir().name == "graphs"
    assert mcps_dir().name == "mcps"
