"""Tests for file rescue recording and prompt hints."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline.file_rescue import (
    format_rescue_prompt_block,
    load_rescue_prompt_for_executor,
    save_rescue_record,
)
from pipeline.path_health import rescue_dir_filtered_moves


def test_rescue_dir_filtered_moves(tmp_path: Path):
    src = tmp_path / "stray"
    dest = tmp_path / "workspace"
    src.mkdir()
    dest.mkdir()
    (src / "mod.py").write_text("x=1\n", encoding="utf-8")
    (src / "pkg").mkdir()
    (src / "pkg" / "a.py").write_text("y=2\n", encoding="utf-8")

    moves = rescue_dir_filtered_moves(src, dest, label="test")
    assert len(moves) == 2
    assert (dest / "mod.py").is_file()
    assert (dest / "pkg" / "a.py").is_file()
    assert not src.exists() or not any(src.rglob("*.py"))


def test_save_and_load_rescue_prompt(tmp_path: Path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    moves = [
        {
            "src": str(tmp_path / "bad" / "x.py"),
            "dest": str(ws / "x.py"),
            "rel": "x.py",
            "label": "root loose .py",
        }
    ]
    rec = save_rescue_record(
        tmp_path,
        moves=moves,
        pruned=["removed workspace/pipeline/"],
        workspace=str(ws),
        phase=1,
        idea_slug="demo",
    )
    assert rec["move_count"] == 1
    assert (tmp_path / "state" / "file_rescue.json").is_file()
    data = json.loads((tmp_path / "state" / "file_rescue.json").read_text(encoding="utf-8"))
    assert data["moves"][0]["rel"] == "x.py"

    block = load_rescue_prompt_for_executor(tmp_path)
    assert "System file rescue" in block
    assert "canonical" in block.lower() or "Canonical" in block or "CANONICAL" in block.upper() or "exact" in block.lower()
    assert str(ws) in block or "x.py" in block


def test_format_empty():
    assert format_rescue_prompt_block(None) == ""
    assert format_rescue_prompt_block({"moves": [], "pruned": []}) == ""
