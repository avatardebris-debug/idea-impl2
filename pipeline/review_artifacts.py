"""
pipeline/review_artifacts.py
Shared helpers for validation/review artifact checks (no LLM).
"""

from __future__ import annotations

import re

_BOILERPLATE_PHRASES = (
    "(bullet list of things",
    "(ONLY issues that will cause",
    "(style, naming, future improvements",
    "(list any self-contained utilities",
    "your structured review here",
    "write your review here",
    "placeholder",
)


def validation_passed(content: str) -> bool:
    return bool(content and "Verdict: PASS" in content)


def review_artifacts_complete(review_content: str) -> bool:
    """True when review.md looks like a finished assessment (not a template)."""
    text = review_content.strip()
    if len(text) < 200:
        return False
    if not re.search(r"##\s+Verdict", text, re.IGNORECASE):
        return False
    if not re.search(r"##\s+Blocking Bugs", text, re.IGNORECASE):
        return False
    lower = text.lower()
    if any(phrase in lower for phrase in _BOILERPLATE_PHRASES):
        return False
    if "review file was not generated" in lower:
        return False
    return True


def count_blocking_bugs(review_content: str) -> int:
    bugs_section = re.search(
        r"## Blocking Bugs.*?(?=## |$)", review_content, re.DOTALL | re.IGNORECASE
    )
    if not bugs_section:
        return 0
    section_text = bugs_section.group()
    if re.search(r"\bnone\b", section_text, re.IGNORECASE):
        return 0
    return len(re.findall(r"^[-*]\s+", section_text, re.MULTILINE))


def extract_non_blocking_notes(review_content: str) -> str:
    non_blocking_section = re.search(
        r"## Non-Blocking Notes.*?(?=## |$)", review_content, re.DOTALL | re.IGNORECASE
    )
    if not non_blocking_section:
        return ""
    raw = non_blocking_section.group().strip()
    if re.search(r"^[-*]\s+", raw, re.MULTILINE):
        return raw
    return ""


def build_review_result(
    *,
    review_content: str,
    review_path: str,
    tasks_path: str,
    workspace_path: str,
    files_written: list | None = None,
) -> dict:
    return {
        "blocking_bugs": count_blocking_bugs(review_content),
        "review_path": review_path,
        "tasks_path": tasks_path,
        "workspace_path": workspace_path,
        "files_written": files_written or [],
        "non_blocking_notes": extract_non_blocking_notes(review_content)[:1500],
        "review_content_preview": review_content[:1500],
    }
