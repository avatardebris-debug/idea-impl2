"""external_ingest v1 — pin, static scan, human gate, promote + external trust clamp."""

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
    monkeypatch.setenv("EXTERNAL_INGEST_ACTOR", "test-operator")
    from pipeline.pipeline_config import reload_pipeline_dir

    reload_pipeline_dir()


def _write_skill_fixture(root: pathlib.Path, name: str = "fake-skill") -> pathlib.Path:
    sk = root / name
    sk.mkdir(parents=True, exist_ok=True)
    (sk / "SKILL.md").write_text(
        f"---\nname: {name}\n---\n\n# {name}\n\nSafe skill body for ingest tests.\n",
        encoding="utf-8",
    )
    (sk / "LICENSE").write_text("MIT License\n\nCopyright (c) test\n", encoding="utf-8")
    return sk


def _write_software_fixture(root: pathlib.Path, name: str = "fake-tool") -> pathlib.Path:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "main.py").write_text("def main():\n    print('ok')\n", encoding="utf-8")
    (d / "pyproject.toml").write_text("[project]\nname = 'fake-tool'\n", encoding="utf-8")
    return d


def _write_mcp_fixture(root: pathlib.Path, name: str = "fake-mcp") -> pathlib.Path:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "server.py").write_text("# stub mcp server\n", encoding="utf-8")
    (d / "manifest.json").write_text('{"name": "fake-mcp"}\n', encoding="utf-8")
    return d


def test_pin_creates_quarantine_and_stable_hash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    fixture = _write_skill_fixture(tmp_path / "fixtures")
    from pipeline.external_ingest import (
        SCHEMA,
        content_sha256_tree,
        get_asset,
        pin_asset,
    )
    from pipeline.paths import external_dir, get_pipeline_dir

    assert get_pipeline_dir() == pipeline.resolve()
    rec = pin_asset(fixture, kind="skill", asset_id="skill_fake-skill")
    assert rec["schema"] == SCHEMA
    assert rec["id"] == "skill_fake-skill"
    assert rec["kind"] == "skill"
    assert rec["status"] == "quarantined"
    assert rec["pin"]["content_sha256"]
    assert (pipeline / "external" / "assets" / "skill_fake-skill" / "asset.json").is_file()
    payload = pipeline / "external" / "assets" / "skill_fake-skill" / "payload"
    assert (payload / "SKILL.md").is_file()
    # Hash stable across recompute
    h1 = rec["pin"]["content_sha256"]
    h2 = content_sha256_tree(payload)
    assert h1 == h2
    # external_dir helper
    assert external_dir() == pipeline.resolve() / "external"
    loaded = get_asset("skill_fake-skill")
    assert loaded is not None
    assert loaded["status"] == "quarantined"

    # Re-pin without force rejected
    with pytest.raises(FileExistsError):
        pin_asset(fixture, kind="skill", asset_id="skill_fake-skill")

    # Force re-pin ok; hash still stable for same content
    rec2 = pin_asset(fixture, kind="skill", asset_id="skill_fake-skill", force=True)
    assert rec2["pin"]["content_sha256"] == h1


def test_scan_pass_and_secret_fail(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    clean = _write_skill_fixture(tmp_path / "fixtures", "clean-skill")
    leaky_root = tmp_path / "fixtures" / "leaky-skill"
    leaky_root.mkdir(parents=True)
    (leaky_root / "SKILL.md").write_text(
        "# Leaky\n\napi_key: sk-abcdefghijklmnopqrstuvwxyz0123456789\n",
        encoding="utf-8",
    )

    from pipeline.external_ingest import pin_asset, scan_asset

    clean_rec = pin_asset(clean, kind="skill", asset_id="skill_clean")
    out = scan_asset(clean_rec["id"])
    assert out["status"] == "scanned"
    assert out["scan_report"]["pass"] is True
    assert out["license_note"]  # LICENSE discovered
    report_path = (
        pipeline / "external" / "assets" / "skill_clean" / "scan_report.json"
    )
    assert report_path.is_file()
    disk_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert disk_report["pass"] is True

    leaky = pin_asset(leaky_root, kind="skill", asset_id="skill_leaky")
    out2 = scan_asset(leaky["id"])
    assert out2["status"] == "rejected"
    assert out2["scan_report"]["pass"] is False
    names = {c["name"] for c in out2["scan_report"]["checks"] if not c["pass"]}
    assert "no_secrets" in names


def test_scan_disallowed_ext(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.external_ingest import pin_asset, scan_asset

    # Disallowed extension
    bad = tmp_path / "fixtures" / "bad-bin"
    bad.mkdir(parents=True)
    (bad / "tool.exe").write_bytes(b"MZ\x00\x00fake")
    (bad / "readme.txt").write_text("hi", encoding="utf-8")
    rec = pin_asset(bad, kind="software", asset_id="software_bad-bin")
    out = scan_asset(rec["id"])
    assert out["scan_report"]["pass"] is False
    names = {c["name"] for c in out["scan_report"]["checks"] if not c["pass"]}
    assert "disallowed_extensions" in names
    assert out["status"] == "rejected"


def test_scan_path_escape_reject(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Deterministic path_escape fail without OS symlinks (Windows-safe).

    Injects a file path outside the payload so relative_to(payload) fails and
    scan reports named check path_escape.
    """
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    fixture = _write_skill_fixture(tmp_path / "fixtures", "escape-skill")
    from pipeline.external_ingest import pin_asset, scan_asset

    rec = pin_asset(fixture, kind="skill", asset_id="skill_escape")
    outside = tmp_path / "outside_payload.txt"
    outside.write_text("not in quarantine\n", encoding="utf-8")

    def _fake_iter(_payload: pathlib.Path) -> list[pathlib.Path]:
        # File not under payload → relative_to raises → path_escape
        return [outside]

    monkeypatch.setattr(
        "pipeline.external_ingest._iter_payload_files", _fake_iter
    )
    out = scan_asset(rec["id"])
    assert out["scan_report"]["pass"] is False
    names = {c["name"] for c in out["scan_report"]["checks"] if not c["pass"]}
    assert "path_escape" in names
    assert out["status"] == "rejected"
    detail = next(
        c["detail"]
        for c in out["scan_report"]["checks"]
        if c["name"] == "path_escape"
    )
    assert detail and detail != "ok"


def test_approve_promote_path_and_block_without_approve(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    fixture = _write_skill_fixture(tmp_path / "fixtures")
    from pipeline.external_ingest import (
        approve_asset,
        pin_asset,
        promote_asset,
        scan_asset,
    )
    from pipeline.goal_trace import EXTERNAL_MAX_TRAIN_WEIGHT

    rec = pin_asset(fixture, kind="skill", asset_id="skill_e2e")
    # Promote without scan/approve blocked
    with pytest.raises(ValueError, match="promote blocked|approved"):
        promote_asset(rec["id"])

    scan_asset(rec["id"])
    # Still blocked without approve
    with pytest.raises(ValueError, match="promote blocked|approved"):
        promote_asset(rec["id"])

    # Approve without scan would fail for quarantined — already scanned
    approved = approve_asset(rec["id"], notes="looks ok")
    assert approved["status"] == "approved"
    assert approved["approval"]["actor"] == "test-operator"

    promoted = promote_asset(rec["id"], notes="fixture promote")
    assert promoted["status"] == "promoted"
    assert promoted.get("promoted_id")
    prom_path = pipeline / "external" / "promoted" / "skill_e2e.json"
    assert prom_path.is_file()
    draft = json.loads(prom_path.read_text(encoding="utf-8"))
    assert draft["schema"] == "external_promoted.v1"
    assert draft["trust"] == "external"
    assert draft["status"] == "draft"
    assert draft["pin"]["content_sha256"]
    assert draft["presence_smoke"]["pass"] is True

    # Audit log has pin/scan/approve/promote
    audit = (pipeline / "external" / "audit.jsonl").read_text(encoding="utf-8")
    actions = [json.loads(line)["action"] for line in audit.splitlines() if line.strip()]
    assert "pin" in actions
    assert "scan" in actions
    assert "approve" in actions
    assert "promote" in actions

    # goal_trace promote has trust=external and weight ≤ EXTERNAL_MAX
    traces = list((pipeline / "goal_traces").glob("external_promote_*.json"))
    assert traces, "expected promote goal_traces"
    tr = json.loads(traces[-1].read_text(encoding="utf-8"))
    assert tr.get("trust") == "external"
    assert float(tr.get("train_weight") or 0) <= EXTERNAL_MAX_TRAIN_WEIGHT
    assert tr.get("outcome") == "proven"


def test_reject_and_approve_from_quarantined_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    fixture = _write_skill_fixture(tmp_path / "fixtures")
    from pipeline.external_ingest import approve_asset, pin_asset, reject_asset, scan_asset

    rec = pin_asset(fixture, kind="skill", asset_id="skill_rej")
    with pytest.raises(ValueError, match="cannot approve"):
        approve_asset(rec["id"])

    scan_asset(rec["id"])
    rejected = reject_asset(rec["id"], reason="not wanted")
    assert rejected["status"] == "rejected"
    assert rejected["rejection"]["reason"] == "not wanted"


def test_presence_smoke_software_and_mcp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    from pipeline.external_ingest import approve_asset, pin_asset, promote_asset, scan_asset

    soft = _write_software_fixture(tmp_path / "fixtures")
    rec = pin_asset(soft, kind="software", asset_id="software_fake-tool")
    scan_asset(rec["id"])
    approve_asset(rec["id"])
    out = promote_asset(rec["id"])
    assert out["status"] == "promoted"
    assert out["presence_smoke"]["pass"] is True

    mcp = _write_mcp_fixture(tmp_path / "fixtures")
    rec2 = pin_asset(mcp, kind="mcp", asset_id="mcp_fake")
    scan_asset(rec2["id"])
    approve_asset(rec2["id"])
    out2 = promote_asset(rec2["id"])
    assert out2["status"] == "promoted"


def test_presence_smoke_fail_blocks_promote(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    emptyish = tmp_path / "fixtures" / "empty-skill"
    emptyish.mkdir(parents=True)
    (emptyish / "README.md").write_text("no skill md\n", encoding="utf-8")

    from pipeline.external_ingest import approve_asset, pin_asset, promote_asset, scan_asset

    rec = pin_asset(emptyish, kind="skill", asset_id="skill_empty")
    scan_asset(rec["id"])
    approve_asset(rec["id"])
    with pytest.raises(ValueError, match="presence smoke"):
        promote_asset(rec["id"])
    # Still approved, not promoted
    from pipeline.external_ingest import get_asset

    assert get_asset(rec["id"])["status"] == "approved"


def test_list_show_and_cli(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    fixture = _write_skill_fixture(tmp_path / "fixtures")
    from pipeline.external_ingest import list_assets, pin_asset, show_asset

    pin_asset(fixture, kind="skill", asset_id="skill_cli")
    rows = list_assets(kind="skill")
    assert any(r["id"] == "skill_cli" for r in rows)
    shown = show_asset("skill_cli")
    assert shown["asset"]["id"] == "skill_cli"

    # CLI round-trip
    from scripts.external_ingest import main as cli_main

    soft = _write_software_fixture(tmp_path / "fixtures", "cli-tool")
    rc = cli_main(
        [
            "--pipeline-dir",
            str(pipeline),
            "pin",
            "--path",
            str(soft),
            "--kind",
            "software",
            "--id",
            "software_cli-tool",
        ]
    )
    assert rc == 0
    rc = cli_main(["--pipeline-dir", str(pipeline), "scan", "--id", "software_cli-tool"])
    assert rc == 0
    rc = cli_main(
        ["--pipeline-dir", str(pipeline), "approve", "--id", "software_cli-tool"]
    )
    assert rc == 0
    rc = cli_main(
        ["--pipeline-dir", str(pipeline), "promote", "--id", "software_cli-tool"]
    )
    assert rc == 0
    rc = cli_main(["--pipeline-dir", str(pipeline), "list"])
    assert rc == 0
    rc = cli_main(["--pipeline-dir", str(pipeline), "show", "--id", "software_cli-tool"])
    assert rc == 0

    # promote without approve via CLI fails
    other = _write_skill_fixture(tmp_path / "fixtures", "no-approve")
    cli_main(
        [
            "--pipeline-dir",
            str(pipeline),
            "pin",
            "--path",
            str(other),
            "--kind",
            "skill",
            "--id",
            "skill_no-approve",
        ]
    )
    cli_main(["--pipeline-dir", str(pipeline), "scan", "--id", "skill_no-approve"])
    rc = cli_main(
        ["--pipeline-dir", str(pipeline), "promote", "--id", "skill_no-approve"]
    )
    assert rc == 1


def test_goal_trace_external_clamp_on_promote(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Promote path must stamp trust=external with weight ≤ EXTERNAL_MAX (Phase 3)."""
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    fixture = _write_skill_fixture(tmp_path / "fixtures")
    from pipeline.external_ingest import approve_asset, pin_asset, promote_asset, scan_asset
    from pipeline.goal_trace import EXTERNAL_MAX_TRAIN_WEIGHT, default_train_weight

    # Unit clamp still holds
    assert default_train_weight("proven", trust="external") == EXTERNAL_MAX_TRAIN_WEIGHT

    rec = pin_asset(fixture, kind="skill", asset_id="skill_trace")
    scan_asset(rec["id"])
    approve_asset(rec["id"])
    promote_asset(rec["id"])

    traces = list((pipeline / "goal_traces").glob("external_promote_*.json"))
    assert traces
    tr = json.loads(max(traces, key=lambda p: p.stat().st_mtime).read_text(encoding="utf-8"))
    assert tr["trust"] == "external"
    assert tr["train_weight"] <= EXTERNAL_MAX_TRAIN_WEIGHT
    assert tr["train_weight"] > 0  # promote success is low-but-nonzero external


def test_load_promoted_and_list_fail_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path
) -> None:
    """Phase 6: load/list promoted-only; draft/quarantine/revoked fail closed."""
    pipeline = tmp_path / "out"
    pipeline.mkdir()
    _reload_pipeline(monkeypatch, pipeline)

    fixture = _write_skill_fixture(tmp_path / "fixtures", name="p6-skill")
    from pipeline.external_ingest import (
        approve_asset,
        kind_to_graph_kind,
        list_promoted,
        load_promoted,
        pin_asset,
        promote_asset,
        resolve_promoted,
        revoke_asset,
        route_hit_from_promoted,
        scan_asset,
    )

    assert kind_to_graph_kind("skill") == "skill"
    assert kind_to_graph_kind("external_mcp") == "external_mcp"
    with pytest.raises(ValueError):
        kind_to_graph_kind("not_a_kind")

    # Path-unsafe ids rejected
    with pytest.raises(ValueError, match="path|invalid"):
        load_promoted("../etc/passwd")
    with pytest.raises(ValueError, match="path|invalid"):
        load_promoted("foo/bar")

    rec = pin_asset(fixture, kind="skill", asset_id="skill_p6")
    # Quarantined only — no promoted file
    with pytest.raises((FileNotFoundError, ValueError), match="not promoted|not found"):
        load_promoted("skill_p6")
    assert list_promoted() == []

    scan_asset(rec["id"])
    with pytest.raises((FileNotFoundError, ValueError), match="not promoted|not found"):
        load_promoted("skill_p6")

    approve_asset(rec["id"])
    # Approved-but-not-promoted still fails closed
    with pytest.raises((FileNotFoundError, ValueError), match="not promoted|not found"):
        load_promoted("skill_p6")

    promote_asset(rec["id"])
    draft = load_promoted("skill_p6")
    assert draft["schema"] == "external_promoted.v1"
    assert draft["trust"] == "external"
    assert draft["pin"]["content_sha256"]
    assert draft["external_asset_id"] == "skill_p6"

    # Resolve by promoted draft id as well
    by_draft = resolve_promoted(str(draft["id"]))
    assert by_draft["external_asset_id"] == "skill_p6"

    listed = list_promoted()
    assert len(listed) == 1
    assert listed[0]["external_asset_id"] == "skill_p6"

    hit = route_hit_from_promoted("skill_p6")
    assert hit["trust"] == "external"
    assert hit["status"] == "verified"
    assert hit["kind"] == "skill"
    assert hit["slug"] == "skill_p6"
    assert hit["pin"]["content_sha256"]

    # Revoke → load/list fail closed
    revoke_asset("skill_p6", reason="test revoke")
    with pytest.raises(ValueError, match="revoked"):
        load_promoted("skill_p6")
    assert list_promoted() == []
