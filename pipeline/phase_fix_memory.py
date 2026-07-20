"""
Structured per-phase fix memory so retries do not repeat failed approaches.

Persists under projects/<slug>/state/phase_{N}_fix_memory.json:

  {
    "attempts": [ { "at", "summary", "signature" }, ... ],
    "recurring_signatures": [ ... ]   # failure signatures seen on FAIL
  }

  (legacy key "banned_signatures" is still read/written for compat)

Written from validator (and optionally other fix paths) on validation FAIL.
Injected into executor fix prompts via format_for_prompt().
Cleared on phase PASS / force-advance.
"""

from __future__ import annotations

import json
import logging
import os
import pathlib
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

MAX_ATTEMPTS_STORED = 40
MAX_RECURRING = 30
MAX_SUMMARY = 240
MAX_SIGNATURE = 120


def fix_memory_path(project_dir: pathlib.Path, phase: int) -> pathlib.Path:
    return pathlib.Path(project_dir) / "state" / f"phase_{int(phase)}_fix_memory.json"


def _empty() -> dict[str, Any]:
    return {"attempts": [], "recurring_signatures": [], "banned_signatures": []}


def load_fix_memory(project_dir: pathlib.Path, phase: int) -> dict[str, Any]:
    path = fix_memory_path(project_dir, phase)
    if not path.is_file():
        return _empty()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _empty()
        attempts = data.get("attempts") or []
        recurring = data.get("recurring_signatures") or data.get("banned_signatures") or []
        if not isinstance(attempts, list):
            attempts = []
        if not isinstance(recurring, list):
            recurring = []
        cleaned = [str(s) for s in recurring if s]
        return {
            "attempts": [a for a in attempts if isinstance(a, dict)],
            "recurring_signatures": cleaned,
            # legacy alias for callers/tests still reading banned_signatures
            "banned_signatures": cleaned,
        }
    except Exception as exc:
        logger.debug("load fix_memory failed: %s", exc)
        return _empty()


def save_fix_memory(
    project_dir: pathlib.Path,
    phase: int,
    data: dict[str, Any],
) -> pathlib.Path:
    path = fix_memory_path(project_dir, phase)
    path.parent.mkdir(parents=True, exist_ok=True)
    attempts = list(data.get("attempts") or [])[-MAX_ATTEMPTS_STORED:]
    recurring = list(
        data.get("recurring_signatures")
        or data.get("banned_signatures")
        or []
    )[-MAX_RECURRING:]
    # Dedupe while preserving order
    seen: set[str] = set()
    recurring_clean: list[str] = []
    for b in recurring:
        key = str(b).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        recurring_clean.append(str(b).strip()[:MAX_SIGNATURE])
    payload = {
        "attempts": attempts,
        "recurring_signatures": recurring_clean,
        # keep legacy key so older tooling still works
        "banned_signatures": recurring_clean,
    }
    text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    # Atomic write: temp + replace
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text(text, encoding="utf-8")
        os.replace(str(tmp), str(path))
    except OSError:
        try:
            path.write_text(text, encoding="utf-8")
        except OSError as exc:
            logger.debug("save fix_memory failed: %s", exc)
        try:
            if tmp.is_file():
                tmp.unlink()
        except OSError:
            pass
    return path


def _signature_from_text(text: str) -> str:
    if not text:
        return ""
    try:
        from pipeline.bug_memory import extract_failure_signature

        sig = extract_failure_signature(text, max_len=MAX_SIGNATURE)
        if sig:
            return sig.strip()
    except Exception:
        pass
    for line in text.splitlines():
        s = line.strip()
        if s and len(s) > 12 and not s.startswith("#"):
            return s[:MAX_SIGNATURE]
    return text.strip()[:MAX_SIGNATURE]


def record_failed_attempt(
    project_dir: pathlib.Path,
    phase: int,
    *,
    summary: str = "",
    signature: str = "",
    source_text: str = "",
    ban: bool = True,
) -> dict[str, Any]:
    """
    Append one failed fix/validation attempt.

    *signature* is a **failure signature** (pytest/error line), not a ban on
    fixing that error. If empty, derive from *source_text* via
    bug_memory.extract_failure_signature when available.

    *ban* (legacy name): when True, add signature to recurring_signatures list.
    """
    data = load_fix_memory(project_dir, phase)
    sig = (signature or "").strip() or _signature_from_text(source_text)
    sum_text = (summary or "").strip()
    if not sum_text:
        sum_text = sig or "validation failed"
    sum_text = sum_text[:MAX_SUMMARY]
    entry = {
        "at": datetime.now(timezone.utc).isoformat(),
        "summary": sum_text,
        "signature": sig[:MAX_SIGNATURE] if sig else "",
    }
    data["attempts"].append(entry)
    if ban and sig:
        recurring = list(data.get("recurring_signatures") or data.get("banned_signatures") or [])
        key = sig.strip().lower()
        if key and not any(str(b).strip().lower() == key for b in recurring):
            recurring.append(sig[:MAX_SIGNATURE])
        data["recurring_signatures"] = recurring
        data["banned_signatures"] = recurring
    save_fix_memory(project_dir, phase, data)
    return data


def format_for_prompt(
    project_dir: pathlib.Path,
    phase: int,
    *,
    last_n: int = 3,
    max_banned: int = 8,
) -> str:
    """Markdown block for executor fix prompts (recurring failures + recent attempts)."""
    data = load_fix_memory(project_dir, phase)
    attempts = data.get("attempts") or []
    recurring = data.get("recurring_signatures") or data.get("banned_signatures") or []
    if not attempts and not recurring:
        return ""

    lines = [
        "## Phase fix memory (retry context — try a *different* approach)",
    ]
    if recurring:
        lines.append(
            "### Recurring failure signatures "
            "(same errors keep showing — do **not** repeat a previous failed fix strategy)"
        )
        for b in recurring[-max_banned:]:
            lines.append(f"- `{b}`")
    recent = attempts[-last_n:] if attempts else []
    if recent:
        lines.append("### Last failed validation attempts")
        for i, att in enumerate(recent, 1):
            sig = att.get("signature") or ""
            summ = att.get("summary") or ""
            at = att.get("at") or ""
            lines.append(f"{i}. [{at}] {summ}" + (f" — sig: `{sig}`" if sig else ""))
    lines.append(
        "These are **failure signatures**, not bans on fixing the bug. "
        "Keep fixing the underlying error, but use a **new** approach if prior "
        "attempts already tried the obvious patch."
    )
    return "\n".join(lines)


def clear_fix_memory(project_dir: pathlib.Path, phase: int) -> None:
    path = fix_memory_path(project_dir, phase)
    try:
        if path.is_file():
            path.unlink()
    except OSError:
        pass
    # Also drop temp leftovers
    try:
        tmp = path.with_suffix(path.suffix + ".tmp")
        if tmp.is_file():
            tmp.unlink()
    except OSError:
        pass


# Back-compat alias
MAX_BANNED = MAX_RECURRING
