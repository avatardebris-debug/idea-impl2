"""
pipeline/corpus_export.py
Merge raw corpus JSONL into training files and print corpus statistics.
"""

from __future__ import annotations

import json
import pathlib
import random

from pipeline.corpus_paths import corpus_dir, phase_dir, project_corpus_dir, raw_dir, task_dir


def corpus_stats() -> None:
    """Print a summary of the current corpus."""
    if not raw_dir().exists():
        print("No corpus yet. Run --collect-all to build it.")
        return

    total_records = 0
    quality_counts: dict[str, int] = {}
    model_counts: dict[str, int] = {}

    for jsonl_file in raw_dir().rglob("*.jsonl"):
        for line in jsonl_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                total_records += 1
                ql = rec.get("quality_label", "?")
                quality_counts[ql] = quality_counts.get(ql, 0) + 1
                m = rec.get("model", "?")
                model_counts[m] = model_counts.get(m, 0) + 1
            except Exception:
                pass

    task_count = sum(1 for _ in task_dir().glob("*.jsonl")) if task_dir().exists() else 0
    phase_count = sum(1 for _ in phase_dir().glob("*.jsonl")) if phase_dir().exists() else 0
    project_count = (
        sum(1 for _ in project_corpus_dir().glob("*.jsonl"))
        if project_corpus_dir().exists()
        else 0
    )

    print(f"\n{'='*50}")
    print("  Fine-Tune Corpus Stats")
    print(f"{'='*50}")
    print(f"  Total records:   {total_records}")
    print(f"  Task files:      {task_count}   -> {task_dir()}")
    print(f"  Phase files:     {phase_count}   -> {phase_dir()}")
    print(f"  Project files:   {project_count}   -> {project_corpus_dir()}")
    print("")
    print("  Quality breakdown:")
    for label, count in sorted(quality_counts.items()):
        bar = "#" * (count * 30 // max(total_records, 1))
        print(f"    {label:<12} {count:>5}  {bar}")
    print("")
    print("  By model:")
    for model, count in sorted(model_counts.items(), key=lambda x: -x[1]):
        print(f"    {model:<40} {count:>5}")
    print("=" * 50)


def merge_corpus(
    granularity: str = "task",
    filter_quality: list[str] | None = None,
    output_path: pathlib.Path | None = None,
    *,
    merge_policy: str = "strict",
    struggled_sample_rate: float = 0.15,
    merge_seed: int | None = None,
    canonical_only: bool = True,
) -> pathlib.Path:
    """
    Merge all JSONL files of the given granularity into a single file ready for trl sft.
    """
    from pipeline.corpus_lineage import dedupe_by_id, ensure_lineage_defaults
    from pipeline.corpus_weights import filter_records_for_merge

    if filter_quality is None:
        filter_quality = ["clean", "patched"]

    src_dir = {
        "task": task_dir(),
        "phase": phase_dir(),
        "project": project_corpus_dir(),
    }.get(granularity)
    if src_dir is None:
        raise ValueError(f"Unknown granularity: {granularity}")

    if output_path is None:
        corpus_dir().mkdir(parents=True, exist_ok=True)
        suffix = "" if merge_policy == "strict" else f"_{merge_policy}"
        output_path = corpus_dir() / f"sft_{granularity}{suffix}.jsonl"

    all_records: list[dict] = []
    for jsonl_file in sorted(src_dir.glob("*.jsonl")):
        for line in jsonl_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ensure_lineage_defaults(rec)
                if canonical_only and not rec.get("is_canonical", True):
                    continue
                all_records.append(rec)
            except Exception:
                pass

    all_records = dedupe_by_id(all_records)

    rng = random.Random(merge_seed)
    selected = filter_records_for_merge(
        all_records,
        policy=merge_policy,
        filter_quality=filter_quality,
        struggled_sample_rate=struggled_sample_rate,
        rng=rng,
    )

    seen_ids: set[str] = set()
    tier_counts: dict[str, int] = {}
    weight_sum = 0.0
    written = 0

    with output_path.open("w", encoding="utf-8") as out:
        for rec in selected:
            rid = rec.get("id")
            if rid and rid in seen_ids:
                continue
            tier = rec.get("train_tier", "?")
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
            weight_sum += float(rec.get("train_weight", 0))
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if rid:
                seen_ids.add(rid)
            written += 1

    print(f"Merged {written} {granularity}-level records ({merge_policy}) -> {output_path}")
    if merge_policy != "strict":
        print("  Tier breakdown:", ", ".join(f"{k}={v}" for k, v in sorted(tier_counts.items())))
        print(f"  Sum of train_weight: {weight_sum:.1f}")
    return output_path
