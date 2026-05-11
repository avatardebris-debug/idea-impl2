# rule_engine_store

JSON persistence layer for rule-based systems.

## Classes

- `RuleStoreError(Exception)` — Custom exception for store operations.
- `RuleStore` — Load and save dataclass-based rule objects to/from JSON files with directory creation and error handling.

## Usage

```python
store = RuleStore()
store.save(rules, "path/to/rules.json")
loaded = store.load("path/to/rules.json")
```

## Source

Copied from: `/workspace/idea impl/.pipeline/projects/rule_based_triage_engine/workspace/rule_engine/store.py`
