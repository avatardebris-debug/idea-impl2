"""DiffEntry class for representing diff entries."""

from typing import Any, List


class DiffEntry:
    """Represents a single diff entry."""
    
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
    
    def __init__(self, path: str, action: str, old_value: Any = None, new_value: Any = None):
        self.path = path
        self.action = action
        self.old_value = old_value
        self.new_value = new_value
    
    def __repr__(self):
        return f"DiffEntry(path={self.path!r}, action={self.action!r}, old={self.old_value!r}, new={self.new_value!r})"
