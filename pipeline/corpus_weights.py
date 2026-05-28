"""Training tier and sample-weight helpers for finetune corpus records."""

from __future__ import annotations

import random
from typing import Any

# Tier A/B/C/D — see corpus_collector merge policies.
TIER_WEIGHT: dict[str, float] = {
    "A": 1.0,    # clean — first-pass PASS
    "B": 0.65,   # patched — 1–2 retries, still PASS
    "C": 0.2,    # struggled — hard path but collected (often still tested)
    "D": 0.0,    # exclude — failed verdicts / unknown
}

DEFAULT_STRUGGLED_SAMPLE_RATE = 0.15


def train_tier_from_record(rec: dict[str, Any]) -> str:
    """Map a corpus record to train tier A–D from quality_label and verdicts."""
    test_v = str(rec.get("test_verdict", "PASS")).upper()
    review_v = str(rec.get("review_verdict", "PASS")).upper()
    if test_v != "PASS" or review_v != "PASS":
        return "D"

    ql = str(rec.get("quality_label", "struggled")).lower()
    if ql == "clean":
        return "A"
    if ql == "patched":
        return "B"
    if ql == "struggled":
        return "C"
    return "D"


def train_weight_for_record(rec: dict[str, Any], *, tier: str | None = None) -> float:
    t = tier if tier is not None else train_tier_from_record(rec)
    return TIER_WEIGHT.get(t, 0.0)


def enrich_record_weights(rec: dict[str, Any]) -> dict[str, Any]:
    """Add train_tier and train_weight to a record (mutates and returns rec)."""
    tier = train_tier_from_record(rec)
    rec["train_tier"] = tier
    rec["train_weight"] = train_weight_for_record(rec, tier=tier)
    return rec


def should_include_struggled(*, rng: random.Random) -> bool:
    return rng.random() < DEFAULT_STRUGGLED_SAMPLE_RATE


def filter_records_for_merge(
    records: list[dict[str, Any]],
    *,
    policy: str = "strict",
    filter_quality: list[str] | None = None,
    struggled_sample_rate: float = DEFAULT_STRUGGLED_SAMPLE_RATE,
    rng: random.Random | None = None,
) -> list[dict[str, Any]]:
    """
    Select records for merge export.

    policy:
      strict   — only filter_quality labels (default clean + patched)
      weighted — A+B always; C sampled at struggled_sample_rate; D dropped
      all      — every record with weight > 0 (no struggled subsample)
    """
    if policy == "strict":
        allowed = set(filter_quality or ["clean", "patched"])
        out: list[dict[str, Any]] = []
        for rec in records:
            enrich_record_weights(rec)
            if rec.get("quality_label") in allowed:
                out.append(rec)
        return out

    if rng is None:
        rng = random.Random()

    out = []
    struggled_pool: list[dict[str, Any]] = []

    for rec in records:
        enrich_record_weights(rec)
        tier = rec["train_tier"]
        if tier == "D" or rec["train_weight"] <= 0:
            continue
        if policy == "all":
            out.append(rec)
            continue
        # weighted
        if tier in ("A", "B"):
            out.append(rec)
        elif tier == "C":
            struggled_pool.append(rec)

    if policy == "weighted" and struggled_pool and struggled_sample_rate > 0:
        if struggled_sample_rate >= 1.0:
            chosen = struggled_pool
        else:
            n_keep = round(len(struggled_pool) * struggled_sample_rate)
            n_keep = max(1, min(n_keep, len(struggled_pool)))
            chosen = (
                struggled_pool
                if n_keep >= len(struggled_pool)
                else rng.sample(struggled_pool, n_keep)
            )
        out.extend(chosen)

    return out
