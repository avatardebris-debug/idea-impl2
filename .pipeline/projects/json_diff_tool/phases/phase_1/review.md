# Phase 1 Review — JSON Diff Tool

## What's Good

- **CLI structure is well-designed**: The `cli.py` properly separates argument parsing (`create_parser`) from the main logic (`main`), making it testable and maintainable.
- **Error handling is robust**: `loader.py` catches both `FileNotFoundError` and `json.JSONDecodeError`, converting them to appropriate exceptions with clear messages.
- **DiffEntry class is well-structured**: The `diff.py` module defines a clear `DiffEntry` class with constants for actions (ADDED, REMOVED, CHANGED) and proper attributes for path, old_value, and new_value.
- **Recursive diff algorithm handles all cases**: The `compare_json` function correctly handles dictionaries, lists, and primitive values, including type mismatches.
- **Formatter produces clear output**: The `format_diff` function uses intuitive symbols (+, -, →) and clearly shows the path to each change.
- **Test coverage is comprehensive**: The test suite covers 21 test cases including edge cases like empty objects, nested structures, arrays, type mismatches, and deeply nested structures.
- **Package structure follows Python conventions**: Proper `__init__.py`, `__main__.py`, and clear module separation.
- **Type hints are used consistently**: All functions have proper type annotations for better code documentation.

## Blocking Bugs

None

## Non-Blocking Notes

- **DiffEntry.__repr__**: The `__repr__` method in `DiffEntry` could be improved to show all attributes more clearly for debugging purposes.
- **Formatter output ordering**: The `format_diff` function outputs entries in the order they appear in the list, which may not be intuitive for complex diffs. Consider sorting by path for better readability.
- **Array comparison limitation**: The array comparison in `compare_json` compares by index position, which means `[1, 2, 3]` vs `[1, 3, 2]` would show two changes rather than recognizing it as a reordering. This is a design choice but worth noting.
- **Path separator consistency**: The path uses `.` for object keys and `[]` for array indices, which is clear but could be documented more explicitly.
- **No diff ordering guarantee**: The order of diff entries depends on dictionary iteration order (Python 3.7+ preserves insertion order, but this could be made explicit).
- **Formatter doesn't handle empty diff lists**: The function returns an empty string for an empty list, which is fine but could return a message like "No differences found" for better UX.

## Reusable Components

- **DiffEntry class** (`diff.py`): A self-contained data class for representing diff entries with standardized action types (ADDED, REMOVED, CHANGED). Could be reused in any diff/comparison tool.
- **load_json function** (`loader.py`): A robust JSON file loader with consistent error handling that could be reused across projects needing JSON file loading.
- **compare_json function** (`diff.py`): A recursive JSON comparison algorithm that handles nested objects and arrays, useful for any JSON diffing needs.
- **format_diff function** (`formatter.py`): A formatter that converts diff entries to human-readable output with clear visual indicators.

## Verdict

PASS — All code is functional, well-structured, and all 21 tests pass with no blocking bugs.
