"""
pipeline/bug_memory.py
Persistent bug resolution memory for the autonomous pipeline.

On PASS-after-retries:
    Validator calls record_validator_pass() — pytest/fix_report signatures.

On review blocking bugs (pre-validation):
    Reviewer calls append_mistake() for each blocking bullet.

On executor fix loops:
    format_for_fix_loop() injects top-N relevant records into the prompt.

On new phase planning:
    Phase planner calls format_for_prompt() from the phase spec.

All records: .pipeline/memory/bug_resolutions.jsonl (types: resolution, mistake).

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

from pipeline.pipeline_config import get_pipeline_dir


def _memory_dir() -> pathlib.Path:
    return get_pipeline_dir() / "memory"


def _resolutions_path() -> pathlib.Path:
    return _memory_dir() / "bug_resolutions.jsonl"

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
# Extraction helpers
# ---------------------------------------------------------------------------

_ERROR_LINE = re.compile(
    r"(?:"
    r"(?:E\s+)?(?:AssertionError|ModuleNotFoundError|ImportError|AttributeError|"
    r"TypeError|ValueError|SyntaxError|FileNotFoundError|PermissionError|"
    r"RuntimeError|KeyError|IndexError)"
    r"[^\n]{0,200}"
    r"|FAILED\s+[^\n]+"
    r"|short test summary info[\s\S]{0,400}?FAILED[^\n]+"
    r")",
    re.IGNORECASE,
)


def extract_failure_signature(text: str, max_len: int = 120) -> str:
    """Pull the most useful error line from pytest output or fix_report."""
    if not text:
        return ""
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if _ERROR_LINE.search(s) or any(
            kw in s.lower()
            for kw in (
                "assertionerror", "importerror", "modulenotfounderror",
                "attributeerror", "typeerror", "failed", "error:",
            )
        ):
            return s[:max_len]
    m = _ERROR_LINE.search(text)
    if m:
        return m.group(0).replace("\n", " ")[:max_len]
    for line in text.splitlines():
        s = line.strip()
        if s and len(s) > 20 and not s.startswith("```"):
            return s[:max_len]
    return ""


def extract_fix_summary(validation_report: str, fix_report: str = "") -> str:
    """Describe how the phase was fixed (not just 'tests passed')."""
    if fix_report:
        attempts = re.findall(r"^### Attempt (\d+)", fix_report, re.MULTILINE)
        if attempts:
            return f"Resolved after {len(attempts)} fix attempt(s); see fix_report.md"
        for line in fix_report.splitlines():
            s = line.strip().lstrip("- ")
            if s and any(
                kw in s.lower()
                for kw in ("fixed", "added", "updated", "changed", "patched", "renamed")
            ):
                return s[:200]
    for line in (validation_report or "").splitlines():
        s = line.strip()
        if "passed" in s.lower() and "failed" not in s.lower():
            return "All tests passing after executor fixes"
    return "Phase passed after executor fix"


def _is_duplicate(failure_reason: str, source: str) -> bool:
    """Skip near-duplicate entries in the last 30 records."""
    if not _resolutions_path().exists() or not failure_reason:
        return False
    try:
        lines = [
            ln for ln in _resolutions_path().read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ][-30:]
    except OSError:
        return False
    key = failure_reason[:80].lower()
    for line in reversed(lines):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec.get("source") != source:
            continue
        if rec.get("failure_reason", "")[:80].lower() == key:
            return True
    return False


def _append_record(record: dict) -> None:
    _memory_dir().mkdir(parents=True, exist_ok=True)
    record.setdefault("ts", datetime.now(timezone.utc).isoformat())
    record.setdefault("keywords", _extract_keywords(
        f"{record.get('failure_reason', '')} {record.get('fix_summary', '')}"
    ))
    with _SimpleLock(_resolutions_path()):
        with _resolutions_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        _prune_if_needed()


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def append_resolution(
    slug: str,
    phase: int,
    failure_reason: str,
    fix_summary: str,
    retry_count: int,
    *,
    source: str = "validator",
    record_type: str = "resolution",
) -> None:
    """
    Append a resolved bug to the persistent memory store.

    Called when a phase PASSes after one or more retries (validator/reviewer).
    """
    failure_reason = (failure_reason or "Unknown failure")[:120]
    if _is_duplicate(failure_reason, source):
        return
    _append_record({
        "type": record_type,
        "source": source,
        "slug": slug,
        "phase": phase,
        "failure_reason": failure_reason,
        "fix_summary": fix_summary[:200],
        "retry_count": retry_count,
    })


def append_mistake(
    slug: str,
    phase: int,
    pattern: str,
    *,
    source: str = "reviewer",
    retry_count: int = 0,
) -> None:
    """Record a recurring coding mistake (review blocking bug, common pytest fail)."""
    pattern = (pattern or "").strip()[:120]
    if not pattern or pattern.lower() in ("none", "n/a"):
        return
    if _is_duplicate(pattern, source):
        return
    _append_record({
        "type": "mistake",
        "source": source,
        "slug": slug,
        "phase": phase,
        "failure_reason": pattern,
        "fix_summary": "Avoid this pattern in future phases",
        "retry_count": retry_count,
    })


def record_validator_pass(
    slug: str,
    phase: int,
    fix_report: str,
    validation_report: str,
    retry_count: int,
) -> None:
    """Record a test-fix resolution after validator PASS (post-retry)."""
    if not fix_report or retry_count < 1:
        return
    fail = extract_failure_signature(fix_report) or extract_failure_signature(
        validation_report
    )
    if not fail:
        fail = "Tests failed before passing"
    fix = extract_fix_summary(validation_report, fix_report)
    append_resolution(
        slug, phase, fail, fix, retry_count,
        source="validator", record_type="resolution",
    )


def record_reviewer_pass(
    slug: str,
    phase: int,
    review_content: str,
    fix_report: str,
    validator_retries: int,
) -> None:
    """Record review-driven fixes after post-validation PASS."""
    if validator_retries < 1 and not fix_report:
        return
    blocking = _extract_blocking_bullets(review_content)
    if blocking:
        for bullet in blocking[:3]:
            append_mistake(slug, phase, bullet, source="reviewer", retry_count=validator_retries)
    if fix_report and validator_retries >= 1:
        fail = extract_failure_signature(fix_report)
        if fail and "reviewer" in fix_report.lower():
            append_resolution(
                slug, phase, fail,
                "Fixed review blocking bugs before validation passed",
                validator_retries,
                source="reviewer",
            )


def record_failure_observation(
    slug: str,
    phase: int,
    pytest_or_report: str,
    retry_count: int,
) -> None:
    """Log a recurring failure signature while still failing (helps next fix attempt)."""
    if retry_count < 2:
        return
    sig = extract_failure_signature(pytest_or_report)
    if sig:
        append_mistake(slug, phase, sig, source="validator", retry_count=retry_count)


def record_grok_debrief(
    slug: str,
    phase: int,
    entries: list[dict],
) -> int:
    """
    Import bug resolutions from a Grok Build post-phase debrief (JSON list).

    Each entry may include:
      failure_reason (str), fix_summary (str),
      type: "resolution" | "mistake" (default resolution),
      retry_count (int, optional).
    """
    written = 0
    for raw in entries:
        if not isinstance(raw, dict):
            continue
        fail = (raw.get("failure_reason") or raw.get("pattern") or "").strip()
        fix = (raw.get("fix_summary") or "").strip()
        if not fail:
            continue
        kind = (raw.get("type") or "resolution").strip().lower()
        retry = int(raw.get("retry_count") or 0)
        if kind == "mistake":
            append_mistake(slug, phase, fail, source="grok", retry_count=retry)
        else:
            append_resolution(
                slug,
                phase,
                fail,
                fix or "Fixed during Grok implement session",
                retry,
                source="grok",
                record_type="resolution",
            )
        written += 1
    return written


def _extract_blocking_bullets(review_content: str) -> list[str]:
    m = re.search(
        r"##\s*Blocking Bugs.*?(?=##\s|\Z)",
        review_content,
        re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return []
    section = m.group(0)
    if re.search(r"\bnone\b", section, re.IGNORECASE):
        return []
    bullets = []
    for line in section.splitlines():
        s = line.strip()
        if s.startswith(("-", "*")) and len(s) > 4:
            bullets.append(s.lstrip("-* ").strip()[:120])
    return bullets


def format_for_fix_loop(
    fix_report: str = "",
    review_content: str = "",
    error_summary: str = "",
    top_n: int = 5,
) -> str:
    """Context block for executor fix runs — wider recall than phase planning."""
    query = f"{fix_report[:4000]} {review_content[:2000]} {error_summary}"
    return format_for_prompt(query, top_n=top_n)


def _prune_if_needed() -> None:
    """Keep only the most recent MAX_RECORDS entries. Called inside lock."""
    if not _resolutions_path().exists():
        return
    lines = _resolutions_path().read_text(encoding="utf-8").splitlines()
    if len(lines) > MAX_RECORDS:
        kept = lines[-MAX_RECORDS:]
        _resolutions_path().write_text("\n".join(kept) + "\n", encoding="utf-8")


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
    if not _resolutions_path().exists():
        return []

    query_keywords = set(_extract_keywords(task_text))
    if not query_keywords:
        return []

    scored: list[tuple[int, dict]] = []

    try:
        lines = _resolutions_path().read_text(encoding="utf-8").splitlines()
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

    lines = [
        "## Pipeline memory (past failures & fixes — do NOT repeat these mistakes)",
    ]
    for i, rec in enumerate(results, 1):
        slug = rec.get("slug", "?")
        phase = rec.get("phase", "?")
        fail = rec.get("failure_reason", "")
        fix = rec.get("fix_summary", "")
        retries = rec.get("retry_count", 1)
        src = rec.get("source", "?")
        kind = rec.get("type", "resolution")
        label = "Mistake" if kind == "mistake" else "Resolution"
        lines.append(
            f"\n**{label} {i}** ({src}, {slug} phase {phase}, {retries} retries):\n"
            f"- Issue: {fail}\n"
            f"- Guidance: {fix}"
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
    if not _resolutions_path().exists():
        print("  No bug resolutions recorded yet.")
        return

    lines = _resolutions_path().read_text(encoding="utf-8").splitlines()
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
    by_type: dict[str, int] = {}
    by_source: dict[str, int] = {}
    for r in records:
        by_type[r.get("type", "resolution")] = by_type.get(r.get("type", "resolution"), 0) + 1
        by_source[r.get("source", "?")] = by_source.get(r.get("source", "?"), 0) + 1

    print(f"\n  Bug Resolution Memory: {_resolutions_path()}")
    print(f"  Total records:     {len(records)}")
    print(f"  Unique projects:   {unique_slugs}")
    print(f"  Avg retries/fix:   {avg_retries:.1f}")
    print(f"  By type:           {by_type}")
    print(f"  By source:         {by_source}")
    print(f"  Top keywords:      {', '.join(kw for kw, _ in top_kw)}")
    print()


if __name__ == "__main__":
    print_stats()
