"""Smoke tests for corpus_workflow CLI helpers."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from pipeline.finetune.corpus_dataset import load_weighted_sft_records, sampler_weights_for_trainer


def test_sampler_weights() -> None:
    recs = [
        {"train_weight": 1.0},
        {"train_weight": 0.2},
    ]
    w = sampler_weights_for_trainer(recs)
    assert w == [1.0, 0.2]


def test_collect_all_cli_parses_skip_gate() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pipeline.corpus_collector", "--help"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert "--skip-gate" in result.stdout


def test_load_records_missing_raises(tmp_path: Path, monkeypatch) -> None:
    import pipeline.finetune.corpus_dataset as cd

    monkeypatch.setattr(cd, "finetune_corpus_dir", lambda: tmp_path)
    try:
        load_weighted_sft_records()
        assert False, "expected FileNotFoundError"
    except FileNotFoundError:
        pass
