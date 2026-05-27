#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline/finetune/harvest.py
Harvest fine-tuning training data from completed pipeline projects.

Produces two JSONL files:
  1. sft_pairs.jsonl   — Supervised Fine-Tuning pairs (prompt → winning output)
                         Used for: Task-level Track A, Phase-compression Track B
  2. dpo_pairs.jsonl   — Direct Preference Optimisation pairs (chosen vs rejected)
                         Used for: Discriminator/generator racing reward signal

Data sources scanned per project/phase:
  - phases/phase_N/tasks.md            → executor prompt input
  - state/master_plan.md               → context injected into prompt
  - phases/phase_N/fix_report.md       → rejected attempt history
  - phases/phase_N/validation_report.md → pass/fail signal
  - workspace/                          → chosen output (winning code)

Usage:
    python pipeline/finetune/harvest.py
    python pipeline/finetune/harvest.py --out-dir finetune_data
    python pipeline/finetune/harvest.py --min-tasks 3 --status complete
    python pipeline/finetune/harvest.py --track phase  # phase-level compression pairs
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Iterator

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = pathlib.Path(__file__).parent.parent.parent.resolve()


def _pipeline_dir() -> pathlib.Path:
    from pipeline.pipeline_config import get_pipeline_dir

    return get_pipeline_dir()


def _projects_dir() -> pathlib.Path:
    return _pipeline_dir() / "projects"

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SFTPair:
    """A single supervised fine-tuning example."""
    slug:           str
    phase:          int
    instruction:    str   # the full executor prompt (system + task list)
    output:         str   # the winning workspace files serialized as a document
    tasks_count:    int   # number of tasks in this phase
    passed_on_try:  int   # 1 = first pass, 2+ = needed retries
    workspace_files: list[str] = field(default_factory=list)

@dataclass
class DPOPair:
    """A direct preference optimisation pair."""
    slug:     str
    phase:    int
    prompt:   str   # same executor prompt
    chosen:   str   # output that passed validation
    rejected: str   # earliest failed attempt output
    failure_reason: str = ""   # what went wrong in rejected


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

ATTEMPT_HEADER = re.compile(
    r"^###\s+Attempt\s+(\d+)", re.MULTILINE
)
VERDICT_PASS = re.compile(r"Verdict:\s*PASS", re.IGNORECASE)
VERDICT_FAIL = re.compile(r"Verdict:\s*FAIL", re.IGNORECASE)


def _parse_attempts(fix_report: str) -> list[dict]:
    """
    Split a fix_report.md into individual attempt records.

    Returns list of:
        {"attempt": int, "text": str, "passed": bool}
    """
    # Find all "### Attempt N" header positions
    headers = list(ATTEMPT_HEADER.finditer(fix_report))
    if not headers:
        return []

    attempts = []
    for i, m in enumerate(headers):
        start = m.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(fix_report)
        text = fix_report[start:end].strip()
        attempts.append({
            "attempt": int(m.group(1)),
            "text":    text,
            "passed":  bool(VERDICT_PASS.search(text)),
        })
    return attempts


def _build_executor_prompt(
    tasks_md: str,
    master_plan: str,
    workspace_path: str,
    phase_num: int,
) -> str:
    """
    Reconstruct the executor prompt from stored task/plan files.
    Mirrors the structure in ExecutorAgent.handle().
    """
    plan_snippet = master_plan[:2000] if master_plan else "(no master plan)"
    return (
        f"You are implementing Phase {phase_num} of a project.\n"
        f"IMPORTANT: Only implement Phase {phase_num} tasks below. "
        f"Do NOT implement tasks from other phases.\n\n"
        f"## Master Plan\n{plan_snippet}\n\n"
        f"## Phase {phase_num} Tasks\n{tasks_md}\n\n"
        f"## Workspace\n{workspace_path}\n"
    )


def _workspace_as_document(workspace: pathlib.Path, max_files: int = 40) -> tuple[str, list[str]]:
    """
    Serialize workspace files into a single text document for training.

    Format:
        === path/to/file.py ===
        <file contents>

    Returns (document_text, file_list).
    Skips __pycache__, .pyc, large files >50k chars.
    """
    parts: list[str] = []
    file_list: list[str] = []
    skip_patterns = ("__pycache__", ".pyc", ".egg-info", ".git")

    py_files = sorted(
        [f for f in workspace.rglob("*")
         if f.is_file()
         and not any(p in str(f) for p in skip_patterns)],
        key=lambda f: f.suffix != ".py"   # .py files first
    )[:max_files]

    for f in py_files:
        rel = str(f.relative_to(workspace))
        file_list.append(rel)
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            if len(content) > 50_000:
                content = content[:50_000] + "\n... (truncated)"
            parts.append(f"=== {rel} ===\n{content}")
        except OSError:
            parts.append(f"=== {rel} ===\n(unreadable)")

    return "\n\n".join(parts), file_list


def _count_tasks(tasks_md: str) -> int:
    """Count total tasks (checked + unchecked) in a tasks.md."""
    return len(re.findall(r"^-\s*\[[ xX]\]", tasks_md, re.MULTILINE))


def _count_passed_tasks(tasks_md: str) -> int:
    """Count checked tasks in a tasks.md."""
    return len(re.findall(r"^-\s*\[[xX]\]", tasks_md, re.MULTILINE))


def _read_safe(path: pathlib.Path, max_chars: int = 0) -> str:
    """Read a file safely, returning empty string on error."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[:max_chars] if max_chars else text
    except OSError:
        return ""


# ---------------------------------------------------------------------------
# Per-project/phase harvesting
# ---------------------------------------------------------------------------

def harvest_phase(
    proj_dir: pathlib.Path,
    phase_num: int,
    min_tasks: int = 2,
    track: str = "task",
) -> tuple[list[SFTPair], list[DPOPair]]:
    """
    Extract SFT and DPO pairs from a single project phase.

    Args:
        proj_dir:  .pipeline/projects/<slug>/
        phase_num: phase number (1-based)
        min_tasks: skip phases with fewer than this many tasks
        track:     "task" = task-level pairs, "phase" = full-phase compression

    Returns (sft_pairs, dpo_pairs) — may be empty.
    """
    sft: list[SFTPair] = []
    dpo: list[DPOPair] = []
    slug = proj_dir.name

    phase_dir = proj_dir / "phases" / f"phase_{phase_num}"
    workspace  = proj_dir / "workspace"

    if not phase_dir.exists():
        return sft, dpo

    tasks_md    = _read_safe(phase_dir / "tasks.md")
    master_plan = _read_safe(proj_dir / "state" / "master_plan.md")
    fix_report  = _read_safe(phase_dir / "fix_report.md")
    val_report  = _read_safe(phase_dir / "validation_report.md")

    if not tasks_md:
        return sft, dpo

    total_tasks  = _count_tasks(tasks_md)
    passed_tasks = _count_passed_tasks(tasks_md)

    if total_tasks < min_tasks:
        return sft, dpo

    # Use validation_report as the authority on whether the phase passed.
    # The tasks.md checkbox state is often NOT updated by the executor even
    # when the phase genuinely passed — the validator is the real signal.
    phase_passed = bool(VERDICT_PASS.search(val_report)) if val_report else False

    # For SFT: require at least 1 checked task as a sanity check that the
    # executor made some attempt, even if checkboxes aren't fully updated.
    # For DPO: we just need phase_passed + at least one fix_report attempt.
    at_least_attempted = passed_tasks >= 1 or fix_report
    if not at_least_attempted:
        return sft, dpo

    # Skip phases that definitively failed AND have no fix_report history
    if not phase_passed and not fix_report:
        return sft, dpo


    # Reconstruct the executor prompt
    prompt = _build_executor_prompt(
        tasks_md=tasks_md,
        master_plan=master_plan,
        workspace_path=str(workspace),
        phase_num=phase_num,
    )

    # Serialize winning workspace output
    if not workspace.exists():
        return sft, dpo

    chosen_doc, file_list = _workspace_as_document(workspace)
    if not chosen_doc:
        return sft, dpo

    # Parse retry history from fix_report
    # Attempts in fix_report are always failures by definition — the model
    # failed and the fix_report records each attempt. The final passing run
    # isn't recorded in fix_report; it's reflected in validation_report.
    attempts = _parse_attempts(fix_report) if fix_report else []
    passed_on_try = 1 + len(attempts)   # 1 if no retries, N+1 if N attempts failed

    # --------------- SFT pair ---------------
    sft.append(SFTPair(
        slug=slug,
        phase=phase_num,
        instruction=prompt,
        output=chosen_doc,
        tasks_count=total_tasks,
        passed_on_try=passed_on_try,
        workspace_files=file_list,
    ))

    # --------------- DPO pairs ---------------
    # Any attempt in fix_report is a "rejected" example — they all failed.
    # We only build a DPO pair when the phase ultimately passed (chosen exists).
    # Use the earliest attempt as rejected for maximum contrast with chosen.
    if attempts and phase_passed:
        earliest = attempts[0]
        rejected_text = earliest["text"]

        # Try to extract the actual test output block for a richer rejected signal
        test_block = re.search(
            r"####\s+Test Output\s*\n```(.*?)```",
            rejected_text, re.DOTALL
        )
        if test_block:
            rejected_text = test_block.group(1).strip()

        rejected_text = rejected_text[:10_000]  # cap for training context

        # Extract a concise failure reason from the test output
        failure_reason = ""
        for line in rejected_text.splitlines()[:20]:
            stripped = line.strip()
            if stripped and any(
                kw in stripped.lower()
                for kw in ("fail", "error", "missing", "wrong", "incomplete", "assert")
            ):
                failure_reason = stripped[:120]
                break

        dpo.append(DPOPair(
            slug=slug,
            phase=phase_num,
            prompt=prompt,
            chosen=chosen_doc,
            rejected=rejected_text,
            failure_reason=failure_reason,
        ))

    return sft, dpo


def harvest_all(
    projects_dir: pathlib.Path,
    status_filter: str | None = None,
    min_tasks: int = 2,
    track: str = "task",
    max_phases: int = 9,
) -> Iterator[tuple[list[SFTPair], list[DPOPair]]]:
    """
    Walk all projects and yield (sft_pairs, dpo_pairs) per phase.

    Args:
        status_filter: only include projects with this status ("complete", etc.)
        min_tasks:     skip phases with fewer tasks
        track:         "task" or "phase"
        max_phases:    maximum phase number to scan
    """
    for proj_dir in sorted(projects_dir.iterdir()):
        if not proj_dir.is_dir():
            continue

        state_file = proj_dir / "state" / "current_idea.json"
        if not state_file.exists():
            continue

        try:
            state = json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        if status_filter and state.get("status") != status_filter:
            continue

        total_phases = int(state.get("total_phases", 0))
        if total_phases == 0:
            continue

        for phase_num in range(1, min(total_phases, max_phases) + 1):
            yield harvest_phase(
                proj_dir=proj_dir,
                phase_num=phase_num,
                min_tasks=min_tasks,
                track=track,
            )


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def write_jsonl(pairs: list, path: pathlib.Path) -> int:
    """Write a list of dataclass instances as JSONL. Returns count written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(asdict(p), ensure_ascii=False) + "\n")
            written += 1
    return written


def write_alpaca_jsonl(sft_pairs: list[SFTPair], path: pathlib.Path) -> int:
    """
    Write SFT pairs in Alpaca format (instruction / input / output).
    Compatible with axolotl, LLaMA-Factory, trl SFTTrainer.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("w", encoding="utf-8") as f:
        for p in sft_pairs:
            record = {
                "instruction": (
                    "You are an expert software engineer. "
                    "Implement the following phase tasks exactly as specified, "
                    "writing all required files to the workspace."
                ),
                "input":  p.instruction,
                "output": p.output,
                # Metadata for filtering/analysis (not used by trainer)
                "_meta": {
                    "slug":          p.slug,
                    "phase":         p.phase,
                    "tasks_count":   p.tasks_count,
                    "passed_on_try": p.passed_on_try,
                    "files":         p.workspace_files,
                },
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
    return written


def write_dpo_jsonl(dpo_pairs: list[DPOPair], path: pathlib.Path) -> int:
    """
    Write DPO pairs in trl/ChatML format:
    {"prompt": ..., "chosen": ..., "rejected": ...}
    Compatible with trl DPOTrainer, axolotl dpo template.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with path.open("w", encoding="utf-8") as f:
        for p in dpo_pairs:
            record = {
                "prompt":   p.prompt,
                "chosen":   p.chosen,
                "rejected": p.rejected,
                "_meta": {
                    "slug":           p.slug,
                    "phase":          p.phase,
                    "failure_reason": p.failure_reason,
                },
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1
    return written


# ---------------------------------------------------------------------------
# Stats reporter
# ---------------------------------------------------------------------------

def print_stats(sft_pairs: list[SFTPair], dpo_pairs: list[DPOPair]) -> None:
    """Print a summary of the harvested dataset."""
    if not sft_pairs:
        print("  No SFT pairs found.")
        return

    total_tasks     = sum(p.tasks_count for p in sft_pairs)
    first_pass      = sum(1 for p in sft_pairs if p.passed_on_try == 1)
    multi_pass      = sum(1 for p in sft_pairs if p.passed_on_try > 1)
    avg_try         = sum(p.passed_on_try for p in sft_pairs) / len(sft_pairs)
    unique_projects = len(set(p.slug for p in sft_pairs))
    avg_tasks       = total_tasks / len(sft_pairs)
    avg_files       = sum(len(p.workspace_files) for p in sft_pairs) / len(sft_pairs)

    # Instruction token estimate (~4 chars per token)
    avg_prompt_tokens = sum(len(p.instruction) for p in sft_pairs) / len(sft_pairs) / 4
    avg_output_tokens = sum(len(p.output)      for p in sft_pairs) / len(sft_pairs) / 4

    SEP = "-" * 55
    print(f"\n  {SEP}")
    print(f"  SFT PAIRS")
    print(f"  {SEP}")
    print(f"  Total pairs:        {len(sft_pairs)}")
    print(f"  Unique projects:    {unique_projects}")
    print(f"  First-pass wins:    {first_pass} ({100*first_pass//len(sft_pairs)}%)")
    print(f"  Multi-pass wins:    {multi_pass} ({100*multi_pass//len(sft_pairs)}%)")
    print(f"  Avg retries:        {avg_try:.2f}")
    print(f"  Avg tasks/phase:    {avg_tasks:.1f}")
    print(f"  Avg files/phase:    {avg_files:.1f}")
    print(f"  Est prompt tokens:  ~{int(avg_prompt_tokens):,} avg")
    print(f"  Est output tokens:  ~{int(avg_output_tokens):,} avg")

    if dpo_pairs:
        print(f"\n  DPO PAIRS")
        print(f"  {SEP}")
        print(f"  Total pairs:        {len(dpo_pairs)}")
        unique_dpo = len(set(p.slug for p in dpo_pairs))
        print(f"  Unique projects:    {unique_dpo}")
        top_failures: dict[str, int] = {}
        for p in dpo_pairs:
            reason = p.failure_reason[:60] or "unknown"
            top_failures[reason] = top_failures.get(reason, 0) + 1
        print(f"  Top failure reasons:")
        for reason, count in sorted(top_failures.items(), key=lambda x: -x[1])[:5]:
            print(f"    [{count:3d}] {reason}")

    print(f"  {SEP}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Force UTF-8 output on Windows consoles
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Harvest fine-tuning data from pipeline project completions."
    )
    parser.add_argument(
        "--out-dir", default="finetune_data",
        help="Output directory for JSONL files (default: finetune_data/)"
    )
    parser.add_argument(
        "--status", default="complete",
        help="Only include projects with this status (default: complete)"
    )
    parser.add_argument(
        "--min-tasks", type=int, default=2,
        help="Skip phases with fewer than N tasks (default: 2)"
    )
    parser.add_argument(
        "--track", choices=["task", "phase"], default="task",
        help="task=task-level SFT, phase=full-phase compression (default: task)"
    )
    parser.add_argument(
        "--all-statuses", action="store_true",
        help="Include projects regardless of status"
    )
    parser.add_argument(
        "--pipeline-dir", default=None,
        help="Override .pipeline directory path"
    )
    parser.add_argument(
        "--stats-only", action="store_true",
        help="Print stats only, don't write files"
    )
    args = parser.parse_args()

    projects_dir = (
        pathlib.Path(args.pipeline_dir) / "projects"
        if args.pipeline_dir
        else _projects_dir()
    )
    if not projects_dir.exists():
        print(f"ERROR: projects dir not found: {projects_dir}")
        sys.exit(1)

    out_dir = ROOT / args.out_dir
    status_filter = None if args.all_statuses else args.status

    print(f"\n  Pipeline: {projects_dir}")
    print(f"  Filter:   status={status_filter or 'any'}, min_tasks={args.min_tasks}")
    print(f"  Track:    {args.track}")
    print(f"  Output:   {out_dir}\n")

    all_sft: list[SFTPair] = []
    all_dpo: list[DPOPair] = []
    phase_count = 0

    for sft_pairs, dpo_pairs in harvest_all(
        projects_dir=projects_dir,
        status_filter=status_filter,
        min_tasks=args.min_tasks,
        track=args.track,
    ):
        all_sft.extend(sft_pairs)
        all_dpo.extend(dpo_pairs)
        phase_count += 1
        if phase_count % 50 == 0:
            print(f"  Scanned {phase_count} phases... ({len(all_sft)} SFT, {len(all_dpo)} DPO)")

    print_stats(all_sft, all_dpo)

    if args.stats_only:
        return

    # Write outputs
    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    # 1. Raw JSONL (all metadata preserved — use for analysis/filtering)
    sft_raw   = out_dir / f"sft_raw_{now}.jsonl"
    dpo_raw   = out_dir / f"dpo_raw_{now}.jsonl"
    n_sft_raw = write_jsonl(all_sft, sft_raw)
    n_dpo_raw = write_jsonl(all_dpo, dpo_raw)

    # 2. Alpaca format (for trl SFTTrainer / axolotl)
    sft_alpaca   = out_dir / f"sft_alpaca_{now}.jsonl"
    n_sft_alpaca = write_alpaca_jsonl(all_sft, sft_alpaca)

    # 3. DPO format (for trl DPOTrainer)
    dpo_trl   = out_dir / f"dpo_trl_{now}.jsonl"
    n_dpo_trl = write_dpo_jsonl(all_dpo, dpo_trl)

    # 4. Manifest
    manifest = {
        "harvested_at":   now,
        "status_filter":  status_filter,
        "min_tasks":      args.min_tasks,
        "track":          args.track,
        "sft_pairs":      n_sft_raw,
        "dpo_pairs":      n_dpo_raw,
        "files": {
            "sft_raw":    str(sft_raw.relative_to(ROOT)),
            "sft_alpaca": str(sft_alpaca.relative_to(ROOT)),
            "dpo_raw":    str(dpo_raw.relative_to(ROOT)),
            "dpo_trl":    str(dpo_trl.relative_to(ROOT)),
        },
    }
    manifest_path = out_dir / f"manifest_{now}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"  [OK] SFT raw:    {n_sft_raw} pairs  -> {sft_raw.name}")
    print(f"  [OK] SFT alpaca: {n_sft_alpaca} pairs -> {sft_alpaca.name}")
    print(f"  [OK] DPO raw:    {n_dpo_raw} pairs  -> {dpo_raw.name}")
    print(f"  [OK] DPO trl:    {n_dpo_trl} pairs  -> {dpo_trl.name}")
    print(f"  [OK] Manifest:   {manifest_path.name}\n")


if __name__ == "__main__":
    main()
