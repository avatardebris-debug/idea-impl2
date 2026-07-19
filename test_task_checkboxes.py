"""Tests for task checkbox honesty gates."""

from __future__ import annotations

from pathlib import Path

from pipeline.review_artifacts import build_review_result, count_blocking_bugs, review_verdict_is_fail
from pipeline.task_checkboxes import (
    count_checkboxes_in_text,
    phase_tasks_closed,
    project_all_tasks_closed,
    stats_for_phase,
)


def test_count_open_and_done():
    text = """
# Phase 1 Tasks
- [ ] Task 1: foo
- [x] Task 2: bar
- [ ] Task 3: baz
"""
    open_n, done_n, titles = count_checkboxes_in_text(text)
    assert open_n == 2
    assert done_n == 1
    assert any("Task 1" in t for t in titles)


def test_phase_tasks_closed(tmp_path: Path):
    phase = tmp_path / "phases" / "phase_1"
    phase.mkdir(parents=True)
    tasks = phase / "tasks.md"
    tasks.write_text("- [ ] Task 1: still open\n", encoding="utf-8")
    assert not phase_tasks_closed(tmp_path, 1)
    tasks.write_text("- [x] Task 1: done\n- [x] Task 2: done\n", encoding="utf-8")
    assert phase_tasks_closed(tmp_path, 1)


def test_project_all_tasks_closed(tmp_path: Path):
    for n, body in (
        (1, "- [x] Task 1: a\n"),
        (2, "- [ ] Task 1: still open\n"),
    ):
        d = tmp_path / "phases" / f"phase_{n}"
        d.mkdir(parents=True)
        (d / "tasks.md").write_text(body, encoding="utf-8")
    assert not project_all_tasks_closed(tmp_path)
    p2 = tmp_path / "phases" / "phase_2" / "tasks.md"
    p2.write_text("- [x] Task 1: closed\n", encoding="utf-8")
    assert project_all_tasks_closed(tmp_path)


def test_review_fail_counts_as_blocking():
    review = (
        "# Code Review\n\n"
        "## Blocking Bugs\nNone\n\n"
        "## Non-Blocking Notes\n- style\n\n"
        "## Verdict\nFAIL - validation does not reliably reject invalid schemas\n"
        + ("x" * 200)
    )
    assert review_verdict_is_fail(review)
    assert count_blocking_bugs(review) >= 1
    result = build_review_result(
        review_content=review,
        review_path="phases/phase_2/review.md",
        tasks_path="phases/phase_2/tasks.md",
        workspace_path="/tmp/ws",
    )
    assert result["blocking_bugs"] >= 1
    assert result["review_fail"] is True


def test_review_pass_with_none_blocking():
    review = (
        "# Code Review\n\n"
        "## Blocking Bugs\nNone\n\n"
        "## Non-Blocking Notes\n- ok\n\n"
        "## Verdict\nPASS - all good\n"
        + ("x" * 200)
    )
    assert not review_verdict_is_fail(review)
    assert count_blocking_bugs(review) == 0
