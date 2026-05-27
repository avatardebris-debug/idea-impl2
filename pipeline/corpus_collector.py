"""
pipeline/corpus_collector.py
Fine-tune corpus collector for the autonomous pipeline.

Emits three granularities of (input -> output) training pairs:

  task    -- one entry per phase (description + phase spec -> code files)
  phase   -- same as task but includes the full master_plan context window
  project -- one entry per completed project (description -> all code across phases)

All pairs include quality signals from the validator and reviewer so the
fine-tune trainer can filter/weight samples without manual labeling.

Usage:
    # Called automatically on every project completion (hooked into _mark_complete)
    from pipeline.corpus_collector import collect_project_on_complete
    collect_project_on_complete(project_dir, state)

    # Retroactive harvest of all already-completed projects
    python -m pipeline.corpus_collector --collect-all

    # Show corpus stats
    python -m pipeline.corpus_collector --stats
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import pathlib
import re
import sys
import textwrap
from typing import Any

# Timezone-aware UTC helper (avoids deprecated utcnow())
_UTC = datetime.timezone.utc
def _utcnow() -> str:
    return datetime.datetime.now(_UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

from pipeline.paths import finetune_corpus_dir, projects_dir
from pipeline.pipeline_config import PROJECT_ROOT


def _corpus_dir() -> pathlib.Path:
    return finetune_corpus_dir()


def _raw_dir() -> pathlib.Path:
    return _corpus_dir() / "raw"


def _task_dir() -> pathlib.Path:
    return _raw_dir() / "task"


def _phase_dir() -> pathlib.Path:
    return _raw_dir() / "phase"


def _project_corpus_dir() -> pathlib.Path:
    return _raw_dir() / "project"

# Legacy hard limits (used only when use_continuation=False)
_MAX_FILE_CHARS = 8_000
_MAX_CODE_CHARS = 40_000   # total code block per pair

# Continuation chunking defaults (see corpus_continuation.py)
_DEFAULT_MAX_OUTPUT = 12_000
_DEFAULT_MAX_INPUT_CONTINUE = 2_000


# ---------------------------------------------------------------------------
# Quality label heuristic
# ---------------------------------------------------------------------------

def _quality_label(retry_count: int, test_verdict: str, review_verdict: str) -> str:
    """
    clean    — passed first try, no blocking bugs
    patched  — needed 1-2 retries but eventually passed
    struggled — 3+ retries or force-advanced
    """
    if test_verdict != "PASS" or review_verdict != "PASS":
        return "struggled"
    if retry_count == 0:
        return "clean"
    if retry_count <= 2:
        return "patched"
    return "struggled"


# ---------------------------------------------------------------------------
# File readers
# ---------------------------------------------------------------------------

def _read(path: pathlib.Path, max_chars: int = 0) -> str:
    """Read a text file safely, returning '' on error."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        if max_chars and len(text) > max_chars:
            text = text[:max_chars] + f"\n... [truncated at {max_chars} chars]"
        return text
    except Exception:
        return ""


def _read_state(project_dir: pathlib.Path, rel: str, max_chars: int = 0) -> str:
    return _read(project_dir / rel, max_chars)


def _collect_workspace_code(
    workspace: pathlib.Path,
    *,
    max_file_chars: int = 0,
) -> dict[str, str]:
    """Return {relative_path: code_content} for all .py files in workspace."""
    files: dict[str, str] = {}
    if not workspace.exists():
        return files
    for py in sorted(workspace.rglob("*.py")):
        # Skip __pycache__ and compiled artefacts
        if "__pycache__" in py.parts:
            continue
        rel = py.relative_to(workspace).as_posix()
        files[rel] = _read(py, max_file_chars)
    return files


def _format_code_block(files: dict[str, str], max_total: int = _MAX_CODE_CHARS) -> str:
    """Format workspace files as a single structured code block."""
    parts: list[str] = []
    total = 0
    for rel, code in files.items():
        chunk = f"### {rel}\n```python\n{code}\n```\n"
        if total + len(chunk) > max_total:
            parts.append(f"### (remaining files truncated — {max_total} char limit)\n")
            break
        parts.append(chunk)
        total += len(chunk)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Per-phase extraction
# ---------------------------------------------------------------------------

def _extract_phase_pair(
    project_dir: pathlib.Path,
    state: dict,
    phase_num: int,
    master_plan: str,
) -> dict[str, Any] | None:
    """
    Extract training pair data for a single phase.
    Returns None if required files are missing.
    """
    slug         = state.get("_slug") or project_dir.name
    title        = state.get("title", slug)
    description  = state.get("description", "")
    model        = os.environ.get("PIPELINE_MODEL", "unknown")
    provider     = os.environ.get("PIPELINE_PROVIDER", "ollama")

    tasks_md     = _read_state(project_dir, f"phases/phase_{phase_num}/tasks.md",     8_000)
    spec_md      = _read_state(project_dir, f"phases/phase_{phase_num}/spec.md",      4_000)
    val_report   = _read_state(project_dir, f"phases/phase_{phase_num}/validation_report.md", 3_000)
    review_md    = _read_state(project_dir, f"phases/phase_{phase_num}/review.md",    3_000)
    fix_report   = _read_state(project_dir, f"phases/phase_{phase_num}/fix_report.md", 2_000)

    # Must have tasks to be useful
    if not tasks_md:
        return None

    # Workspace code (full files; chunking happens at Alpaca export)
    workspace    = project_dir / "workspace"
    code_files   = _collect_workspace_code(workspace, max_file_chars=0)
    code_block   = _format_code_block(code_files)  # legacy single-block preview

    # Parse verdicts
    test_verdict   = "PASS" if "Verdict: PASS" in val_report else ("FAIL" if val_report else "UNKNOWN")
    review_verdict = "PASS" if re.search(r"Verdict\s*\n\s*PASS", review_md, re.IGNORECASE) else (
                     "PASS" if "## Verdict\nPASS" in review_md else (
                     "PASS" if "Verdict: PASS" in review_md else (
                     "FAIL" if review_md else "UNKNOWN")))

    # Count retries from fix_report
    retry_count = len(re.findall(r"^### Attempt \d+", fix_report, re.MULTILINE))

    # Count blocking bugs
    m = re.search(r"## Blocking Bugs(.*?)(?=##|$)", review_md, re.DOTALL | re.IGNORECASE)
    if m:
        section = m.group(1)
        if re.search(r"\bnone\b", section, re.IGNORECASE):
            blocking_bugs = 0
        else:
            blocking_bugs = len(re.findall(r"^[-*]\s+", section, re.MULTILINE))
    else:
        blocking_bugs = 0

    quality = _quality_label(retry_count, test_verdict, review_verdict)

    pair_id = f"{slug}__p{phase_num}"

    return {
        "id":               pair_id,
        "type":             "task",          # task-level granularity
        "project_slug":     slug,
        "project_title":    title,
        "project_description": description,
        "phase_num":        phase_num,
        "total_phases":     state.get("total_phases", 1),
        # ── inputs ──
        "master_plan":      master_plan[:3000] if master_plan else "",
        "phase_spec":       spec_md,
        "tasks":            tasks_md,
        # ── output ──
        "code":             code_block,
        "code_files":       list(code_files.keys()),
        # ── quality signals ──
        "test_verdict":     test_verdict,
        "review_verdict":   review_verdict,
        "blocking_bugs":    blocking_bugs,
        "retry_count":      retry_count,
        "quality_label":    quality,
        # ── metadata ──
        "model":            model,
        "provider":         provider,
        "collected_at":     _utcnow(),
    }


# ---------------------------------------------------------------------------
# Alpaca-format builders
# ---------------------------------------------------------------------------

def _task_instruction(pair: dict) -> str:
    return textwrap.dedent(f"""\
        You are a senior software engineer. Write production-quality Python code for the following task.

        ## Project: {pair["project_title"]}
        {pair["project_description"]}

        ## Phase {pair["phase_num"]} of {pair["total_phases"]}
        {"## Phase Spec\n" + pair["phase_spec"] if pair["phase_spec"] else ""}

        ## Tasks & Acceptance Criteria
        {pair["tasks"]}
    """).strip()


def _phase_instruction(pair: dict) -> str:
    ctx = ""
    if pair["master_plan"]:
        ctx = f"\n## Full Project Master Plan\n{pair['master_plan']}\n"

    return textwrap.dedent(f"""\
        You are a senior software engineer implementing one phase of a larger project.

        ## Project: {pair["project_title"]}
        {pair["project_description"]}
        {ctx}
        ## Phase {pair["phase_num"]} of {pair["total_phases"]}
        {"## Phase Spec\n" + pair["phase_spec"] if pair["phase_spec"] else ""}

        ## Tasks & Acceptance Criteria
        {pair["tasks"]}

        Write all code files needed to complete this phase. Format as:
        ### filename.py
        ```python
        <code>
        ```
    """).strip()


def _shared_alpaca_fields(pair: dict) -> dict[str, Any]:
    return {
        "quality_label": pair["quality_label"],
        "retry_count":   pair["retry_count"],
        "model":         pair["model"],
        "collected_at":  pair["collected_at"],
        "phase_num":     pair["phase_num"],
        "project_slug":  pair["project_slug"],
    }


def _to_task_alpaca(pair: dict, *, use_continuation: bool = True) -> list[dict]:
    """Convert a task-level pair to one or more Alpaca records."""
    instruction = _task_instruction(pair)
    shared = _shared_alpaca_fields(pair)

    if not use_continuation:
        rec = {
            "id": pair["id"],
            "instruction": instruction,
            "input": "",
            "output": pair["code"],
            **shared,
        }
        return [rec]

    from pipeline.corpus_continuation import chunk_workspace_to_records

    workspace = pair.get("_workspace_path")
    code_files = pair.get("code_files_map") or {}
    if workspace is not None:
        return chunk_workspace_to_records(
            workspace,
            instruction,
            input="",
            max_chars_per_output=_DEFAULT_MAX_OUTPUT,
            max_chars_per_input_continue=_DEFAULT_MAX_INPUT_CONTINUE,
            sequence_id=pair["id"],
            source_slug=pair["project_slug"],
            granularity="task",
            base_id=pair["id"],
            extra_fields=shared,
        )
    from pipeline.corpus_continuation import records_from_code_block

    return records_from_code_block(
        pair["code"],
        instruction,
        input="",
        max_chars_per_output=_DEFAULT_MAX_OUTPUT,
        max_chars_per_input_continue=_DEFAULT_MAX_INPUT_CONTINUE,
        sequence_id=pair["id"],
        source_slug=pair["project_slug"],
        granularity="task",
        base_id=pair["id"],
        extra_fields=shared,
    )


def _to_phase_alpaca(pair: dict, *, use_continuation: bool = True) -> list[dict]:
    """Phase-level pair includes master_plan in the instruction context."""
    instruction = _phase_instruction(pair)
    shared = _shared_alpaca_fields(pair)
    base_id = f"{pair['id']}_phase"

    if not use_continuation:
        return [{
            "id": base_id,
            "instruction": instruction,
            "input": "",
            "output": pair["code"],
            **shared,
        }]

    from pipeline.corpus_continuation import chunk_workspace_to_records

    workspace = pair.get("_workspace_path")
    if workspace is not None:
        return chunk_workspace_to_records(
            workspace,
            instruction,
            input="",
            max_chars_per_output=_DEFAULT_MAX_OUTPUT,
            max_chars_per_input_continue=_DEFAULT_MAX_INPUT_CONTINUE,
            sequence_id=base_id,
            source_slug=pair["project_slug"],
            granularity="phase",
            base_id=base_id,
            extra_fields=shared,
        )
    from pipeline.corpus_continuation import records_from_code_block

    return records_from_code_block(
        pair["code"],
        instruction,
        input="",
        max_chars_per_output=_DEFAULT_MAX_OUTPUT,
        max_chars_per_input_continue=_DEFAULT_MAX_INPUT_CONTINUE,
        sequence_id=base_id,
        source_slug=pair["project_slug"],
        granularity="phase",
        base_id=base_id,
        extra_fields=shared,
    )


def _to_project_alpaca(
    slug: str,
    state: dict,
    all_phase_pairs: list[dict],
    *,
    use_continuation: bool = True,
) -> list[dict]:
    """Project-level pair: description → all code across all phases."""
    if not all_phase_pairs:
        return []

    title       = state.get("title", slug)
    description = state.get("description", "")
    model       = os.environ.get("PIPELINE_MODEL", "unknown")

    # Concatenate all phase code blocks (full content when use_continuation)
    combined_code_parts: list[str] = []
    total_chars = 0
    for pair in sorted(all_phase_pairs, key=lambda p: p["phase_num"]):
        header = f"## Phase {pair['phase_num']}: {pair['tasks'][:120].splitlines()[0]}\n"
        block  = header + pair["code"]
        if not use_continuation and total_chars + len(block) > _MAX_CODE_CHARS * 2:
            combined_code_parts.append("## [remaining phases truncated]\n")
            break
        combined_code_parts.append(block)
        total_chars += len(block)

    combined_code = "\n\n".join(combined_code_parts)

    # Aggregate quality
    labels = [p["quality_label"] for p in all_phase_pairs]
    if all(l == "clean" for l in labels):
        quality = "clean"
    elif any(l == "struggled" for l in labels):
        quality = "struggled"
    else:
        quality = "patched"

    avg_retries = sum(p["retry_count"] for p in all_phase_pairs) / max(len(all_phase_pairs), 1)

    instruction = textwrap.dedent(f"""\
        You are a senior software engineer. Build a complete Python project from the following specification.

        ## Project: {title}
        {description}

        Write all source files, tests, and a requirements.txt. Format output as:
        ### path/to/file.py
        ```python
        <code>
        ```
    """).strip()

    base_id = f"{slug}__project"
    shared = {
        "quality_label": quality,
        "avg_retries":   round(avg_retries, 2),
        "total_phases":  state.get("total_phases", len(all_phase_pairs)),
        "final_status":  state.get("status", "unknown"),
        "model":         model,
        "collected_at":  _utcnow(),
        "project_slug":  slug,
    }

    if not use_continuation:
        return [{
            "id": base_id,
            "instruction": instruction,
            "input": "",
            "output": combined_code,
            **shared,
        }]

    from pipeline.corpus_continuation import records_from_code_block

    return records_from_code_block(
        combined_code,
        instruction,
        input="",
        max_chars_per_output=_DEFAULT_MAX_OUTPUT,
        max_chars_per_input_continue=_DEFAULT_MAX_INPUT_CONTINUE,
        sequence_id=base_id,
        source_slug=slug,
        granularity="project",
        base_id=base_id,
        extra_fields=shared,
    )


# ---------------------------------------------------------------------------
# JSONL writers
# ---------------------------------------------------------------------------

def _append_jsonl(path: pathlib.Path, record: dict) -> None:
    """Append a single record to a JSONL file, creating it if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def _already_collected(path: pathlib.Path, record_id: str) -> bool:
    """Check if a record id already exists in a JSONL file (dedup guard)."""
    if not path.exists():
        return False
    needle = f'"id": "{record_id}"'
    try:
        content = path.read_text(encoding="utf-8")
        return needle in content
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def collect_project(
    project_dir: pathlib.Path,
    state: dict | None = None,
    *,
    use_continuation: bool = True,
    run_enrichers: bool = False,
    enricher_names: list[str] | None = None,
) -> int:
    """
    Collect fine-tune pairs from a single project directory.

    Args:
        project_dir:  Path to the project (e.g. .pipeline/projects/csv_analyzer)
        state:        Pre-loaded current_idea.json dict (loaded from disk if None)

    Returns:
        Number of new pairs written.
    """
    if state is None:
        state_path = project_dir / "state" / "current_idea.json"
        if not state_path.exists():
            return 0
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("corpus_collector: failed to read %s: %s", state_path, e)
            return 0

    slug         = state.get("_slug") or project_dir.name
    final_status = state.get("status", "")
    total_phases = state.get("total_phases", 1)

    # Only collect from terminal states — in-progress projects have incomplete code
    if final_status not in ("complete", "budget_exceeded"):
        return 0

    master_plan = _read_state(project_dir, "state/master_plan.md", 4_000)

    # Output JSONL file paths keyed by slug
    task_file    = _task_dir()    / f"{slug}.jsonl"
    phase_file   = _phase_dir()   / f"{slug}.jsonl"
    project_file = _project_corpus_dir() / f"{slug}.jsonl"

    written      = 0
    phase_pairs: list[dict] = []

    workspace_path = project_dir / "workspace"

    for phase_num in range(1, total_phases + 1):
        pair = _extract_phase_pair(project_dir, state, phase_num, master_plan)
        if not pair:
            continue
        pair["_workspace_path"] = workspace_path
        pair["code_files_map"] = _collect_workspace_code(workspace_path, max_file_chars=0)
        if use_continuation:
            from pipeline.corpus_continuation import format_workspace_block
            pair["code"] = format_workspace_block(pair["code_files_map"])
        phase_pairs.append(pair)

        def _write_records(path: pathlib.Path, records: list[dict]) -> int:
            n = 0
            for rec in records:
                batch = [rec]
                if run_enrichers:
                    from pipeline.corpus_enrichers import run_corpus_enrichers
                    batch = run_corpus_enrichers(rec, project_dir, only=enricher_names)
                for out_rec in batch:
                    if not _already_collected(path, out_rec["id"]):
                        _append_jsonl(path, out_rec)
                        n += 1
            return n

        written += _write_records(
            task_file,
            _to_task_alpaca(pair, use_continuation=use_continuation),
        )
        written += _write_records(
            phase_file,
            _to_phase_alpaca(pair, use_continuation=use_continuation),
        )

    # --- Project-level pair ---
    if phase_pairs:
        for proj_rec in _to_project_alpaca(
            slug, state, phase_pairs, use_continuation=use_continuation
        ):
            batch = [proj_rec]
            if run_enrichers:
                from pipeline.corpus_enrichers import run_corpus_enrichers
                batch = run_corpus_enrichers(proj_rec, project_dir, only=enricher_names)
            for out_rec in batch:
                if not _already_collected(project_file, out_rec["id"]):
                    _append_jsonl(project_file, out_rec)
                    written += 1

    if written:
        logger.info(
            "corpus_collector: %s → %d new pairs (task=%d phase=%d project=%d)",
            slug, written,
            len(phase_pairs),      # task pairs
            len(phase_pairs),      # phase pairs (same count)
            1 if phase_pairs else 0,
        )
    return written


def collect_project_on_complete(project_dir: pathlib.Path, state: dict) -> None:
    """
    Lightweight wrapper called from runner._mark_complete().
    Fires asynchronously-safe (no exceptions bubble up to caller).
    """
    try:
        n = collect_project(project_dir, state)
        if n:
            print(f"  [corpus] +{n} fine-tune pairs -> {_raw_dir()}")
            from pipeline.pipeline_activity import log_activity, maybe_sync_output_repo

            log_activity(
                "corpus_collected",
                slug=project_dir.name,
                pairs_added=n,
                corpus_dir=str(_raw_dir()),
            )
            maybe_sync_output_repo(f"corpus: {project_dir.name} (+{n} pairs)")
    except Exception as exc:
        logger.debug("corpus_collector.collect_project_on_complete failed (non-critical): %s", exc)


# ---------------------------------------------------------------------------
# Retroactive batch collection
# ---------------------------------------------------------------------------

def collect_all_existing(
    verbose: bool = True,
    *,
    use_continuation: bool = True,
    run_enrichers: bool = False,
) -> dict[str, int]:
    """
    Scan all project directories and collect pairs from every terminal project.
    Safe to re-run — existing records are skipped (dedup by id).

    Returns:
        {slug: pairs_written}
    """
    results: dict[str, int] = {}
    if not projects_dir().exists():
        print(f"No projects directory found at {projects_dir()}")
        return results

    dirs = sorted(p for p in projects_dir().iterdir() if p.is_dir())
    print(f"Scanning {len(dirs)} project directories...")

    total_written = 0
    for project_dir in dirs:
        state_path = project_dir / "state" / "current_idea.json"
        if not state_path.exists():
            continue
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        status = state.get("status", "")
        if status not in ("complete", "budget_exceeded"):
            if verbose:
                print(f"  skip {project_dir.name} (status={status})")
            continue

        n = collect_project(
            project_dir,
            state,
            use_continuation=use_continuation,
            run_enrichers=run_enrichers,
        )
        results[project_dir.name] = n
        total_written += n
        if verbose:
            marker = "[ok]" if state.get("status") == "complete" else "[be]"
            print(f"  {marker} {project_dir.name}: +{n} pairs")

    print(f"\nDone. Total new pairs written: {total_written}")
    print(f"Corpus: {_raw_dir()}")
    return results


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

def corpus_stats() -> None:
    """Print a summary of the current corpus."""
    if not _raw_dir().exists():
        print("No corpus yet. Run --collect-all to build it.")
        return

    total_records    = 0
    quality_counts: dict[str, int] = {}
    model_counts: dict[str, int]   = {}

    for jsonl_file in _raw_dir().rglob("*.jsonl"):
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

    task_count    = sum(1 for _ in _task_dir().glob("*.jsonl"))    if _task_dir().exists()    else 0
    phase_count   = sum(1 for _ in _phase_dir().glob("*.jsonl"))   if _phase_dir().exists()   else 0
    project_count = sum(1 for _ in _project_corpus_dir().glob("*.jsonl")) if _project_corpus_dir().exists() else 0

    print(f"\n{'='*50}")
    print(f"  Fine-Tune Corpus Stats")
    print(f"{'='*50}")
    print(f"  Total records:   {total_records}")
    print(f"  Task files:      {task_count}   -> {_task_dir()}")
    print(f"  Phase files:     {phase_count}   -> {_phase_dir()}")
    print(f"  Project files:   {project_count}   -> {_project_corpus_dir()}")
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


# ---------------------------------------------------------------------------
# Merge to single training file
# ---------------------------------------------------------------------------

def merge_corpus(
    granularity: str = "task",
    filter_quality: list[str] | None = None,
    output_path: pathlib.Path | None = None,
) -> pathlib.Path:
    """
    Merge all JSONL files of the given granularity into a single file
    ready for trl sft.

    Args:
        granularity:    "task", "phase", or "project"
        filter_quality: Only include records with these quality labels.
                        Default: ["clean", "patched"] (excludes "struggled")
        output_path:    Where to write. Default: _corpus_dir()/sft_{granularity}.jsonl

    Returns:
        Path to the merged file.
    """
    if filter_quality is None:
        filter_quality = ["clean", "patched"]

    src_dir = {"task": _task_dir(), "phase": _phase_dir(), "project": _project_corpus_dir()}.get(granularity)
    if src_dir is None:
        raise ValueError(f"Unknown granularity: {granularity}")

    if output_path is None:
        _corpus_dir().mkdir(parents=True, exist_ok=True)
        output_path = _corpus_dir() / f"sft_{granularity}.jsonl"

    written = 0
    seen_ids: set[str] = set()

    with output_path.open("w", encoding="utf-8") as out:
        for jsonl_file in sorted(src_dir.glob("*.jsonl")):
            for line in jsonl_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if rec.get("id") in seen_ids:
                        continue
                    if filter_quality and rec.get("quality_label") not in filter_quality:
                        continue
                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    seen_ids.add(rec["id"])
                    written += 1
                except Exception:
                    pass

    print(f"Merged {written} {granularity}-level records -> {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cli() -> None:
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [corpus] %(message)s")

    parser = argparse.ArgumentParser(
        description="Pipeline fine-tune corpus collector",
    )
    parser.add_argument(
        "--collect-all",
        action="store_true",
        help="Retroactively collect pairs from all completed projects",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print corpus statistics",
    )
    parser.add_argument(
        "--merge",
        choices=["task", "phase", "project"],
        help="Merge all JSONL files of given granularity into a single sft_<type>.jsonl",
    )
    parser.add_argument(
        "--quality",
        nargs="+",
        default=["clean", "patched"],
        help="Quality labels to include when merging (default: clean patched)",
    )
    parser.add_argument(
        "--project",
        metavar="SLUG",
        help="Collect from a single project slug",
    )
    parser.add_argument(
        "--no-continuation",
        action="store_true",
        help="Use legacy hard truncation (8k/file, 40k/phase) instead of continuation chains",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="Run registered corpus enrichers (architecture_notes, external_review_pair, ...)",
    )
    args = parser.parse_args()

    use_cont = not args.no_continuation

    if args.collect_all:
        collect_all_existing(verbose=True, use_continuation=use_cont, run_enrichers=args.enrich)

    if args.project:
        project_dir = projects_dir() / args.project
        if not project_dir.exists():
            print(f"Project not found: {project_dir}")
            sys.exit(1)
        n = collect_project(
            project_dir,
            use_continuation=use_cont,
            run_enrichers=args.enrich,
        )
        print(f"Collected {n} records from {args.project}")

    if args.merge:
        merge_corpus(granularity=args.merge, filter_quality=args.quality)

    if args.stats:
        corpus_stats()

    if not any([args.collect_all, args.project, args.merge, args.stats]):
        parser.print_help()


if __name__ == "__main__":
    _cli()
