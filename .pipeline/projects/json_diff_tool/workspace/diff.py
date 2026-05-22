"""Module for comparing JSON structures and computing diffs."""

from typing import Any, List, Union


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


def compare_json(obj1: Any, obj2: Any, path: str = "") -> List[DiffEntry]:
    """Recursively compare two JSON structures and return a list of diff entries.
    
    Args:
        obj1: First JSON object (dict, list, or primitive).
        obj2: Second JSON object (dict, list, or primitive).
        path: Current path in the structure (for tracking nested locations).
        
    Returns:
        A list of DiffEntry objects describing the differences.
    """
    entries: List[DiffEntry] = []
    
    # Handle type mismatches
    if type(obj1) != type(obj2):
        entries.append(DiffEntry(path, DiffEntry.CHANGED, obj1, obj2))
        return entries
    
    # Handle dictionaries
    if isinstance(obj1, dict):
        all_keys = set(obj1.keys()) | set(obj2.keys())
        
        for key in all_keys:
            key_path = f"{path}.{key}" if path else key
            
            if key in obj1 and key not in obj2:
                entries.append(DiffEntry(key_path, DiffEntry.REMOVED, obj1[key], None))
            elif key not in obj1 and key in obj2:
                entries.append(DiffEntry(key_path, DiffEntry.ADDED, None, obj2[key]))
            else:
                # Key exists in both, recurse
                entries.extend(compare_json(obj1[key], obj2[key], key_path))
    
    # Handle lists/arrays
    elif isinstance(obj1, list):
        max_len = max(len(obj1), len(obj2))
        
        for i in range(max_len):
            index_path = f"{path}[{i}]"
            
            if i >= len(obj1):
                entries.append(DiffEntry(index_path, DiffEntry.ADDED, None, obj2[i]))
            elif i >= len(obj2):
                entries.append(DiffEntry(index_path, DiffEntry.REMOVED, obj1[i], None))
            else:
                entries.extend(compare_json(obj1[i], obj2[i], index_path))
    
    # Handle primitive values
    else:
        if obj1 != obj2:
            entries.append(DiffEntry(path, DiffEntry.CHANGED, obj1, obj2))
    
    return entries
