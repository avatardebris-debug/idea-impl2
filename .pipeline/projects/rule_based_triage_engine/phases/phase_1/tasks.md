# Phase 1 Tasks

- [ ] Task 1: Define data models (Rule, Condition, Action dataclasses)
  - What: Create the core dataclasses that represent rules, conditions, and actions. These are the foundational types the rest of the engine builds on.
  - Files: `rule_engine/__init__.py`, `rule_engine/models.py`
  - Done when: Rule, Condition, and Action dataclasses are defined with all required fields; `__init__.py` exports them; dataclasses support JSON serialization/deserialization via `to_dict()` and `from_dict()` class methods

- [ ] Task 2: Implement condition operator logic
  - What: Build the operator evaluation functions that compare an email field value against a condition's value. Supports: `contains`, `not_contains`, `equals`, `regex`, `is_empty`, `gt`, `lt`.
  - Files: `rule_engine/operators.py`
  - Done when: Each operator correctly evaluates against string, numeric, and boolean email fields; `regex` uses Python `re` module; `is_empty` handles None, empty string, and False; `gt`/`lt` handle numeric comparisons; unicode strings are handled without errors

- [ ] Task 3: Implement the RuleEngine evaluation class
  - What: Build `RuleEngine` that loads rules, evaluates an email dict against all rules, and returns matching actions sorted by priority.
  - Files: `rule_engine/engine.py`
  - Done when: `evaluate(email: dict) -> list[Action]` returns all matching actions sorted by priority (highest first); disabled rules are skipped; multiple rules with different priorities produce correctly ordered actions; no matching rules returns empty list; `evaluate_batch` processes multiple emails

- [ ] Task 4: Implement RuleStore for JSON persistence
  - What: Build `RuleStore` class that loads rules from and saves rules to JSON files, with proper serialization/deserialization of dataclass objects.
  - Files: `rule_engine/store.py`
  - Done when: `save(rules)` writes a list of Rule objects to a JSON file; `load()` reads rules back without data loss; file creation and directory handling work correctly; invalid JSON raises a clear error

- [ ] Task 5: Write unit tests (minimum 15 test cases)
  - What: Comprehensive unit tests covering all condition operators, rule matching logic, priority ordering, RuleStore persistence, and edge cases.
  - Files: `tests/test_engine.py`, `tests/test_operators.py`, `tests/test_store.py`
  - Done when: All test cases pass; coverage includes: `contains`, `not_contains`, `equals`, `regex`, `is_empty`, `gt`, `lt` operators; priority ordering with multiple rules; RuleStore save/load round-trip; empty body handling; unicode subject handling; no-match graceful no-op; disabled rule skipping; minimum 15 test cases total