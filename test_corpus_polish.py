"""Tests for polish queue ↔ corpus refresh integration."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.corpus_polish import (
    CORPUS_REFRESH_FLAG,
    check_off_polish_queue,
    collect_polish_queue_complete,
    project_phases_done,
    should_force_refresh_corpus,
    slug_on_polish_queue,
    tag_polish_corpus_refresh,
)


def test_should_force_refresh_from_flag() -> None:
    state = {CORPUS_REFRESH_FLAG: True}
    tag_polish_corpus_refresh(state)
    assert should_force_refresh_corpus(state) is True


def test_should_force_refresh_from_polish_notes() -> None:
    assert should_force_refresh_corpus({"polish_notes": "fix tests"}) is True
    assert should_force_refresh_corpus({}) is False


def test_project_phases_done() -> None:
    assert project_phases_done({"phase": 3, "total_phases": 3}) is True
    assert project_phases_done({"phase": 2, "total_phases": 3}) is False


def test_check_off_polish_queue(tmp_path: Path) -> None:
    pq = tmp_path / "polish_queue.md"
    pq.write_text(
        "- [ ] **[my_project]** — finish phase 3\n",
        encoding="utf-8",
    )
    assert check_off_polish_queue("my_project", pq) is True
    text = pq.read_text(encoding="utf-8")
    assert "- [x]" in text
    assert slug_on_polish_queue("my_project", pq) is False


def test_collect_polish_queue_complete_dry_run(tmp_path: Path, monkeypatch) -> None:
    pq = tmp_path / "polish_queue.md"
    pq.write_text(
        "- [ ] **[done_proj]** — all phases done\n",
        encoding="utf-8",
    )

    projects = tmp_path / "projects"
    proj = projects / "done_proj"
    (proj / "state").mkdir(parents=True)
    (proj / "state" / "current_idea.json").write_text(
        json.dumps(
            {
                "_slug": "done_proj",
                "status": "complete",
                "phase": 3,
                "total_phases": 3,
                "title": "Done",
            }
        ),
        encoding="utf-8",
    )
    (proj / "workspace").mkdir()
    (proj / "phases" / "phase_1").mkdir(parents=True)
    (proj / "phases" / "phase_1" / "tasks.md").write_text("- [ ] task\n", encoding="utf-8")

    import pipeline.corpus_polish as cp

    monkeypatch.setattr(cp, "projects_dir", lambda: projects)

    results = collect_polish_queue_complete(polish_path=pq, verbose=False, dry_run=True)
    assert "done_proj" in results
