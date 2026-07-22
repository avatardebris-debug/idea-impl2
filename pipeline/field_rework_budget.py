"""
Accumulative field/ship rework budget.

Stuck projects (field_testing, ship_insufficient retries, etc.) may re-enter
the ship track a few times, but not forever. When caps are hit, status becomes
``deeper_work_needed`` so overnight from-list can move on.

Env:
  FIELD_REWORK_MAX_ATTEMPTS   default 3        (thin-ship / field rework entries)
  FIELD_REWORK_MAX_MINUTES    default 45       (sum of wall minutes across attempts)
  FIELD_REWORK_MAX_TOKENS     default 2500000  (sum of measured LLM tokens; fairer across models)
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_DEEPER_WORK_NEEDED = "deeper_work_needed"

# In-flight ship statuses that count toward rework caps when re-queued
FIELD_REWORK_STATUSES = frozenset({
    "field_testing",
    "field_test_planning",
    "field_test_failed",
    "field_test_passed",
    "thermo_reviewing",
    "thermo_refactoring",
    "ship_evaluating",
    "ship_insufficient",  # retry path
})

DEFAULT_MAX_TOKENS = 2_500_000


def rework_max_attempts() -> int:
    raw = (os.environ.get("FIELD_REWORK_MAX_ATTEMPTS") or "3").strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return 3


def rework_max_minutes() -> float:
    raw = (os.environ.get("FIELD_REWORK_MAX_MINUTES") or "45").strip()
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 45.0


def rework_max_tokens() -> int:
    raw = (os.environ.get("FIELD_REWORK_MAX_TOKENS") or str(DEFAULT_MAX_TOKENS)).strip()
    # allow 2.5e6 / 2_500_000 / 2500000
    raw = raw.replace("_", "").replace(",", "")
    try:
        if "e" in raw.lower():
            return max(0, int(float(raw)))
        return max(0, int(float(raw)))
    except ValueError:
        return DEFAULT_MAX_TOKENS


def rework_over_budget(state: dict[str, Any] | None) -> bool:
    """True if attempts, minutes, or tokens exceed env caps."""
    if not state:
        return False
    attempts = int(state.get("field_rework_attempts") or 0)
    minutes = float(state.get("field_rework_minutes") or 0.0)
    tokens = int(state.get("field_rework_tokens") or 0)
    if attempts >= rework_max_attempts():
        return True
    if minutes >= rework_max_minutes():
        return True
    max_tok = rework_max_tokens()
    if max_tok > 0 and tokens >= max_tok:
        return True
    return False


def begin_field_rework_attempt(state: dict[str, Any]) -> dict[str, Any]:
    """Increment attempt counter and stamp attempt start (UTC iso + unix)."""
    state = dict(state)
    state["field_rework_attempts"] = int(state.get("field_rework_attempts") or 0) + 1
    now = datetime.now(timezone.utc)
    state["field_rework_attempt_started_at"] = now.isoformat()
    state["field_rework_attempt_started_unix"] = now.timestamp()
    return state


def _parse_start_unix(state: dict[str, Any]) -> float | None:
    u = state.get("field_rework_attempt_started_unix")
    if isinstance(u, (int, float)) and u > 0:
        return float(u)
    started = state.get("field_rework_attempt_started_at")
    if isinstance(started, str) and started:
        try:
            dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            return dt.timestamp()
        except Exception:
            return None
    return None


def _has_active_rework_attempt(state: dict[str, Any]) -> bool:
    """True when begin_field_rework_attempt stamped an open attempt."""
    u = state.get("field_rework_attempt_started_unix")
    if isinstance(u, (int, float)) and u > 0:
        return True
    started = state.get("field_rework_attempt_started_at")
    return isinstance(started, str) and bool(started.strip())


def _llm_row_tokens(e: dict[str, Any]) -> int:
    tok = e.get("tokens")
    if tok is None:
        tok = e.get("total_tokens")
    if tok is None:
        pt = int(e.get("prompt_tokens") or 0)
        ct = int(e.get("completion_tokens") or 0)
        tok = pt + ct if (pt or ct) else 0
    return int(tok or 0)


def measure_tokens_for_slug(
    slug: str,
    *,
    since_unix: float | None,
    project_dir: Path | None = None,
) -> int:
    """Sum measured tokens for *slug* since *since_unix* (best effort).

    Primary source only (never sum agent_timing + llm_calls — same call is often
    recorded in both):
      1. metrics/llm_calls.jsonl if any positive token rows in the window
      2. else state/agent_timing.jsonl if any positive token rows in the window
      3. else fallback: rough char/4 estimate from grok_*.log / prompts
         (Grok CLI often has no usage API)

    When *since_unix* is set, rows without a usable timestamp are skipped.
    """
    if not slug:
        return 0
    since = float(since_unix or 0.0)

    # 1) llm_calls.jsonl (preferred when it has positive token rows)
    llm_total = 0
    llm_has_positive = False
    try:
        from pipeline.paths import metrics_dir

        calls = metrics_dir() / "llm_calls.jsonl"
        if calls.is_file():
            for line in calls.read_text(encoding="utf-8", errors="replace").splitlines()[-3000:]:
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if (e.get("slug") or "") != slug:
                    continue
                ts = float(e.get("ts_unix") or 0)
                if not ts and e.get("ts"):
                    try:
                        ts = datetime.fromisoformat(
                            str(e["ts"]).replace("Z", "+00:00")
                        ).timestamp()
                    except Exception:
                        ts = 0.0
                if since:
                    # No usable ts → skip (do not count untimestamped rows every attempt)
                    if not ts or ts < since:
                        continue
                tok_i = _llm_row_tokens(e)
                if tok_i > 0:
                    llm_has_positive = True
                llm_total += tok_i
    except Exception:
        pass

    if llm_has_positive:
        return max(0, int(llm_total))

    # 2) agent_timing.jsonl
    agent_total = 0
    agent_has_positive = False
    try:
        from pipeline.paths import state_dir

        timing = state_dir() / "agent_timing.jsonl"
        if timing.is_file():
            for line in timing.read_text(encoding="utf-8", errors="replace").splitlines():
                if not line.strip():
                    continue
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if (e.get("slug") or "") != slug:
                    continue
                ts = float(e.get("ts") or 0)
                if since:
                    if not ts or ts < since:
                        continue
                tok_i = int(e.get("tokens") or 0)
                if tok_i > 0:
                    agent_has_positive = True
                agent_total += tok_i
    except Exception:
        pass

    if agent_has_positive:
        return max(0, int(agent_total))

    # 3) Grok CLI logs — only if neither metrics source had positive tokens
    total = 0
    if project_dir is not None:
        try:
            proj = Path(project_dir)
            phases = proj / "phases"
            if phases.is_dir():
                chars = 0
                for logf in phases.rglob("grok_*.log"):
                    try:
                        if since and logf.stat().st_mtime < since:
                            continue
                        chars += logf.stat().st_size
                    except OSError:
                        continue
                for pf in phases.rglob("grok_prompt_*.md"):
                    try:
                        if since and pf.stat().st_mtime < since:
                            continue
                        chars += pf.stat().st_size
                    except OSError:
                        continue
                # ~4 chars/token rough; logs are prompt+output-ish
                total = max(0, chars // 4)
        except Exception:
            pass

    return max(0, int(total))


def end_field_rework_attempt(
    state: dict[str, Any],
    *,
    slug: str = "",
    project_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Add wall minutes + measured tokens for this attempt.

    No-op when there is no active attempt stamp (already ended / never begun),
    so callers that both end and then mark_deeper_work_needed do not double-add
    all-history tokens (since=0).
    """
    state = dict(state)
    if not _has_active_rework_attempt(state):
        return state

    started = state.get("field_rework_attempt_started_at")
    since_unix = _parse_start_unix(state)
    elapsed_min = 0.0
    if isinstance(started, str) and started:
        try:
            dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
            elapsed_min = max(
                0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 60.0
            )
        except Exception:
            elapsed_min = 0.0
    prev_m = float(state.get("field_rework_minutes") or 0.0)
    state["field_rework_minutes"] = round(prev_m + elapsed_min, 2)

    slug = slug or state.get("slug") or state.get("_slug") or ""
    proj = Path(project_dir) if project_dir else None
    attempt_tokens = measure_tokens_for_slug(
        slug, since_unix=since_unix, project_dir=proj
    )
    prev_t = int(state.get("field_rework_tokens") or 0)
    # attempt_tokens is absolute window sum for slug; use as delta for this attempt
    state["field_rework_tokens"] = prev_t + max(0, attempt_tokens)
    state["field_rework_tokens_last_attempt"] = attempt_tokens

    state.pop("field_rework_attempt_started_at", None)
    state.pop("field_rework_attempt_started_unix", None)
    return state


def mark_deeper_work_needed(
    state: dict[str, Any],
    *,
    reason: str,
    slug: str = "",
    project_dir: Path | str | None = None,
) -> dict[str, Any]:
    """Terminal status: needs human / deeper effort; stop auto re-queue."""
    state = dict(state)
    state = end_field_rework_attempt(state, slug=slug, project_dir=project_dir)
    state["status"] = STATUS_DEEPER_WORK_NEEDED
    state["deeper_work_reason"] = (reason or "")[:500]
    state["deeper_work_at"] = datetime.now(timezone.utc).isoformat()
    return state


def maybe_park_if_over_budget(
    state: dict[str, Any],
    *,
    reason_prefix: str = "field rework budget exhausted",
    slug: str = "",
    project_dir: Path | str | None = None,
) -> tuple[dict[str, Any], bool]:
    """If over budget, park as deeper_work_needed. Returns (state, parked)."""
    if not rework_over_budget(state):
        return state, False
    attempts = int(state.get("field_rework_attempts") or 0)
    minutes = float(state.get("field_rework_minutes") or 0.0)
    tokens = int(state.get("field_rework_tokens") or 0)
    reason = (
        f"{reason_prefix}: attempts={attempts}/{rework_max_attempts()} "
        f"minutes={minutes:.1f}/{rework_max_minutes():.0f} "
        f"tokens={tokens}/{rework_max_tokens()}"
    )
    return (
        mark_deeper_work_needed(
            state, reason=reason, slug=slug, project_dir=project_dir
        ),
        True,
    )


def write_state(project_dir: Path, state: dict[str, Any]) -> None:
    sf = Path(project_dir) / "state" / "current_idea.json"
    sf.parent.mkdir(parents=True, exist_ok=True)
    sf.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
