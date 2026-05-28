"""
pipeline/corpus_workflow.py
End-to-end finetune corpus workflow (weighted export, lineage, polish refresh, gate).

Usage:
    python -m pipeline.corpus_workflow status
    python -m pipeline.corpus_workflow audit [--policy enforce]
    python -m pipeline.corpus_workflow export [--merge-policy weighted]
    python -m pipeline.corpus_workflow polish-candidates [--append-queue]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from pipeline.paths import finetune_corpus_dir


def cmd_status() -> None:
    from pipeline.corpus_collector import corpus_stats
    from pipeline.corpus_qc import build_report, load_records

    print("\n--- Raw corpus ---")
    corpus_stats()
    report = build_report(load_records())
    print("\n--- Lineage ---")
    print(f"  Canonical:     {report['canonical']}")
    print(f"  Superseded:    {report['superseded']}")
    print(f"  Max generation: {report['generation_max']}")


def cmd_audit(policy: str | None) -> int:
    from pipeline.corpus_gate import audit_all_projects, gate_policy

    if policy:
        os.environ["CORPUS_GATE_POLICY"] = policy
    rows = audit_all_projects(only_complete=True, run_quality_scorer=False)
    blocked = sum(1 for _, r in rows if not r.allow_collect)
    warned = sum(1 for _, r in rows if r.warnings)
    active_policy = policy or gate_policy()
    print(f"\n  Policy: {active_policy}")
    print(f"  Projects audited: {len(rows)}")
    print(f"  Would block collect: {blocked}")
    print(f"  With warnings: {warned}")
    return 1 if blocked and active_policy == "enforce" else 0


def cmd_export(
    *,
    granularity: str = "task",
    merge_policy: str = "weighted",
    struggled_rate: float = 0.15,
    merge_seed: int | None = 42,
) -> Path:
    from pipeline.corpus_collector import merge_corpus

    out = merge_corpus(
        granularity=granularity,
        merge_policy=merge_policy,
        struggled_sample_rate=struggled_rate,
        merge_seed=merge_seed,
        canonical_only=True,
    )
    print(f"\n  Export ready: {out}")
    return out


def cmd_polish_candidates(*, append_queue: bool = False, dry_run: bool = False) -> int:
    """
    List (or append to polish_queue.md) projects that fail corpus gate closeout.
    """
    from pipeline.corpus_gate import audit_all_projects
    from pipeline.corpus_polish import resolve_polish_queue_path

    rows = audit_all_projects(only_complete=True, run_quality_scorer=False)
    candidates = [
        (slug, r)
        for slug, r in rows
        if not r.passed or r.recommend_polish
    ]
    if not candidates:
        print("  No polish candidates from gate audit.")
        return 0

    print(f"\n  Gate polish candidates ({len(candidates)}):")
    lines_to_add: list[str] = []
    for slug, result in sorted(candidates):
        reason = (result.blockers or result.warnings or ["needs review"])[0]
        print(f"    {slug}: {reason[:72]}")
        lines_to_add.append(
            f"- [ ] **[{slug}]** — corpus gate: {reason[:120]}. "
            f"Run: python pipeline/runner.py --polish --resume ..."
        )

    if not append_queue:
        print("\n  Pass --append-queue to add lines to polish_queue.md")
        return 0

    pq = resolve_polish_queue_path()
    existing = pq.read_text(encoding="utf-8") if pq.exists() else ""
    new_slugs = {slug for slug, _ in candidates}
    if any(slug in existing for slug in new_slugs):
        print("  (some slugs already mentioned in queue — still appending new lines)")

    if dry_run:
        print(f"\n  Would append {len(lines_to_add)} line(s) to {pq}")
        return 0

    with pq.open("a", encoding="utf-8") as f:
        f.write("\n\n# Added by corpus_workflow polish-candidates\n")
        for line in lines_to_add:
            f.write(line + "\n")
    print(f"\n  Appended {len(lines_to_add)} line(s) to {pq}")
    return 0


def cmd_refresh_polish_queue(*, dry_run: bool = False) -> None:
    from pipeline.corpus_polish import collect_polish_queue_complete

    collect_polish_queue_complete(dry_run=dry_run)


def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="Finetune corpus workflow (QC phases 1–4)",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Corpus stats + lineage summary")

    p_audit = sub.add_parser("audit", help="Run closeout gate on all complete projects")
    p_audit.add_argument("--policy", choices=["off", "warn", "enforce"], default=None)

    p_export = sub.add_parser("export", help="Merge canonical corpus to sft_*.jsonl")
    p_export.add_argument("--granularity", choices=["task", "phase", "project"], default="task")
    p_export.add_argument(
        "--merge-policy",
        choices=["strict", "weighted", "all"],
        default="weighted",
    )
    p_export.add_argument("--struggled-rate", type=float, default=0.15)
    p_export.add_argument("--merge-seed", type=int, default=42)

    p_polish = sub.add_parser(
        "polish-candidates",
        help="List projects failing corpus gate (candidates for --polish)",
    )
    p_polish.add_argument(
        "--append-queue",
        action="store_true",
        help="Append candidates to polish_queue.md",
    )
    p_polish.add_argument("--dry-run", action="store_true")

    p_refresh = sub.add_parser(
        "refresh-polish",
        help="Force-refresh corpus for fully complete polish_queue entries",
    )
    p_refresh.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "status":
        cmd_status()
    elif args.command == "audit":
        sys.exit(cmd_audit(args.policy))
    elif args.command == "export":
        cmd_export(
            granularity=args.granularity,
            merge_policy=args.merge_policy,
            struggled_rate=args.struggled_rate,
            merge_seed=args.merge_seed,
        )
    elif args.command == "polish-candidates":
        sys.exit(cmd_polish_candidates(
            append_queue=args.append_queue,
            dry_run=args.dry_run,
        ))
    elif args.command == "refresh-polish":
        cmd_refresh_polish_queue(dry_run=args.dry_run)


if __name__ == "__main__":
    _cli()
