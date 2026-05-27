"""
pipeline/corpus_enrichers.py
Pluggable enrichers for fine-tune corpus records (registry pattern).

Enrichers run after raw collect and before export merge. Register new hooks with:
    register_corpus_enricher("my_enricher", my_fn)
"""

from __future__ import annotations

import logging
import pathlib
import re
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

CorpusEnricherFn = Callable[[dict[str, Any], pathlib.Path], list[dict[str, Any]]]

_REGISTRY: dict[str, CorpusEnricherFn] = {}


def register_corpus_enricher(name: str, fn: CorpusEnricherFn) -> None:
    """Register a corpus enricher by name. Later registrations override same name."""
    _REGISTRY[name] = fn


def list_corpus_enrichers() -> list[str]:
    return sorted(_REGISTRY.keys())


def run_corpus_enrichers(
    record: dict[str, Any],
    project_dir: pathlib.Path,
    *,
    only: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Run all registered enrichers (or a subset) on one record.

    Each enricher returns zero or more records (may replace or expand).
    """
    current = [record]
    names = only if only is not None else list_corpus_enrichers()

    for name in names:
        fn = _REGISTRY.get(name)
        if fn is None:
            continue
        next_batch: list[dict[str, Any]] = []
        for rec in current:
            try:
                produced = fn(rec, project_dir)
                next_batch.extend(produced if produced else [rec])
            except Exception as exc:
                logger.debug("corpus enricher %s failed (non-critical): %s", name, exc)
                next_batch.append(rec)
        current = next_batch
    return current


# ---------------------------------------------------------------------------
# Stub enrichers (documented behavior; safe no-ops when inputs missing)
# ---------------------------------------------------------------------------

_ARCH_NOTE_MARKER = "keep files under"


def _read_text(path: pathlib.Path, max_chars: int = 0) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return text[:max_chars] if max_chars else text
    except OSError:
        return ""


def enrich_architecture_notes(
    record: dict[str, Any],
    project_dir: pathlib.Path,
) -> list[dict[str, Any]]:
    """
    Inject architecture constraints from master_plan.md / tasks into instruction.

    Looks for lines mentioning file-size limits (e.g. 'under 1000 lines') and
    appends a short ## Architecture Constraints section when found.
    """
    master = _read_text(project_dir / "state" / "master_plan.md", 8_000)
    if not master:
        return [record]

    constraints: list[str] = []
    for line in master.splitlines():
        low = line.lower()
        if _ARCH_NOTE_MARKER in low or "lines per file" in low or "file size" in low:
            constraints.append(line.strip())

    phase_num = record.get("phase_num")
    if phase_num:
        tasks = _read_text(project_dir / f"phases/phase_{phase_num}/tasks.md", 4_000)
        for line in tasks.splitlines():
            low = line.lower()
            if _ARCH_NOTE_MARKER in low or "refactor" in low and "split" in low:
                constraints.append(line.strip())

    if not constraints:
        return [record]

    block = "## Architecture Constraints\n" + "\n".join(f"- {c}" for c in constraints[:8])
    out = dict(record)
    instruction = out.get("instruction", "")
    if block not in instruction:
        out["instruction"] = f"{instruction.rstrip()}\n\n{block}\n"
    tags = list(out.get("enricher_tags") or [])
    if "architecture_notes" not in tags:
        tags.append("architecture_notes")
    out["enricher_tags"] = tags
    return [out]


def enrich_external_review_pair(
    record: dict[str, Any],
    project_dir: pathlib.Path,
) -> list[dict[str, Any]]:
    """
    If workspace_pre_review/ and workspace_post_review/ exist, emit an
    'Improve this code' SFT pair (before → after). Otherwise pass through.

    Snapshot dirs are populated manually or by a future external review script;
    this enricher does not invoke thermo-nuclear review.
    """
    pre_dir = project_dir / "workspace_pre_review"
    post_dir = project_dir / "workspace_post_review"
    if not pre_dir.is_dir() or not post_dir.is_dir():
        return [record]

    from pipeline.corpus_continuation import collect_workspace_files, format_workspace_block

    pre_files = collect_workspace_files(pre_dir)
    post_files = collect_workspace_files(post_dir)
    if not pre_files or not post_files:
        return [record]

    slug = record.get("source_slug") or project_dir.name
    seq = record.get("sequence_id", slug)
    pair_id = f"{slug}__external_review"

    improve_rec: dict[str, Any] = {
        "id": pair_id,
        "instruction": (
            "You are a senior engineer performing a thermo-nuclear code quality review. "
            "Refactor and split oversized files, improve structure, and add tests where missing. "
            "Preserve behavior unless the review explicitly requires a fix."
        ),
        "input": format_workspace_block(pre_files),
        "output": format_workspace_block(post_files),
        "sequence_id": f"{seq}__review",
        "part_index": 1,
        "total_parts": 1,
        "source_slug": slug,
        "granularity": "review",
        "enricher_tags": ["external_review_pair"],
        "is_continuation": False,
    }
    return [record, improve_rec]


def _register_defaults() -> None:
    register_corpus_enricher("architecture_notes", enrich_architecture_notes)
    register_corpus_enricher("external_review_pair", enrich_external_review_pair)


_register_defaults()
