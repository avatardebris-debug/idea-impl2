"""Condition operator evaluation functions for the rule engine."""

from __future__ import annotations

import re
from typing import Any


def evaluate_condition(field_value: Any, operator: str, value: Any) -> bool:
    """Evaluate a single condition against an email field value.

    Args:
        field_value: The value from the email (e.g., subject, body, from).
        operator: The comparison operator (contains, not_contains, equals,
                  regex, is_empty, gt, lt).
        value: The value to compare against.

    Returns:
        True if the condition matches, False otherwise.

    Raises:
        ValueError: If the operator is not supported.
    """
    if operator == "is_empty":
        return _is_empty(field_value)

    if operator == "gt":
        return _gt(field_value, value)

    if operator == "lt":
        return _lt(field_value, value)

    # For string-based operators, coerce to string
    if field_value is None:
        field_str = ""
    else:
        field_str = str(field_value)

    if operator == "contains":
        return str(value) in field_str

    if operator == "not_contains":
        return str(value) not in field_str

    if operator == "equals":
        return field_str == str(value)

    if operator == "regex":
        return bool(re.search(str(value), field_str))

    raise ValueError(f"Unsupported operator: {operator}")


def _is_empty(value: Any) -> bool:
    """Check if a value is considered empty.

    Handles None, empty string, False, and empty collections.
    """
    if value is None:
        return True
    if isinstance(value, bool):
        return not value
    if isinstance(value, str) and value.strip() == "":
        return True
    if isinstance(value, (list, dict)) and len(value) == 0:
        return True
    return False


def _gt(field_value: Any, value: Any) -> bool:
    """Greater-than comparison using numeric conversion."""
    try:
        return float(field_value) > float(value)
    except (TypeError, ValueError):
        return False


def _lt(field_value: Any, value: Any) -> bool:
    """Less-than comparison using numeric conversion."""
    try:
        return float(field_value) < float(value)
    except (TypeError, ValueError):
        return False
