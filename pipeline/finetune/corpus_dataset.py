"""
Load merged SFT JSONL with per-sample train_weight for TRL/HuggingFace trainers.

Example:
    from pipeline.finetune.corpus_dataset import load_weighted_sft_dataset
    ds = load_weighted_sft_dataset()  # default: sft_task_weighted.jsonl
    # Use ds["train_weight"] with WeightedRandomSampler or loss masking in trainer.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

from pipeline.paths import finetune_corpus_dir


def default_sft_path(*, weighted: bool = True) -> pathlib.Path:
    name = "sft_task_weighted.jsonl" if weighted else "sft_task.jsonl"
    return finetune_corpus_dir() / name


def load_weighted_sft_records(
    path: pathlib.Path | None = None,
    *,
    weighted: bool = True,
    min_weight: float = 0.0,
) -> list[dict[str, Any]]:
    """Load JSONL records; filter by train_weight >= min_weight."""
    path = path or default_sft_path(weighted=weighted)
    if not path.exists():
        raise FileNotFoundError(f"Corpus file not found: {path}")

    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        w = float(rec.get("train_weight", 1.0))
        if w >= min_weight:
            records.append(rec)
    return records


def load_weighted_sft_dataset(path: pathlib.Path | None = None, **kwargs: Any) -> Any:
    """
    Return a HuggingFace Dataset with instruction/input/output and train_weight column.

    Requires: pip install datasets
    """
    from datasets import Dataset

    records = load_weighted_sft_records(path, **kwargs)
    if not records:
        return Dataset.from_dict({
            "instruction": [],
            "input": [],
            "output": [],
            "train_weight": [],
        })
    columns = {
        "instruction": [r.get("instruction", "") for r in records],
        "input": [r.get("input", "") for r in records],
        "output": [r.get("output", "") for r in records],
        "train_weight": [float(r.get("train_weight", 1.0)) for r in records],
        "train_tier": [r.get("train_tier", "?") for r in records],
        "project_slug": [r.get("project_slug", "") for r in records],
    }
    return Dataset.from_dict(columns)


def sampler_weights_for_trainer(records: list[dict[str, Any]]) -> list[float]:
    """Weights list for torch.utils.data.WeightedRandomSampler."""
    return [max(float(r.get("train_weight", 1.0)), 1e-6) for r in records]
