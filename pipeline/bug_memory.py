"""
pipeline/bug_memory.py
Persistent bug resolution memory for the autonomous pipeline.

On PASS-after-retries:
    The validator calls append_resolution() with the failure pattern and fix summary.
    This writes a compact 3-field record to .pipeline/memory/bug_resolutions.jsonl.

On new phase planning:
    The phase planner calls query_relevant() with keywords from the task spec.
    Returns the top-N most relevant resolutions as a formatted context block.

Design principles:
  - Append-only JSONL — never modifies existing records, survives crashes.
  - Keyword matching — no embeddings needed; fast and deterministic.
  - Capped at MAX_RECORDS — oldest entries pruned to prevent unbounded growth.
  - Thread-safe — uses a simple file lock via the message bus's _FileLock.
"""

from __future__ import annotations

import json
import pathlib
import re
import time
from datetime import datetime, timezone
from typing import NamedTuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
PIPELINE_DIR   = _PROJECT_ROOT / ".pipeline"
MEMORY_DIR     = PIPELINE_DIR / "memory"
RESOLUTIONS_PATH = MEMORY_DIR / "bug_resolutions.jsonl"

MAX_RECORDS = 500   # prune oldest when exceeded
MAX_CONTEXT = 2000  # characters of resolution context injected into planner

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

class Resolution(NamedTuple):
    """A single bug resolution record."""
    ts:             str    # ISO timestamp
    slug:           str    # project slug
    phase:          int    # phase number
    failure_reason: str    # ≤120 chars — what went wrong
    fix_summary:    str    # ≤200 chars — what the executor did to fix it
    keywords:       list   # extracted keywords for matching
    retry_count:    int    # how many attempts before passing


# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------

_STOP_WORDS = {
    "the", "a", "an", "is", "in", "at", "of", "for", "to", "and", "or",
    "but", "not", "with", "from", "by", "on", "as", "was", "be", "it",
    "this", "that", "are", "were", "has", "have", "had", "use", "used",
    "when", "if", "then", "no", "yes", "can", "could", "should", "would",
    "will", "may", "might", "must", "shall", "does", "do", "did", "your",
    "our", "their", "its",
}

_TECH_PATTERNS = re.compile(
    r"\b("
    r"import|module|class|function|method|error|exception|assertion|"
    r"test|fixture|mock|patch|assert|raise|return|yield|async|await|"
    r"sqlalchemy|sqlite|pydantic|fastapi|flask|pytest|unittest|"
    r"windows|linux|path|file|write|read|open|close|"
    r"ModuleNotFoundError|ImportError|AttributeError|TypeError|"
    r"ValueError|RuntimeError|KeyError|IndexError|SyntaxError|"
    r"AssertionError|FileNotFoundError|PermissionError"
    r")\b",
    re.IGNORECASE,
)


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from a failure/fix description."""
    # Lowercase, split on word boundaries
    raw = re.findall(r"\b\w{3,}\b", text.lower())
    # Keep tech keywords + any word not in stop list
    keywords = []
    for word in raw:
        if word in _STOP_WORDS:
            continue
        if len(keywords) >= 20:
            break
        keywords.append(word)
    # Also add any tech pattern matches (case-preserved for error names)
    tech = _TECH_PATTERNS.findall(text)
    for t in tech:
        if t.lower() not in keywords:
            keywords.append(t.lower())
    return list(dict.fromkeys(keywords))  # deduplicate, preserve order


# ---------------------------------------------------------------------------
# File lock (reuse MessageBus lock pattern for consistency)
# ---------------------------------------------------------------------------

class _SimpleLock:
    """Minimal cross-platform file lock via a .lock sentinel file."""

    def __init__(self, path: pathlib.Path):
        self._lock = path.parent / (path.name + ".lock")

    def __enter__(self):
        deadline = time.time() + 10.0
        while True:
            try:
                self._lock.parent.mkdir(parents=True, exist_ok=True)
                self._lock.open("x").close()  # atomic create — fails if exists
                return self
            except FileExistsError:
                if time.time() > deadline:
                    # Stale lock — remove and retry
                    try:
                        self._lock.unlink()
                    except OSError:
                        pass
                time.sleep(0.05)

    def __exit__(self, *_):
        try:
            self._lock.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def append_resolution(
    slug: str,
    phase: int,
    failure_reason: str,
    fix_summary: str,
    retry_count: int,
) -> None:
    """
    Append a resolved bug to the persistent memory store.

    Called by the validator when a phase PASSes after one or more retries.
    Safe to call from multiple processes — uses file locking.

    Args:
        slug:           project slug (e.g. "csv_analyzer")
        phase:          phase number (1-based)
        failure_reason: ≤120-char description of what failed
        fix_summary:    ≤200-char description of how it was fixed
        retry_count:    number of failed attempts before final pass
    """
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)

    record = {
        "ts":             datetime.now(timezone.utc).isoformat(),
        "slug":           slug,
        "phase":          phase,
        "failure_reason": failure_reason[:120],
        "fix_summary":    fix_summary[:200],
        "keywords":       _extract_keywords(f"{failure_reason} {fix_summary}"),
        "retry_count":    retry_count,
    }

    with _SimpleLock(RESOLUTIONS_PATH):
        # Append new record
        with RESOLUTIONS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        # Prune if over limit (keep most recent MAX_RECORDS)
        _prune_if_needed()


def _prune_if_needed() -> None:
    """Keep only the most recent MAX_RECORDS entries. Called inside lock."""
    if not RESOLUTIONS_PATH.exists():
        return
    lines = RESOLUTIONS_PATH.read_text(encoding="utf-8").splitlines()
    if len(lines) > MAX_RECORDS:
        kept = lines[-MAX_RECORDS:]
        RESOLUTIONS_PATH.write_text("\n".join(kept) + "\n", encoding="utf-8")


def query_relevant(
    task_text: str,
    top_n: int = 3,
    min_score: int = 1,
) -> list[dict]:
    """
    Find the most relevant past resolutions for a given task description.

    Uses keyword overlap scoring — O(n) over records, fast enough for ≤500.

    Args:
        task_text: the task description / phase spec to match against
        top_n:     maximum number of results to return
        min_score: minimum keyword overlap required to include a result

    Returns:
        List of resolution dicts, sorted by relevance score descending.
    """
    if not RESOLUTIONS_PATH.exists():
        return []

    query_keywords = set(_extract_keywords(task_text))
    if not query_keywords:
        return []

    scored: list[tuple[int, dict]] = []

    try:
        lines = RESOLUTIONS_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue

        rec_keywords = set(rec.get("keywords", []))
        score = len(query_keywords & rec_keywords)
        if score >= min_score:
            scored.append((score, rec))

    # Sort by score desc, then by timestamp desc (most recent first on ties)
    scored.sort(key=lambda x: (x[0], x[1].get("ts", "")), reverse=True)
    return [rec for _, rec in scored[:top_n]]


def format_for_prompt(task_text: str, top_n: int = 3) -> str:
    """
    Query relevant resolutions and format them as a prompt context block.

    Returns empty string if no relevant resolutions found.
    Designed to be injected directly into the phase_planner or executor prompt.
    """
    results = query_relevant(task_text, top_n=top_n)
    if not results:
        return ""

    lines = ["## Past Bug Resolutions (from pipeline memory — use as guardrails)"]
    for i, rec in enumerate(results, 1):
        slug  = rec.get("slug", "?")
        phase = rec.get("phase", "?")
        fail  = rec.get("failure_reason", "")
        fix   = rec.get("fix_summary", "")
        retries = rec.get("retry_count", 1)
        lines.append(
            f"\n**Resolution {i}** (from {slug} phase {phase}, {retries} retries):\n"
            f"- Failed because: {fail}\n"
            f"- Fixed by: {fix}"
        )

    block = "\n".join(lines)
    # Cap to MAX_CONTEXT to avoid bloating prompts
    if len(block) > MAX_CONTEXT:
        block = block[:MAX_CONTEXT] + "\n... (truncated)"
    return block


# ---------------------------------------------------------------------------
# Stats / CLI
# ---------------------------------------------------------------------------

def print_stats() -> None:
    """Print a summary of the bug resolution memory store."""
    if not RESOLUTIONS_PATH.exists():
        print("  No bug resolutions recorded yet.")
        return

    lines = RESOLUTIONS_PATH.read_text(encoding="utf-8").splitlines()
    records = []
    for line in lines:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass

    if not records:
        print("  Bug resolution store is empty.")
        return

    unique_slugs = len({r["slug"] for r in records})
    avg_retries = sum(r.get("retry_count", 1) for r in records) / len(records)

    # Top failure patterns
    all_keywords: dict[str, int] = {}
    for r in records:
        for kw in r.get("keywords", []):
            all_keywords[kw] = all_keywords.get(kw, 0) + 1

    top_kw = sorted(all_keywords.items(), key=lambda x: -x[1])[:8]

    print(f"\n  Bug Resolution Memory: {RESOLUTIONS_PATH}")
    print(f"  Total resolutions: {len(records)}")
    print(f"  Unique projects:   {unique_slugs}")
    print(f"  Avg retries/fix:   {avg_retries:.1f}")
    print(f"  Top failure keywords: {', '.join(kw for kw, _ in top_kw)}")
    print()


if __name__ == "__main__":
    print_stats()
