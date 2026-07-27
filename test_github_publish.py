"""Tests for per-project local git publish (no network).

L1 = local git commit of projects/<slug>/ (always on matching trigger).
L2 = optional push when PIPELINE_GITHUB_PUBLISH=1 (fail-soft; no live network in tests).
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.github_publish import (
    ensure_local_git,
    list_eligible_slugs,
    maybe_publish_project,
    publish_enabled,
    publish_project,
    publish_triggers,
    repo_name_for_slug,
    repo_prefix,
)


def test_repo_name_for_slug():
    assert repo_name_for_slug("ship_canary").startswith("pipe-")
    assert "ship_canary" in repo_name_for_slug("ship_canary")


def test_publish_enabled_and_triggers_pure_helpers(monkeypatch):
    """Pure helpers: env parsing for L1/L2 flags (no git, no network)."""
    monkeypatch.delenv("PIPELINE_GITHUB_PUBLISH", raising=False)
    assert publish_enabled() is False
    monkeypatch.setenv("PIPELINE_GITHUB_PUBLISH", "1")
    assert publish_enabled() is True
    monkeypatch.setenv("PIPELINE_GITHUB_PUBLISH", "0")
    assert publish_enabled() is False

    monkeypatch.delenv("PIPELINE_GITHUB_ON", raising=False)
    default = publish_triggers()
    assert "complete" in default
    assert "field_proven" in default

    monkeypatch.setenv("PIPELINE_GITHUB_ON", "field_proven")
    assert publish_triggers() == frozenset({"field_proven"})

    monkeypatch.setenv("PIPELINE_GITHUB_REPO_PREFIX", "out-")
    assert repo_prefix() == "out-"
    assert repo_name_for_slug("x").startswith("out-")


def test_ensure_local_git_commits_whole_tree(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("PIPELINE_GITHUB_PUBLISH", raising=False)
    proj = tmp_path / "my_tool"
    (proj / "workspace").mkdir(parents=True)
    (proj / "state").mkdir()
    (proj / "phases" / "phase_1").mkdir(parents=True)
    (proj / "workspace" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (proj / "state" / "current_idea.json").write_text(
        json.dumps({"title": "My Tool", "status": "complete", "description": "demo"}),
        encoding="utf-8",
    )
    (proj / "phases" / "phase_1" / "tasks.md").write_text("- [x] Task 1\n", encoding="utf-8")

    r = ensure_local_git(proj, slug="my_tool", message="test commit")
    assert r.ok, r.error
    assert r.sha
    assert (proj / ".git").is_dir()
    assert (proj / ".gitignore").is_file()
    assert (proj / "README.md").is_file()

    # Second call clean
    r2 = ensure_local_git(proj, slug="my_tool", message="noop")
    assert r2.ok
    assert r2.sha == r.sha


def test_publish_project_local_only(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PIPELINE_GITHUB_PUBLISH", "0")
    proj = tmp_path / "abc"
    (proj / "workspace").mkdir(parents=True)
    (proj / "workspace" / "a.py").write_text("x=1\n", encoding="utf-8")
    (proj / "state").mkdir()
    (proj / "state" / "current_idea.json").write_text(
        json.dumps({"title": "Abc", "status": "complete"}), encoding="utf-8"
    )

    r = publish_project("abc", trigger="complete", project_path=proj, force_push=False)
    assert r.ok, r.error
    assert r.local_only
    assert r.sha
    status = json.loads((proj / "state" / "github_status.json").read_text(encoding="utf-8"))
    assert status.get("sha")


def test_maybe_publish_l2_fail_soft_no_network(tmp_path: Path, monkeypatch):
    """L2 on + missing org: push fails soft; never raises; L1 commit still attempted.

    Uses force_push via publish_project path under a temp project; no GitHub API.
    """
    monkeypatch.setenv("PIPELINE_GITHUB_PUBLISH", "1")
    monkeypatch.delenv("PIPELINE_GITHUB_ORG", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)

    proj = tmp_path / "l2soft"
    (proj / "workspace").mkdir(parents=True)
    (proj / "workspace" / "a.py").write_text("x=1\n", encoding="utf-8")
    (proj / "state").mkdir()
    (proj / "state" / "current_idea.json").write_text(
        json.dumps({"title": "L2Soft", "status": "field_proven"}), encoding="utf-8"
    )

    # force_push=True exercises push_to_github without requiring publish_enabled alone
    r = publish_project(
        "l2soft", trigger="field_proven", project_path=proj, force_push=True
    )
    # Local commit succeeded; push fails soft (no org / no network)
    assert r.sha, "L1 local commit should produce a sha even when L2 fails"
    assert r.ok is False
    assert "PIPELINE_GITHUB_ORG" in (r.error or "") or r.error
    assert (proj / "state" / "github_status.json").is_file()

    # maybe_publish_project never raises (uses default project_dir; trigger filter)
    monkeypatch.setenv("PIPELINE_GITHUB_ON", "complete,field_proven")
    # Trigger not matching → None
    monkeypatch.setenv("PIPELINE_GITHUB_ON", "complete")
    out = maybe_publish_project("anything", trigger="ship_insufficient")
    assert out is None


def test_list_eligible_slugs(tmp_path: Path):
    for name, st in [("a", "complete"), ("b", "field_proven"), ("c", "ship_insufficient")]:
        p = tmp_path / name
        (p / "state").mkdir(parents=True)
        (p / "state" / "current_idea.json").write_text(
            json.dumps({"status": st}), encoding="utf-8"
        )
    found = list_eligible_slugs(
        statuses=frozenset({"complete", "field_proven"}),
        projects_root=tmp_path,
    )
    assert set(found) == {"a", "b"}
