"""Compare two NDA text outputs side-by-side (unified diff style)."""

import difflib
import logging
import os
from typing import List, Tuple

logger = logging.getLogger(__name__)


def compare_ndas(text_a: str, text_b: str, label_a: str = "NDA A", label_b: str = "NDA B") -> str:
    """Generate a unified diff comparison of two NDA texts.

    Args:
        text_a: The first NDA text.
        text_b: The second NDA text.
        label_a: Label for the first NDA (shown in diff header).
        label_b: Label for the second NDA (shown in diff header).

    Returns:
        A unified diff string showing differences.
    """
    lines_a = text_a.splitlines(keepends=True)
    lines_b = text_b.splitlines(keepends=True)

    diff = difflib.unified_diff(
        lines_a,
        lines_b,
        fromfile=label_a,
        tofile=label_b,
        lineterm="",
    )
    result = "\n".join(diff)
    if not result.strip():
        return f"[No differences found between {label_a} and {label_b}]"
    return result


def compare_nda_files(path_a: str, path_b: str) -> str:
    """Compare two NDA files by path.

    Args:
        path_a: Path to the first NDA file.
        path_b: Path to the second NDA file.

    Returns:
        Unified diff string.

    Raises:
        FileNotFoundError: If either file does not exist.
    """
    if not os.path.exists(path_a):
        raise FileNotFoundError(f"File not found: {path_a}")
    if not os.path.exists(path_b):
        raise FileNotFoundError(f"File not found: {path_b}")

    with open(path_a, encoding="utf-8") as f:
        text_a = f.read()
    with open(path_b, encoding="utf-8") as f:
        text_b = f.read()

    return compare_ndas(text_a, text_b, label_a=path_a, label_b=path_b)


def summary_diff(text_a: str, text_b: str) -> dict:
    """Return a summary of differences between two NDA texts.

    Args:
        text_a: The first NDA text.
        text_b: The second NDA text.

    Returns:
        Dict with 'added_lines', 'removed_lines', 'changed_sections', 'identical'.
    """
    lines_a = text_a.splitlines()
    lines_b = text_b.splitlines()

    added = [l for l in lines_b if l not in set(lines_a) and l.strip()]
    removed = [l for l in lines_a if l not in set(lines_b) and l.strip()]

    sm = difflib.SequenceMatcher(None, text_a, text_b)
    similarity = sm.ratio()

    return {
        "identical": text_a == text_b,
        "similarity_ratio": round(similarity, 3),
        "added_lines": len(added),
        "removed_lines": len(removed),
        "total_lines_a": len(lines_a),
        "total_lines_b": len(lines_b),
    }
