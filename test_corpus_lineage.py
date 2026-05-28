"""Tests for corpus lineage and QC helpers."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from pipeline.corpus_lineage import (
    dedupe_by_id,
    lineage_group_key,
    plan_refresh_generations,
    stamp_new_generation,
)
from pipeline.corpus_qc import (
    build_report,
    fix_canonical_per_file,
    load_records_by_file,
    prepare_refresh_in_file,
    stamp_legacy_records,
    write_records,
)


def test_lineage_group_key() -> None:
    rec = {
        "granularity": "task",
        "project_slug": "foo",
        "sequence_id": "foo__p1",
        "id": "foo__p1__p1of2",
    }
    assert lineage_group_key(rec) == "task:foo:foo__p1"


def test_plan_refresh_increments_generation() -> None:
    existing = [
        {
            "id": "a",
            "sequence_id": "seq1",
            "granularity": "task",
            "project_slug": "x",
            "corpus_generation": 1,
            "is_canonical": True,
        }
    ]
    plan = plan_refresh_generations(existing, {"task:x:seq1"})
    assert plan["task:x:seq1"] == (2, "seq1")


def test_prepare_refresh_marks_old_non_canonical(tmp_path: Path) -> None:
    path = tmp_path / "x.jsonl"
    write_records(
        path,
        [
            {
                "id": "old",
                "sequence_id": "seq1",
                "granularity": "task",
                "project_slug": "x",
                "corpus_generation": 1,
                "is_canonical": True,
            }
        ],
    )
    plan = prepare_refresh_in_file(path, {"task:x:seq1"})
    assert plan["task:x:seq1"][0] == 2
    rows = load_records_by_file(path)
    assert rows[0]["is_canonical"] is False

    stamp_new_generation(
        {
            "id": "new",
            "sequence_id": "seq1",
            "granularity": "task",
            "project_slug": "x",
        },
        generation=plan["task:x:seq1"][0],
        supersedes=plan["task:x:seq1"][1],
    )
    write_records(path, rows + [{"id": "new", "sequence_id": "seq1", "granularity": "task", "project_slug": "x", "corpus_generation": 2, "is_canonical": True, "supersedes": "seq1"}])

    report = build_report(load_records_by_file(path))
    assert report["canonical"] == 1
    assert report["superseded"] == 1


def test_dedupe_by_id_prefers_canonical() -> None:
    records = [
        {"id": "same", "is_canonical": False, "corpus_generation": 1, "train_tier": "C"},
        {"id": "same", "is_canonical": True, "corpus_generation": 2, "train_tier": "A"},
    ]
    out = dedupe_by_id(records)
    assert len(out) == 1
    assert out[0]["corpus_generation"] == 2


def test_fix_canonical_per_file(tmp_path: Path) -> None:
    path = tmp_path / "y.jsonl"
    write_records(
        path,
        [
            {
                "id": "a1",
                "sequence_id": "s",
                "granularity": "task",
                "project_slug": "p",
                "corpus_generation": 1,
                "is_canonical": True,
                "quality_label": "struggled",
                "test_verdict": "PASS",
                "review_verdict": "PASS",
            },
            {
                "id": "a2",
                "sequence_id": "s",
                "granularity": "task",
                "project_slug": "p",
                "corpus_generation": 2,
                "is_canonical": True,
                "quality_label": "clean",
                "test_verdict": "PASS",
                "review_verdict": "PASS",
            },
        ],
    )
    n = fix_canonical_per_file(path)
    assert n == 1
    rows = load_records_by_file(path)
    by_id = {r["id"]: r["is_canonical"] for r in rows}
    assert by_id["a1"] is False
    assert by_id["a2"] is True


def test_stamp_legacy_records(tmp_path: Path) -> None:
    path = tmp_path / "z.jsonl"
    path.write_text(json.dumps({"id": "only", "instruction": "x"}) + "\n", encoding="utf-8")
    n = stamp_legacy_records([path])
    assert n == 1
    row = load_records_by_file(path)[0]
    assert row["corpus_generation"] == 1
    assert row["is_canonical"] is True
