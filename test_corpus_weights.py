"""Tests for corpus train tiers and merge weighting."""

from __future__ import annotations

import random

from pipeline.corpus_weights import (
    DEFAULT_STRUGGLED_SAMPLE_RATE,
    TIER_WEIGHT,
    filter_records_for_merge,
    train_tier_from_record,
    train_weight_for_record,
)


def _rec(quality: str, **extra) -> dict:
    base = {
        "id": f"x_{quality}",
        "quality_label": quality,
        "retry_count": 0,
        "test_verdict": "PASS",
        "review_verdict": "PASS",
    }
    base.update(extra)
    return base


def test_tier_mapping() -> None:
    assert train_tier_from_record(_rec("clean")) == "A"
    assert train_tier_from_record(_rec("patched", retry_count=2)) == "B"
    assert train_tier_from_record(_rec("struggled", retry_count=5)) == "C"
    assert train_tier_from_record(_rec("clean", test_verdict="FAIL")) == "D"


def test_tier_weights() -> None:
    assert train_weight_for_record(_rec("clean")) == TIER_WEIGHT["A"]
    assert train_weight_for_record(_rec("struggled")) == TIER_WEIGHT["C"]
    assert train_weight_for_record(_rec("clean", test_verdict="FAIL")) == 0.0


def test_strict_merge_excludes_struggled() -> None:
    records = [_rec("clean"), _rec("patched"), _rec("struggled")]
    out = filter_records_for_merge(records, policy="strict", filter_quality=["clean", "patched"])
    labels = {r["quality_label"] for r in out}
    assert labels == {"clean", "patched"}
    assert all("train_weight" in r for r in out)


def test_weighted_merge_samples_struggled() -> None:
    records = [_rec("clean")] + [_rec("struggled", id=f"s{i}") for i in range(100)]
    rng = random.Random(42)
    out = filter_records_for_merge(
        records,
        policy="weighted",
        struggled_sample_rate=0.2,
        rng=rng,
    )
    assert len([r for r in out if r["quality_label"] == "clean"]) == 1
    struggled = [r for r in out if r["quality_label"] == "struggled"]
    assert 15 <= len(struggled) <= 25  # ~20% of 100


def test_weighted_merge_includes_all_ab() -> None:
    records = [_rec("clean"), _rec("patched"), _rec("struggled")]
    out = filter_records_for_merge(
        records,
        policy="weighted",
        struggled_sample_rate=0.0,
        rng=random.Random(0),
    )
    labels = {r["quality_label"] for r in out}
    assert "clean" in labels and "patched" in labels
    assert "struggled" not in labels
