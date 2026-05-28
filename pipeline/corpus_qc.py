"""
pipeline/corpus_qc.py
Quality control for finetune corpus JSONL: lineage audit, canonical repair, legacy stamping.

Usage:
    python -m pipeline.corpus_qc --report
    python -m pipeline.corpus_qc --stamp-legacy
    python -m pipeline.corpus_qc --fix-canonical
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from collections import defaultdict
from typing import Any

from pipeline.corpus_lineage import ensure_lineage_defaults, lineage_group_key
from pipeline.corpus_weights import train_tier_from_record
from pipeline.paths import finetune_corpus_dir

_TIER_RANK = {"A": 4, "B": 3, "C": 2, "D": 1}


def raw_corpus_root() -> pathlib.Path:
    return finetune_corpus_dir() / "raw"


def iter_jsonl_files(root: pathlib.Path | None = None) -> list[pathlib.Path]:
    base = root or raw_corpus_root()
    if not base.exists():
        return []
    return sorted(base.rglob("*.jsonl"))


def load_records(paths: list[pathlib.Path] | None = None) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths or iter_jsonl_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def load_records_by_file(path: pathlib.Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def write_records(path: pathlib.Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _granularity_from_path(path: pathlib.Path) -> str | None:
    parts = {p.lower() for p in path.parts}
    if "task" in parts:
        return "task"
    if "phase" in parts:
        return "phase"
    if "project" in parts:
        return "project"
    return None


def stamp_legacy_records(paths: list[pathlib.Path] | None = None, *, dry_run: bool = False) -> int:
    """Add corpus_generation=1, is_canonical=True to rows missing lineage fields."""
    changed = 0
    for path in paths or iter_jsonl_files():
        records = load_records_by_file(path)
        inferred_gran = _granularity_from_path(path)
        file_changed = False
        for rec in records:
            before = (
                rec.get("corpus_generation"),
                rec.get("is_canonical"),
                rec.get("sequence_id"),
                rec.get("granularity"),
            )
            ensure_lineage_defaults(rec)
            if not rec.get("granularity") and inferred_gran:
                rec["granularity"] = inferred_gran
            after = (
                rec.get("corpus_generation"),
                rec.get("is_canonical"),
                rec.get("sequence_id"),
                rec.get("granularity"),
            )
            if before != after:
                file_changed = True
                changed += 1
        if file_changed and not dry_run:
            write_records(path, records)
    return changed


def fix_canonical_per_file(path: pathlib.Path, *, dry_run: bool = False) -> int:
    """
    For each lineage group in one JSONL file, keep only the best generation canonical.

    Prefers higher corpus_generation; ties break on train tier (A > B > C).
    """
    records = load_records_by_file(path)
    if not records:
        return 0

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        ensure_lineage_defaults(rec)
        groups[lineage_group_key(rec)].append(rec)

    flipped = 0
    for group_recs in groups.values():
        def _sort_key(r: dict[str, Any]) -> tuple[int, int]:
            gen = int(r.get("corpus_generation", 1))
            tier = train_tier_from_record(r)
            return (gen, _TIER_RANK.get(tier, 0))

        winner = max(group_recs, key=_sort_key)
        winner_id = winner.get("id")
        for rec in group_recs:
            should_canonical = rec.get("id") == winner_id
            if bool(rec.get("is_canonical", True)) != should_canonical:
                rec["is_canonical"] = should_canonical
                flipped += 1

    if flipped and not dry_run:
        write_records(path, records)
    return flipped


def fix_canonical_all(*, dry_run: bool = False) -> int:
    total = 0
    for path in iter_jsonl_files():
        total += fix_canonical_per_file(path, dry_run=dry_run)
    return total


def build_report(records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    records = records if records is not None else load_records()
    report: dict[str, Any] = {
        "total_records": len(records),
        "canonical": 0,
        "superseded": 0,
        "missing_lineage": 0,
        "multi_canonical_groups": 0,
        "generation_max": 0,
        "by_granularity": defaultdict(int),
        "by_generation": defaultdict(int),
    }

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        if "corpus_generation" not in rec or "is_canonical" not in rec:
            report["missing_lineage"] += 1
        ensure_lineage_defaults(rec)
        if rec.get("is_canonical", True):
            report["canonical"] += 1
        else:
            report["superseded"] += 1
        gen = int(rec.get("corpus_generation", 1))
        report["generation_max"] = max(report["generation_max"], gen)
        report["by_generation"][gen] += 1
        gran = rec.get("granularity", "unknown")
        report["by_granularity"][gran] += 1
        groups[lineage_group_key(rec)].append(rec)

    for group_recs in groups.values():
        canonical_count = sum(1 for r in group_recs if r.get("is_canonical", True))
        if canonical_count > 1:
            report["multi_canonical_groups"] += 1

    report["unique_sequences"] = len(groups)
    report["by_granularity"] = dict(report["by_granularity"])
    report["by_generation"] = dict(sorted(report["by_generation"].items()))
    return report


def print_report(report: dict[str, Any]) -> None:
    print(f"\n{'='*50}")
    print("  Corpus QC Report")
    print(f"{'='*50}")
    print(f"  Total records:        {report['total_records']}")
    print(f"  Unique sequences:     {report['unique_sequences']}")
    print(f"  Canonical:            {report['canonical']}")
    print(f"  Superseded:           {report['superseded']}")
    print(f"  Missing lineage:      {report['missing_lineage']}")
    print(f"  Multi-canonical bugs: {report['multi_canonical_groups']}")
    print(f"  Max generation:       {report['generation_max']}")
    print("  By granularity:")
    for gran, count in sorted(report["by_granularity"].items()):
        print(f"    {gran:<12} {count:>5}")
    print("  By generation:")
    for gen, count in report["by_generation"].items():
        print(f"    gen {gen:<8} {count:>5}")
    print("=" * 50)


def mark_keys_non_canonical(
    path: pathlib.Path,
    keys: set[str],
    *,
    dry_run: bool = False,
) -> int:
    """Set is_canonical=False on all records whose lineage_group_key is in keys."""
    records = load_records_by_file(path)
    flipped = 0
    for rec in records:
        ensure_lineage_defaults(rec)
        if lineage_group_key(rec) in keys and rec.get("is_canonical", True):
            rec["is_canonical"] = False
            flipped += 1
    if flipped and not dry_run:
        write_records(path, records)
    return flipped


def prepare_refresh_in_file(
    path: pathlib.Path,
    incoming_keys: set[str],
    *,
    dry_run: bool = False,
) -> dict[str, tuple[int, str | None]]:
    """
    Mark prior generations non-canonical and return generation plan for incoming keys.
    """
    from pipeline.corpus_lineage import plan_refresh_generations

    records = load_records_by_file(path)
    if incoming_keys and not dry_run:
        mark_keys_non_canonical(path, incoming_keys)
        records = load_records_by_file(path)
    return plan_refresh_generations(records, incoming_keys)


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Finetune corpus QC and lineage repair")
    parser.add_argument("--report", action="store_true", help="Print lineage/QC summary")
    parser.add_argument(
        "--stamp-legacy",
        action="store_true",
        help="Add corpus_generation=1 and is_canonical=True to rows missing lineage",
    )
    parser.add_argument(
        "--fix-canonical",
        action="store_true",
        help="Keep only highest generation (best tier) canonical per sequence",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    args = parser.parse_args()

    if not any([args.report, args.stamp_legacy, args.fix_canonical]):
        parser.print_help()
        sys.exit(0)

    if args.stamp_legacy:
        n = stamp_legacy_records(dry_run=args.dry_run)
        verb = "would stamp" if args.dry_run else "stamped"
        print(f"  {verb} lineage on {n} record(s)")

    if args.fix_canonical:
        n = fix_canonical_all(dry_run=args.dry_run)
        verb = "would fix" if args.dry_run else "fixed"
        print(f"  {verb} {n} canonical flag(s)")

    if args.report:
        print_report(build_report())


if __name__ == "__main__":
    _cli()
