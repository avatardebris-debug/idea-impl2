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


# --- Phase 1 / v1: re-smoke, revoke, invoke oracle, provenance ---


def test_manifest_provenance_fields(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import SCHEMA, WRAP_VERSION, resmoke_mcp, wrap_capability_as_mcp
    from pipeline.paths import mcps_dir

    man = wrap_capability_as_mcp("prov_cap", force=True)
    assert man["schema"] == SCHEMA
    assert man["capability_slug"] == "prov_cap"
    assert man["wraps_capability"] == "prov_cap"
    assert man["wrap_version"] == WRAP_VERSION
    assert man.get("content_sha256")
    assert len(man["content_sha256"]) == 64
    assert man["status"] == "draft"
    assert "last_smoke_at" not in man or man.get("last_smoke_at") is None

    r = resmoke_mcp("mcp_prov_cap", require_invoke=False)
    assert r["ok"] is True, r
    man2 = json.loads(
        (mcps_dir() / "mcp_prov_cap" / "manifest.json").read_text(encoding="utf-8")
    )
    assert man2["status"] == "smoked"
    assert man2.get("last_smoke_at")
    assert man2.get("last_smoke_ok") is True
    assert man2.get("smoked_at")
    assert man2["content_sha256"] == man["content_sha256"]
    assert man2["wrap_version"] == WRAP_VERSION
    assert man2["capability_slug"] == "prov_cap"


def test_resmoke_pass_and_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import (
        is_mcp_smoked,
        resmoke_mcp,
        smoke_mcp,
        wrap_capability_as_mcp,
    )
    from pipeline.paths import mcps_dir

    wrap_capability_as_mcp("rs_cap", force=True)
    r1 = smoke_mcp("mcp_rs_cap", require_invoke=False)
    assert r1["ok"] is True
    man1 = json.loads(
        (mcps_dir() / "mcp_rs_cap" / "manifest.json").read_text(encoding="utf-8")
    )
    first_ts = man1["last_smoke_at"]

    r2 = resmoke_mcp("mcp_rs_cap", require_invoke=False)
    assert r2["ok"] is True, r2
    assert not r2.get("skipped")
    man2 = json.loads(
        (mcps_dir() / "mcp_rs_cap" / "manifest.json").read_text(encoding="utf-8")
    )
    assert man2["last_smoke_at"] >= first_ts
    assert is_mcp_smoked("mcp_rs_cap")

    # Fail path: remove server
    (mcps_dir() / "mcp_rs_cap" / "server.py").unlink()
    r3 = resmoke_mcp("mcp_rs_cap", require_invoke=False)
    assert r3["ok"] is False
    assert "missing" in (r3.get("error") or "").lower() or "server" in (
        r3.get("error") or ""
    ).lower()
    smoke_disk = json.loads(
        (mcps_dir() / "mcp_rs_cap" / "smoke_report.json").read_text(encoding="utf-8")
    )
    assert smoke_disk["ok"] is False
    man3 = json.loads(
        (mcps_dir() / "mcp_rs_cap" / "manifest.json").read_text(encoding="utf-8")
    )
    assert man3.get("last_smoke_ok") is False
    assert man3.get("last_smoke_at")


def test_revoke_not_smoked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import (
        is_mcp_revoked,
        is_mcp_smoked,
        list_mcps,
        resmoke_mcp,
        revoke_mcp,
        smoke_mcp,
        wrap_capability_as_mcp,
    )

    wrap_capability_as_mcp("rev_cap", force=True)
    assert smoke_mcp("mcp_rev_cap", require_invoke=False)["ok"] is True
    assert is_mcp_smoked("mcp_rev_cap")

    result = revoke_mcp("mcp_rev_cap", reason="test revoke")
    assert result["ok"] is True
    assert result["status"] == "revoked"
    assert is_mcp_revoked("mcp_rev_cap")
    assert not is_mcp_smoked("mcp_rev_cap")
    assert result.get("is_mcp_smoked") is False

    rows = list_mcps()
    rev_row = next(r for r in rows if r.get("mcp_slug") == "mcp_rev_cap")
    assert rev_row["status"] == "revoked"
    assert rev_row.get("revoke_reason") == "test revoke"

    # re-smoke refuses revoked
    r = resmoke_mcp("mcp_rev_cap", require_invoke=False)
    assert r["ok"] is False
    assert "revok" in (r.get("error") or "").lower()


def test_invoke_oracle_success_and_failure_reports(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """require_invoke writes invoke_report.json for pass and fail (no overnight)."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import (
        load_invoke_report,
        smoke_mcp,
        wrap_capability_as_mcp,
    )
    from pipeline.paths import mcps_dir

    # Failure: no registry / no project → invoke ERROR with require_invoke
    wrap_capability_as_mcp("no_inv_cap", force=True)
    fail_rep = smoke_mcp(
        "mcp_no_inv_cap",
        require_invoke=True,
        invoke_args="--help",
        timeout_s=20.0,
    )
    assert fail_rep["ok"] is False, fail_rep
    inv_path = mcps_dir() / "mcp_no_inv_cap" / "invoke_report.json"
    assert inv_path.is_file()
    inv_fail = load_invoke_report("mcp_no_inv_cap")
    assert inv_fail is not None
    assert inv_fail["ok"] is False
    assert inv_fail["schema"] == "mcp_invoke_report.v1"
    assert inv_fail.get("require_invoke") is True

    # Success: mini CLI under projects/ + registry
    ws = pipeline / "projects" / "ok_inv_cap" / "workspace"
    ws.mkdir(parents=True)
    (ws / "cli.py").write_text(
        "import sys\nprint('usage: ok_inv_cap --help')\nsys.exit(0)\n",
        encoding="utf-8",
    )
    from pipeline.capability_registry import _connect, _now

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
            "ok_inv_cap",
            "Ok Inv",
            "project",
            "verified",
            "test",
            "[]",
            "python cli.py",
            "",
            "projects/ok_inv_cap/workspace",
            "[]",
            "python cli.py --help",
            "ok_inv_cap",
            1,
            1,
            _now(),
        ),
    )
    conn.commit()
    conn.close()

    wrap_capability_as_mcp("ok_inv_cap", force=True)
    ok_rep = smoke_mcp(
        "mcp_ok_inv_cap",
        require_invoke=True,
        invoke_args="--help",
        timeout_s=20.0,
    )
    assert ok_rep["ok"] is True, ok_rep
    inv_ok = load_invoke_report("mcp_ok_inv_cap")
    assert inv_ok is not None
    assert inv_ok["ok"] is True
    assert (mcps_dir() / "mcp_ok_inv_cap" / "invoke_report.json").is_file()
    methods = {c["method"]: c for c in ok_rep["checks"]}
    assert methods["invoke"]["ok"] is True


def test_cli_lists_resmoke_and_revoke(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from scripts.mcp_factory import main

    # --help must list re-smoke and revoke (Task 1 Done-when)
    with pytest.raises(SystemExit) as ei:
        main(["--help"])
    assert ei.value.code in (0, None)
    help_text = capsys.readouterr().out + capsys.readouterr().err
    assert "re-smoke" in help_text
    assert "revoke" in help_text

    # Functional CLI path: wrap → re-smoke → revoke
    assert main(["wrap", "--slug", "cli_v1_cap", "--force"]) == 0
    assert main(
        ["re-smoke", "--mcp-slug", "mcp_cli_v1_cap", "--no-require-invoke"]
    ) == 0
    assert main(["revoke", "--mcp-slug", "mcp_cli_v1_cap", "--reason", "cli"]) == 0


def test_unsafe_mcp_slug_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import (
        mcp_dir,
        mcp_slug_for,
        revoke_mcp,
        smoke_mcp,
        wrap_capability_as_mcp,
    )

    for bad in ("../x", "a/b", r"a\b", "mcp_../escape", "c:foo"):
        with pytest.raises(ValueError):
            mcp_slug_for(bad)
        with pytest.raises(ValueError):
            mcp_dir(bad)
        with pytest.raises(ValueError):
            wrap_capability_as_mcp(bad, force=True)
        with pytest.raises(ValueError):
            smoke_mcp(bad, require_invoke=False)
        with pytest.raises(ValueError):
            revoke_mcp(bad)


def test_force_wrap_clears_oracle_reports(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import smoke_mcp, wrap_capability_as_mcp
    from pipeline.paths import mcps_dir

    wrap_capability_as_mcp("force_clear", force=True)
    # Plant durable reports without full hard invoke path
    d = mcps_dir() / "mcp_force_clear"
    (d / "smoke_report.json").write_text(
        json.dumps({"ok": True, "ts": "2026-01-01T00:00:00+00:00"}) + "\n",
        encoding="utf-8",
    )
    (d / "invoke_report.json").write_text(
        json.dumps(
            {
                "schema": "mcp_invoke_report.v1",
                "ok": True,
                "mcp_slug": "mcp_force_clear",
                "ts": "2026-01-01T00:00:00+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    wrap_capability_as_mcp("force_clear", force=True)
    assert not (d / "invoke_report.json").is_file()
    assert not (d / "smoke_report.json").is_file()
    # Soft smoke without prior invoke evidence → presence path, no invoke_report
    r = smoke_mcp("mcp_force_clear", require_invoke=False)
    assert r["ok"] is True
    # Soft smoke with failed invoke clears any leftover (none here)
    assert not (d / "invoke_report.json").is_file() or r.get("invoke_report", {}).get(
        "ok"
    )


def test_soft_smoke_clears_stale_invoke_report(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Soft smoke with failed invoke deletes prior ok invoke_report."""
    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import load_invoke_report, smoke_mcp, wrap_capability_as_mcp
    from pipeline.paths import mcps_dir

    wrap_capability_as_mcp("stale_inv", force=True)
    d = mcps_dir() / "mcp_stale_inv"
    (d / "invoke_report.json").write_text(
        json.dumps(
            {
                "schema": "mcp_invoke_report.v1",
                "ok": True,
                "mcp_slug": "mcp_stale_inv",
                "ts": "2020-01-01T00:00:00+00:00",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    # Soft smoke: no registry → invoke fails, overall soft ok; must clear stale
    r = smoke_mcp("mcp_stale_inv", require_invoke=False)
    assert r["ok"] is True, r
    assert load_invoke_report("mcp_stale_inv") is None
    assert r.get("invoke_report_cleared") == "soft_smoke_invoke_failed"


def test_rpc_timeout_enforced(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Hung server readline must surface TimeoutError within budget (not hang)."""
    import subprocess
    import sys
    import time

    pipeline = tmp_path / "out"
    pipeline.mkdir(parents=True)
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.mcp_factory import _rpc_line

    # Child that never writes a response line
    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    t0 = time.monotonic()
    try:
        with pytest.raises(TimeoutError):
            _rpc_line(proc, {"method": "ping", "params": {}}, timeout_s=0.3)
    finally:
        try:
            proc.kill()
            proc.wait(timeout=3)
        except Exception:
            pass
    elapsed = time.monotonic() - t0
    assert elapsed < 5.0, f"timeout not enforced (took {elapsed}s)"
