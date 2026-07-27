"""Tests for MCP factory queue (T3) + factory wrap/smoke (T4)."""

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
    monkeypatch.setenv("KEEP_GOAL_TRACES", "1")
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


# --- T4: wrap + smoke + list + drain ---


def test_scaffold_and_smoke(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Scaffold server alone is enough for ping+describe smoke (no registry needed)."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import (
        SCHEMA,
        list_mcps,
        mcp_dir,
        smoke_mcp,
        wrap_capability_as_mcp,
    )
    from pipeline.paths import mcps_dir

    manifest = wrap_capability_as_mcp(
        "tiny_ping_cap",
        entrypoint="python cli.py",  # test override recorded only
        force=True,
    )
    assert manifest["schema"] == SCHEMA
    assert manifest["schema"] == "mcp_manifest.v1"
    assert manifest["mcp_slug"] == "mcp_tiny_ping_cap"
    assert manifest["wraps_capability"] == "tiny_ping_cap"
    assert manifest["transport"] == "stdio_jsonl"
    assert "ping" in manifest["tools"]
    assert "describe" in manifest["tools"]
    assert "invoke" in manifest["tools"]
    assert manifest["entrypoint_override"] == "python cli.py"
    assert manifest["status"] in ("draft", "smoked")

    d = mcp_dir("mcp_tiny_ping_cap")
    assert d == mcps_dir() / "mcp_tiny_ping_cap"
    assert (d / "server.py").is_file()
    assert (d / "manifest.json").is_file()
    server_src = (d / "server.py").read_text(encoding="utf-8")
    assert "WRAPS_CAPABILITY" in server_src
    assert "tiny_ping_cap" in server_src
    assert '"ping"' in server_src or "method == \"ping\"" in server_src

    report = smoke_mcp("mcp_tiny_ping_cap", timeout_s=20.0)
    assert report["ok"] is True, report
    assert report["mcp_slug"] == "mcp_tiny_ping_cap"
    methods = {c["method"]: c for c in report["checks"]}
    assert methods["ping"]["ok"] is True
    assert methods["describe"]["ok"] is True
    assert (d / "smoke_report.json").is_file()
    smoke_disk = json.loads((d / "smoke_report.json").read_text(encoding="utf-8"))
    assert smoke_disk["ok"] is True

    # manifest bumped to smoked
    man2 = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    assert man2["status"] == "smoked"

    rows = list_mcps()
    assert any(r.get("mcp_slug") == "mcp_tiny_ping_cap" for r in rows)


def test_wrap_idempotent_without_force(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import wrap_capability_as_mcp

    m1 = wrap_capability_as_mcp("idem_cap", force=True)
    created = m1["created_at"]
    m2 = wrap_capability_as_mcp("idem_cap", force=False)
    assert m2["mcp_slug"] == "mcp_idem_cap"
    assert m2["created_at"] == created


def test_drain_queue_wraps_and_marks_done(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import drain_queue, list_mcps
    from pipeline.mcp_queue import enqueue_wrap, list_pending, load_job, queue_dir

    enqueue_wrap("drain_cap_a", reason="test drain")
    assert len(list_pending()) == 1

    results = drain_queue(limit=1, require_invoke=False)
    assert len(results) == 1
    assert results[0]["ok"] is True, results[0]
    assert results[0]["mcp_slug"] == "mcp_drain_cap_a"
    assert list_pending() == []
    done = list((queue_dir() / "done").glob("*.json"))
    assert len(done) == 1
    job = load_job(done[0])
    assert job["status"] == "done"
    assert any(r.get("mcp_slug") == "mcp_drain_cap_a" for r in list_mcps())


def test_register_mcp_best_effort(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import register_mcp, wrap_capability_as_mcp

    man = wrap_capability_as_mcp("reg_cap", force=True)
    # Should not raise even with empty/new registry
    register_mcp(man)
    man2 = json.loads(
        (tmp_path / "out" / "mcps" / "mcp_reg_cap" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert "registry_note" in man2
    # Prefer success when registry helpers work
    assert man2["registry_note"].startswith("registry_")


def test_skip_if_smoked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import is_mcp_smoked, smoke_mcp, wrap_capability_as_mcp

    wrap_capability_as_mcp("skip_cap", force=True)
    r1 = smoke_mcp("mcp_skip_cap", require_invoke=False)
    assert r1["ok"] is True
    assert is_mcp_smoked("mcp_skip_cap")
    r2 = smoke_mcp("mcp_skip_cap", skip_if_smoked=True, require_invoke=False)
    assert r2["ok"] is True
    assert r2.get("skipped") is True
    assert r2.get("skip_reason") == "already_smoked"


def test_invoke_oracle_with_real_mini_cli(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """require_invoke=True needs live capability under PIPELINE_DIR (subprocess server)."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    # Mini project + registry row so invoke_capability works inside MCP server process
    ws = pipeline / "projects" / "inv_cap" / "workspace"
    ws.mkdir(parents=True)
    (ws / "cli.py").write_text(
        "import sys\nprint('usage: inv_cap --help')\nsys.exit(0)\n",
        encoding="utf-8",
    )
    from pipeline.capability_registry import _connect, _now
    from pipeline.paths import registry_db

    conn = _connect()
    conn.execute(
        """
        INSERT INTO capabilities
        (slug, title, kind, status, purpose, domains, entrypoint, import_path,
         cwd_template, requires, example_invoke, source_project, phase, total_phases, updated_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(slug) DO UPDATE SET
            status=excluded.status,
            entrypoint=excluded.entrypoint,
            cwd_template=excluded.cwd_template,
            updated_at=excluded.updated_at
        """,
        (
            "inv_cap",
            "Inv Cap",
            "project",
            "verified",
            "test",
            "[]",
            "python cli.py",
            "",
            "projects/inv_cap/workspace",
            "[]",
            "python cli.py --help",
            "inv_cap",
            1,
            1,
            _now(),
        ),
    )
    conn.commit()
    conn.close()
    assert registry_db().is_file()

    from pipeline.mcp_factory import smoke_mcp, wrap_capability_as_mcp

    wrap_capability_as_mcp("inv_cap", force=True)
    report = smoke_mcp(
        "mcp_inv_cap",
        require_invoke=True,
        invoke_args="--help",
        timeout_s=20.0,
    )
    assert report["ok"] is True, report
    methods = {c["method"]: c for c in report["checks"]}
    assert methods["ping"]["ok"] is True
    assert methods["describe"]["ok"] is True
    assert methods["invoke"]["ok"] is True


def test_drain_skips_already_smoked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import drain_queue, smoke_mcp, wrap_capability_as_mcp
    from pipeline.mcp_queue import enqueue_wrap, list_pending

    wrap_capability_as_mcp("pre_smoked", force=True)
    assert smoke_mcp("mcp_pre_smoked", require_invoke=False)["ok"] is True
    enqueue_wrap("pre_smoked", reason="already done")
    assert len(list_pending()) == 1
    results = drain_queue(limit=1, skip_if_smoked=True, require_invoke=False)
    assert len(results) == 1
    assert results[0]["ok"] is True
    assert results[0].get("skipped") is True
    assert list_pending() == []
