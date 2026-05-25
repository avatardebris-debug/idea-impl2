"""
pipeline/text_util.py
Small text helpers for terminal output.
"""

from __future__ import annotations

import re

_ANSI_ESCAPE = re.compile(
    r"(?:\x1B[@-Z\\-_]|[\x80-\x9A\x9C-\x9F]|(?:\x1B\[|\x9B)[0-?]*[ -/]*[@-~]|\x1B\][^\x07\x1B]*(?:\x07|\x1B\\))"
)


def clean_ansi(text: str) -> str:
    """Strip ANSI/OSC escape sequences from a string."""
    return _ANSI_ESCAPE.sub("", text)
