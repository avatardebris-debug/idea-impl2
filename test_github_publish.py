"""Tests for per-project local git publish (no network)."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.github_publish import (
    ensure_local_git,
    list_eligible_slugs,
    publish_project,
    repo_name_for_slug,
)


def test_repo_name_for_slug():
    assert repo_name_for_slug("ship_canary").startswith("pipe-")
    assert "ship_canary" in repo_name_for_slug("ship_canary")


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
