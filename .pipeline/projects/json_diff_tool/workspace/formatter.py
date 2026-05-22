"""Module for formatting diff output in a human-readable way."""

from typing import List
from .diff import DiffEntry


def format_diff(diff_entries: List[DiffEntry]) -> str:
    """Format a list of diff entries into a human-readable string.
    
    Args:
        diff_entries: List of DiffEntry objects to format.
        
    Returns:
        A formatted string showing the differences with clear indicators.
    """
    lines: List[str] = []
    
    for entry in diff_entries:
        if entry.action == DiffEntry.ADDED:
            prefix = "+"
            value_str = str(entry.new_value)
            lines.append(f"{prefix} {entry.path}: {value_str}")
        elif entry.action == DiffEntry.REMOVED:
            prefix = "-"
            value_str = str(entry.old_value)
            lines.append(f"{prefix} {entry.path}: {value_str}")
        elif entry.action == DiffEntry.CHANGED:
            prefix = "→"
            old_str = str(entry.old_value)
            new_str = str(entry.new_value)
            lines.append(f"{prefix} {entry.path}: {old_str} → {new_str}")
    
    return "\n".join(lines)
