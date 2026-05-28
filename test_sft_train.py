"""Tests for SFT formatting and CLI-safe helpers (no GPU / trl required)."""

import pathlib

import pytest

from pipeline.finetune.formatting import alpaca_prompt, alpaca_text, record_to_text
from pipeline.finetune.sft_train import cmd_dry_run
from pipeline.finetune.weighted_trainer import validate_record_weights


def test_alpaca_with_input() -> None:
    text = alpaca_text("Do X", "context", "code here")
    assert "### Instruction:" in text
    assert "### Input:" in text
    assert text.endswith("code here")


def test_alpaca_no_input() -> None:
    prompt = alpaca_prompt("Do X", "")
    assert "### Input:" not in prompt
    assert "### Response:" in prompt


def test_record_to_text() -> None:
    t = record_to_text({"instruction": "a", "input": "", "output": "b"})
    assert t.endswith("b")


def test_cmd_dry_run_empty_after_filter(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    corpus = tmp_path / "sft.jsonl"
    corpus.write_text(
        '{"id":"x","instruction":"i","input":"","output":"o","train_weight":0.2}\n',
        encoding="utf-8",
    )
    cmd_dry_run(corpus, min_weight=1.0)
    out = capsys.readouterr().out
    assert "No records after filtering." in out


def test_validate_record_weights_rejects_bad_value() -> None:
    records = [{"id": "bad", "train_weight": "oops"}]
    with pytest.raises(ValueError, match="row=0 id='bad'"):
        validate_record_weights(records)


def test_validate_record_weights_allows_zero() -> None:
    records = [{"id": "zero", "train_weight": 0}]
    assert validate_record_weights(records) == [0.0]
