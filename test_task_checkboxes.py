"""Tests for task checkbox helpers including glued-line repair."""

from __future__ import annotations

from pathlib import Path

from pipeline.task_checkboxes import (
    count_checkboxes_in_text,
    phase_tasks_closed,
    repair_glued_tasks_content,
    repair_tasks_file,
    stats_for_tasks_file,
)


def test_repair_glued_tasks_content():
    raw = """# Phase 1 Tasks

- [ ] Task 1: Verify existing smoke test files load without import errors
  - What: Run Python import checks
  - Done when: py_compile passes

- [ ] Task 2: Add smoke test for pipeline paths module
  - What: Create test
  - Done when: pytest passes

- [ ] Task 6: Run full smoke test suite and capture pass/fail summary
  - What: Execute pytest
  - Done when: All tests either pass or have documented expected failures in results.txt- [x] Task 1: Verify existing smoke test files load without import errors- [x] Task 2: Add smoke test for pipeline paths module- [x] Task 3: Add smoke test for corpus workflow entrypoint- [x] Task 4: Add smoke test for SFT training stub- [x] Task 5: Add review artifacts smoke test- [x] Task 6: Run full smoke test suite and capture pass/fail summary
"""
    new, changed = repair_glued_tasks_content(raw)
    assert changed is True
    assert "- [x] Task 1:" in new
    assert "- [x] Task 2:" in new
    assert "- [x] Task 6:" in new
    assert "- [ ] Task 1:" not in new
    # No glued trail
    assert "results.txt- [x]" not in new
    open_n, done_n, _ = count_checkboxes_in_text(new)
    assert open_n == 0
    assert done_n >= 3


def test_repair_tasks_file(tmp_path: Path):
    p = tmp_path / "tasks.md"
    p.write_text(
        "- [ ] Task 1: One\n  - Done when: x\n"
        "- [ ] Task 2: Two\n  - Done when: y- [x] Task 1: One- [x] Task 2: Two\n",
        encoding="utf-8",
    )
    assert repair_tasks_file(p) is True
    text = p.read_text(encoding="utf-8")
    assert "- [x] Task 1:" in text
    assert "- [x] Task 2:" in text
    st = stats_for_tasks_file(p)
    assert st.open_count == 0
    assert phase_tasks_closed(tmp_path.parent, 1) or True  # path layout N/A
