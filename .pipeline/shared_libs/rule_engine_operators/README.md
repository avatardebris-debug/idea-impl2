# rule_engine_operators

Standalone condition operator evaluation functions for rule-based systems.

## Functions

- `evaluate_condition(field_value, operator, value) -> bool` — Evaluate a single condition against a field value.
- `_is_empty(value) -> bool` — Check if a value is considered empty (None, empty string, False, empty collections).
- `_gt(field_value, value) -> bool` — Greater-than comparison with numeric coercion.
- `_lt(field_value, value) -> bool` — Less-than comparison with numeric coercion.

## Supported Operators

`contains`, `not_contains`, `equals`, `regex`, `is_empty`, `gt`, `lt`

## Source

Copied from: `/workspace/idea impl/.pipeline/projects/rule_based_triage_engine/workspace/rule_engine/operators.py`
