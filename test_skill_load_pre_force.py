"""skill_load + pre_force_debug unit tests."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.pre_force_debug import (
    already_attempted,
    mark_attempted,
    try_enqueue_pre_force_debug,
)
from pipeline.skill_load import load_skill_body, skill_available


def test_systematic_debugging_skill_available(tmp_path: Path, monkeypatch):
    # Offline-friendly: inject a fake skill root
    sk = tmp_path / "skills" / "systematic-debugging"
    sk.mkdir(parents=True)
    (sk / "SKILL.md").write_text(
        "---\nname: systematic-debugging\n---\n\n# Systematic Debugging\n\n"
        "## Root Cause Investigation\nAlways find root cause.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        "pipeline.skill_load.skill_search_roots",
        lambda: [tmp_path / "skills"],
    )
    assert skill_available("systematic-debugging") is True
    body = load_skill_body("systematic-debugging", max_chars=2000)
    assert "Root Cause" in body


def test_pre_force_debug_once(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.setenv("PRE_FORCE_SYSTEMATIC_DEBUG", "1")
    # project_dir uses PIPELINE_DIR/projects/slug
    proj = tmp_path / "projects" / "demo"
    (proj / "state").mkdir(parents=True)
    (proj / "workspace").mkdir(parents=True)
    (proj / "state" / "current_idea.json").write_text(
        json.dumps({"title": "demo", "status": "phase_1_executing", "phase": 1}),
        encoding="utf-8",
    )

    p1 = try_enqueue_pre_force_debug(idea_slug="demo", phase=1, fix_report_content="fail")
    assert p1 is not None
    assert p1.get("systematic_debug") is True
    assert "SYSTEMATIC DEBUG" in p1["fix_instructions"]
    assert already_attempted(proj, 1) is True

    # Second time → allow force-advance
    p2 = try_enqueue_pre_force_debug(idea_slug="demo", phase=1)
    assert p2 is None


def test_pre_force_debug_disabled(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("PIPELINE_DIR", str(tmp_path))
    monkeypatch.setenv("PRE_FORCE_SYSTEMATIC_DEBUG", "0")
    proj = tmp_path / "projects" / "demo2"
    (proj / "state").mkdir(parents=True)
    (proj / "state" / "current_idea.json").write_text("{}", encoding="utf-8")
    assert try_enqueue_pre_force_debug(idea_slug="demo2", phase=1) is None
