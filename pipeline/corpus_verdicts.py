"""Shared validation/review verdict parsing for corpus collect and gate."""

from __future__ import annotations

import re

_VERDICT_PASS = re.compile(
    r"(?:^|\n)\s*(?:##\s*)?Verdict\s*:?\s*PASS\b",
    re.IGNORECASE | re.MULTILINE,
)
_VERDICT_FAIL = re.compile(
    r"(?:^|\n)\s*(?:##\s*)?Verdict\s*:?\s*FAIL\b",
    re.IGNORECASE | re.MULTILINE,
)


def verdict_from_report(text: str) -> str:
    """Return PASS, FAIL, or UNKNOWN from a validation/review markdown report."""
    if not text.strip():
        return "UNKNOWN"
    if _VERDICT_FAIL.search(text):
        return "FAIL"
    if _VERDICT_PASS.search(text):
        return "PASS"
    if "Verdict: PASS" in text or "## Verdict\nPASS" in text:
        return "PASS"
    return "UNKNOWN"


def parse_phase_verdicts(val_report: str, review_md: str) -> tuple[str, str]:
    """Parse test and review verdict strings for a phase."""
    return verdict_from_report(val_report), verdict_from_report(review_md)
