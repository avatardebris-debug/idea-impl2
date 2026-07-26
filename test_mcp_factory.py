"""Tests for MCP factory queue (T3) — file-based mcp_factory_job.v1 jobs."""

from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _reload_pipeline(monkeypatch: pytest.MonkeyPatch, pipeline: pathlib.Path) -> None:
    monkeypatch.setenv("PIPELINE_DIR", str(pipeline))
    monkeypatch.delenv("PIPELINE_CLOUD", raising=False)
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()


def test_enqueue_creates_pending_with_schema(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_queue import SCHEMA, enqueue_wrap, load_job, queue_dir
    from pipeline.paths import get_pipeline_dir

    assert get_pipeline_dir() == pipeline.resolve()

    path = enqueue_wrap(
        "foo_cli",
        goal_id="g_test",
        reason="missing mcp node",
    )
    assert path.is_file()
    assert path.parent == queue_dir() / "pending"
    assert path.name.startswith("mcpjob_")
    assert path.suffix == ".json"

    job = load_job(path)
    assert job["schema"] == SCHEMA
    assert job["schema"] == "mcp_factory_job.v1"
    assert job["job_id"] == path.stem
    assert job["capability_slug"] == "foo_cli"
    assert job["goal_id"] == "g_test"
    assert job["reason"] == "missing mcp node"
    assert job["status"] == "pending"
    assert job.get("created_at")


def test_mark_done_moves_to_done(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_queue import enqueue_wrap, list_pending, load_job, mark_done, queue_dir

    pending_path = enqueue_wrap("bar_tool", reason="wrap")
    assert pending_path.is_file()
    assert len(list_pending()) == 1

    done_path = mark_done(pending_path, {"ok": True, "mcp_slug": "mcp_bar_tool"})
    assert done_path.is_file()
    assert done_path.parent == queue_dir() / "done"
    assert done_path.name == pending_path.name
    assert not pending_path.is_file()
    assert list_pending() == []

    job = load_job(done_path)
    assert job["status"] == "done"
    assert job["result"]["ok"] is True
    assert job["result"]["mcp_slug"] == "mcp_bar_tool"
    assert job.get("finished_at")

    # failed status from result
    p2 = enqueue_wrap("baz_tool")
    done_fail = mark_done(p2, {"ok": False, "error": "smoke failed"})
    assert load_job(done_fail)["status"] == "failed"


def test_list_pending_returns_new_job(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_queue import enqueue_wrap, list_pending, queue_dir

    assert list_pending() == []
    # ensures dirs exist even when empty
    assert (queue_dir() / "pending").is_dir()
    assert (queue_dir() / "done").is_dir()

    p1 = enqueue_wrap("cap_a")
    p2 = enqueue_wrap("cap_b")
    pending = list_pending()
    assert p1 in pending
    assert p2 in pending
    assert pending == sorted(pending)
    assert all(p.suffix == ".json" for p in pending)
    assert all(json.loads(p.read_text(encoding="utf-8"))["status"] == "pending" for p in pending)
