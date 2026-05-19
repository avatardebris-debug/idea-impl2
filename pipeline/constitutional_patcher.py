#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline/constitutional_patcher.py
Constitutional Self-Modification -- Auto-patches agent system prompts.

Reads bug_resolutions.jsonl, identifies recurring failure patterns
(same keyword cluster appearing in 3+ distinct projects), and prepends
a "Constitutional Guardrail" block to the relevant role's prompt file.

This is second-order learning: instead of injecting guardrails per-phase at
runtime, patterns that recur often enough get baked permanently into the
agent's system prompt so they never need injecting again.

The patcher is intentionally conservative:
  - Only patches when a pattern appears in 3+ DISTINCT projects (not 3 retries
    on the same project -- that's noise, not a systemic bug)
  - Never removes existing content; only appends a new guardrail section
  - De-duplicates: won't add a guardrail that's already present (keyword match)
  - Writes a patch log so the manager can audit what changed

Usage (standalone):
    python pipeline/constitutional_patcher.py
    python pipeline/constitutional_patcher.py --dry-run
    python pipeline/constitutional_patcher.py --min-projects 2 --role executor

Called by the Manager agent's periodic health loop (every ~30 min).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT         = pathlib.Path(__file__).parent.parent.resolve()
PIPELINE_DIR = ROOT / ".pipeline"
MEMORY_DIR   = PIPELINE_DIR / "memory"
PROMPTS_DIR  = ROOT / "pipeline" / "prompts"
PATCH_LOG    = MEMORY_DIR / "constitutional_patches.jsonl"

BUG_MEMORY   = MEMORY_DIR / "bug_resolutions.jsonl"

# ---------------------------------------------------------------------------
# Role → which keywords suggest this role's prompt needs patching
# ---------------------------------------------------------------------------

# Maps role names (matching prompts/*.md filenames without extension) to keyword
# clusters that indicate the failure is in that role's output.
ROLE_KEYWORD_MAP: dict[str, set[str]] = {
    "executor": {
        "importerror", "modulenotfounderror", "syntaxerror", "nameerror",
        "filenotfounderror", "permissionerror", "sqlite", "tempfile",
        "workspace", "stub", "placeholder", "todo", "missing", "incomplete",
        "checkbox", "tasks", "patch_file", "write_file", "wrong path",
        "double", "nesting",
    },
    "validator": {
        "verdict", "assertion", "assertionerror", "test", "pytest",
        "conftest", "fixture", "import", "validation", "fail",
    },
    "phase_planner": {
        "planner", "tasks.md", "phase", "task format", "heading",
        "bullet", "checkbox",
    },
    "reviewer": {
        "review", "reviewer", "quality", "incomplete review",
    },
}

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

@dataclass
class PatternCluster:
    """A recurring failure pattern identified across multiple projects."""
    keywords:      frozenset[str]
    slug_set:      frozenset[str]   # distinct project slugs affected
    resolutions:   list[dict]       # raw resolution records
    role:          str              # which prompt to patch
    guardrail_text: str             # the text to add


class PatchRecord(NamedTuple):
    role:      str
    pattern:   str     # human-readable summary of the pattern
    guardrail: str     # exact text added
    patched_at: str    # ISO timestamp
    projects:  list[str]


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _load_resolutions() -> list[dict]:
    """Load all records from bug_resolutions.jsonl."""
    if not BUG_MEMORY.exists():
        return []
    records = []
    for line in BUG_MEMORY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except Exception:
            pass
    return records


def _cluster_by_keywords(records: list[dict]) -> dict[str, list[dict]]:
    """
    Group records by their most prominent keyword.

    For each record, pick the keyword with the highest tf-simple frequency
    across all records (the one that distinguishes this failure class).
    Returns {dominant_keyword: [records...]}.
    """
    # Count keyword frequency across all records
    freq: dict[str, int] = defaultdict(int)
    for rec in records:
        for kw in rec.get("keywords", []):
            freq[kw] += 1

    # For each record, find its "dominant" keyword (highest frequency)
    clusters: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        kws = rec.get("keywords", [])
        if not kws:
            continue
        dominant = max(kws, key=lambda k: freq.get(k, 0), default=None)
        if dominant:
            clusters[dominant].append(rec)
    return clusters


def _infer_role(keywords: list[str]) -> str:
    """
    Map a record's keyword list to the most-likely responsible agent role.
    Falls back to 'executor' since that's the most common failure source.
    """
    kw_set = set(k.lower() for k in keywords)
    best_role = "executor"
    best_score = 0
    for role, role_kws in ROLE_KEYWORD_MAP.items():
        score = len(kw_set & role_kws)
        if score > best_score:
            best_score = score
            best_role = role
    return best_role


def _build_guardrail(cluster_kw: str, records: list[dict]) -> str:
    """
    Build a CRITICAL GUARDRAIL block from a cluster of related failures.

    The guardrail is formatted as a tight bullet point that can be inserted
    into any prompt/*.md file in the "What NOT to do" or "Rules" section.
    """
    # Summarize the most common fix
    fix_counts: dict[str, int] = defaultdict(int)
    for rec in records:
        fix = rec.get("fix_summary", "").strip()
        if fix:
            fix_counts[fix[:120]] += 1

    if fix_counts:
        top_fix = max(fix_counts, key=fix_counts.__getitem__)
    else:
        top_fix = "See bug_resolutions.jsonl for fix details."

    # Summarize the most common failure
    fail_counts: dict[str, int] = defaultdict(int)
    for rec in records:
        fail = rec.get("failure_reason", "").strip()
        if fail:
            fail_counts[fail[:120]] += 1

    top_fail = max(fail_counts, key=fail_counts.__getitem__) if fail_counts else cluster_kw

    n_projects = len(set(r.get("slug", "") for r in records))
    avg_retries = sum(r.get("retry_count", 1) for r in records) / len(records)

    return (
        f"- **CRITICAL GUARDRAIL [{cluster_kw.upper()}]** "
        f"(pattern seen in {n_projects} projects, avg {avg_retries:.1f} retries): "
        f"*Problem*: {top_fail}. "
        f"*Fix*: {top_fix}."
    )


def _guardrail_already_present(prompt_text: str, guardrail_keyword: str) -> bool:
    """Return True if this guardrail's keyword cluster is already in the prompt."""
    marker = f"CRITICAL GUARDRAIL [{guardrail_keyword.upper()}]"
    return marker in prompt_text


def _append_guardrail_to_prompt(
    role: str,
    guardrail: str,
    dry_run: bool = False,
) -> bool:
    """
    Append a guardrail bullet to the relevant prompts/<role>.md file.

    Inserts into the "What NOT to do" section if present, otherwise appends
    a new "## Constitutional Guardrails" section at the end of the file.

    Returns True if the file was (or would be) modified.
    """
    prompt_file = PROMPTS_DIR / f"{role}.md"
    if not prompt_file.exists():
        return False

    text = prompt_file.read_text(encoding="utf-8")

    # Extract guardrail keyword for dedup check
    kw_match = re.search(r"CRITICAL GUARDRAIL \[([^\]]+)\]", guardrail)
    if kw_match and _guardrail_already_present(text, kw_match.group(1)):
        return False  # already patched

    # Find the "What NOT to do" section to insert under, or append a new section
    not_do_match = re.search(r"(^##\s+What NOT to do.*?\n)", text, re.MULTILINE)

    if not dry_run:
        if not_do_match:
            # Insert the guardrail as the first item in that section
            insert_pos = not_do_match.end()
            new_text = text[:insert_pos] + guardrail + "\n" + text[insert_pos:]
        else:
            # Append a new section
            new_text = (
                text.rstrip() + "\n\n"
                "## Constitutional Guardrails\n"
                "*Auto-patched by constitutional_patcher.py based on recurring failures.*\n"
                + guardrail + "\n"
            )
        prompt_file.write_text(new_text, encoding="utf-8")

    return True


def run_patcher(
    min_projects: int = 3,
    role_filter: str | None = None,
    dry_run: bool = False,
    verbose: bool = True,
) -> list[PatchRecord]:
    """
    Main entry point: scan bug memory, find patterns, patch prompts.

    Args:
        min_projects: minimum distinct projects for a pattern to warrant patching
        role_filter:  if set, only patch this role's prompt
        dry_run:      analyze but don't write
        verbose:      print progress

    Returns list of PatchRecord for all applied (or would-be applied) patches.
    """
    records = _load_resolutions()
    if not records:
        if verbose:
            print("  [constitutional] No bug resolutions found — nothing to patch.")
        return []

    if verbose:
        print(f"  [constitutional] Loaded {len(records)} bug resolution(s)")

    clusters = _cluster_by_keywords(records)
    patches: list[PatchRecord] = []

    for cluster_kw, cluster_records in sorted(clusters.items()):
        # Filter: must appear in enough DISTINCT projects
        slugs = set(r.get("slug", "") for r in cluster_records)
        if len(slugs) < min_projects:
            continue

        # Determine which role's prompt to patch
        all_kws = []
        for r in cluster_records:
            all_kws.extend(r.get("keywords", []))
        role = _infer_role(all_kws)

        if role_filter and role != role_filter:
            continue

        # Build the guardrail text
        guardrail = _build_guardrail(cluster_kw, cluster_records)

        # Try to patch the prompt
        patched = _append_guardrail_to_prompt(role, guardrail, dry_run=dry_run)
        if not patched:
            if verbose:
                print(f"  [constitutional] SKIP [{cluster_kw}] → {role}.md "
                      f"(already present or file missing)")
            continue

        # Record the patch
        patch = PatchRecord(
            role=role,
            pattern=cluster_kw,
            guardrail=guardrail,
            patched_at=datetime.now(timezone.utc).isoformat(),
            projects=sorted(slugs),
        )
        patches.append(patch)

        # Persist to patch log
        if not dry_run:
            PATCH_LOG.parent.mkdir(parents=True, exist_ok=True)
            with PATCH_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "role":      patch.role,
                    "pattern":   patch.pattern,
                    "guardrail": patch.guardrail,
                    "patched_at": patch.patched_at,
                    "projects":  patch.projects,
                }) + "\n")

        action = "DRY-RUN" if dry_run else "PATCHED"
        if verbose:
            print(f"  [constitutional] {action} [{cluster_kw}] -> {role}.md "
                  f"({len(slugs)} projects)")
            if verbose and dry_run:
                print(f"    {guardrail}")

    if verbose:
        if patches:
            print(f"  [constitutional] Applied {len(patches)} constitutional patch(es)")
        else:
            print(f"  [constitutional] No new patterns met the threshold "
                  f"(min_projects={min_projects})")

    return patches


def print_patch_log() -> None:
    """Print all previously applied patches."""
    if not PATCH_LOG.exists():
        print("  No constitutional patches applied yet.")
        return
    records = []
    for line in PATCH_LOG.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except Exception:
                pass
    if not records:
        print("  Patch log is empty.")
        return

    SEP = "-" * 55
    print(f"\n  {SEP}")
    print(f"  CONSTITUTIONAL PATCHES ({len(records)} total)")
    print(f"  {SEP}")
    for r in records:
        print(f"  [{r.get('patched_at','?')[:10]}] {r.get('role','?')}.md "
              f"  pattern={r.get('pattern','?')} "
              f"({len(r.get('projects',[]))} projects)")
        print(f"    {r.get('guardrail','')[:100]}")
    print(f"  {SEP}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Patch agent system prompts with recurring failure patterns",
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Analyze but don't write prompt files")
    parser.add_argument("--min-projects", type=int, default=3,
                        help="Minimum distinct projects for pattern to trigger patch (default: 3)")
    parser.add_argument("--role", default=None,
                        choices=list(ROLE_KEYWORD_MAP.keys()),
                        help="Only patch this role's prompt (default: all roles)")
    parser.add_argument("--log", action="store_true",
                        help="Print patch log and exit")
    args = parser.parse_args()

    # Force UTF-8 output on Windows consoles
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    if args.log:
        print_patch_log()
        return

    patches = run_patcher(
        min_projects=args.min_projects,
        role_filter=args.role,
        dry_run=args.dry_run,
        verbose=True,
    )

    if patches and not args.dry_run:
        print(f"\n  Patches written to prompts/ — restart the pipeline to activate.\n")


if __name__ == "__main__":
    main()
