"""Core utilities for column mapping.

Provides default mapping retrieval and custom-over-default merging.
"""

from typing import Dict, Optional


# Default column mapping: CSV column name → SOP field name
DEFAULT_MAPPING: Dict[str, str] = {
    "task_name": "task_name",
    "task": "task_name",
    "name": "task_name",
    "title": "task_name",
    "description": "description",
    "desc": "description",
    "steps": "steps",
    "step": "steps",
    "assignee": "assignee",
    "assigned_to": "assignee",
    "owner": "assignee",
    "deadline": "deadline",
    "due_date": "deadline",
    "due": "deadline",
    "priority": "priority",
    "level": "priority",
}


def get_default_mapping() -> Dict[str, str]:
    """Return a copy of the default column mapping.

    Returns a new dict each time so callers can safely mutate it
    without affecting the module-level constant.
    """
    return dict(DEFAULT_MAPPING)


def merge_mappings(
    default: Dict[str, str],
    custom: Optional[Dict[str, str]],
) -> Dict[str, str]:
    """Merge a custom mapping over the default mapping.

    Custom keys override defaults; new keys are added.
    Neither *default* nor *custom* is mutated.

    Parameters
    ----------
    default : dict
        The default mapping (base).
    custom : dict or None
        Custom mapping to overlay on top.

    Returns
    -------
    dict
        A new merged mapping.
    """
    merged = dict(default)
    if custom:
        merged.update(custom)
    return merged
