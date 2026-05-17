# Test Plan — VAST.ai Instance Initializer (Phase 1 MVP)

## Architecture Overview

```
vastai_init/
├── __init__.py          # Package entry, __version__
├── batch/
│   ├── __init__.py      # Public exports
│   ├── config.py        # BatchConfig, BatchPresetRef, TimingConfig, load_batch_config, find_batch_configs
│   ├── validator.py     # validate_batch_config, validate_batch_config_raw, BatchConfigValidationError
│   ├── orchestrator.py  # BatchOrchestrator, LaunchTask, BatchResult
│   └── state.py         # BatchState, InstanceState, save_batch_state, load_batch_state
└── presets/
    └── default.yaml     # Example preset
```

## Test Coverage Matrix

| Module | Class/Function | Tests | Status |
|--------|---------------|-------|--------|
| config.py | BatchPresetRef | ✅ defaults, count, to_dict, from_dict, from_dict_defaults | Done |
| config.py | TimingConfig | ✅ defaults, custom, to_dict, from_dict, from_dict_defaults | Done |
| config.py | BatchConfig | ✅ to_dict_roundtrip | Done |
| config.py | Schema constants | ✅ required, optional, preset_ref | Done |
| config.py | _parse_batch_config | ✅ minimal, full, string_presets, empty_presets | Done |
| config.py | load_batch_config | ✅ valid, missing file, bad yaml, non-mapping | Done |
| config.py | find_batch_configs | ✅ existing dir, nonexistent dir, default dir | Done |
| validator.py | validate_batch_config | ✅ valid, empty_name, empty_presets, missing_file, zero/neg count, negative delay, invalid stagger, zero concurrency, zero timeout, multiple errors | Done |
| validator.py | validate_batch_config_raw | ✅ valid, missing fields, invalid types | Done |
| orchestrator.py | LaunchTask | ✅ defaults, custom status | Done |
| orchestrator.py | BatchResult | ✅ defaults | Done |
| orchestrator.py | _build_tasks | ✅ single/multi preset, multi count, no timing, delay, stagger, stagger single | Done |
| orchestrator.py | _update_status | ✅ launched, failed | Done |
| orchestrator.py | _get_batch_status | ✅ all pending, all completed, mixed, no tasks | Done |
| orchestrator.py | launch (dry_run) | ✅ single, multiple, concurrency, timing, empty, preserves states | Done |
| orchestrator.py | launch (state) | ✅ save/load, resume | Done |
| orchestrator.py | helpers | ✅ get_task_count, get_pending_count, get_completed_count, get_failed_count, get_result | Done |
| orchestrator.py | integration | ✅ full dry_run, callback, result accuracy | Done |
| state.py | BatchState serialization | ✅ save/load, missing file, nested dirs | Done |

## Gap Analysis — Missing Tests

### 1. BatchPresetRef edge cases
- `__eq__` comparison (if implemented)
- `__repr__` (if implemented)
- Invalid preset_path (empty string, None)

### 2. TimingConfig edge cases
- Negative values
- Very large values
- `__repr__` (if implemented)

### 3. BatchConfig edge cases
- `__repr__` (if implemented)
- `__eq__` comparison
- Very large concurrency/timeout values

### 4. validator.py additional edge cases
- `validate_batch_config_raw` with non-dict presets
- `validate_batch_config_raw` with string presets
- `validate_batch_config_raw` with missing timing
- `validate_batch_config_raw` with missing concurrency
- `validate_batch_config_raw` with missing timeout
- `validate_batch_config` with valid preset file (should not raise)

### 5. orchestrator.py additional edge cases
- `launch` with timeout exceeded (asyncio.TimeoutError)
- `launch` with mixed success/failure (simulated)
- `_save_state` when state_path is None
- `_save_state` when batch_state is None
- `get_tasks` returns list copy
- `on_instance_status` callback with errors
- `launch` with 0 concurrency (edge case)
- Task status transitions (pending → launching → completed)
- `launch` with state file that has fewer instances than tasks

### 6. state.py additional edge cases
- `load_batch_state` with corrupted JSON
- `load_batch_state` with missing required fields
- `save_batch_state` with empty state
- `InstanceState` defaults
- Round-trip with all fields populated

### 7. config.py additional edge cases
- `load_batch_config` with YAML containing extra fields
- `load_batch_config` with deeply nested preset paths
- `find_batch_configs` with subdirectories
- `find_batch_configs` with hidden files
- `_parse_batch_config` with None presets

### 8. Integration tests
- End-to-end: load config → validate → orchestrate → check results
- Config with multiple presets, timing, concurrency, state persistence
- Error handling in full pipeline

### 9. Edge cases across all modules
- Unicode in preset paths
- Very long preset paths
- Special characters in batch names
- Concurrent batch launches

## Test Execution Plan

### Phase 1: Unit Tests (Existing — Complete)
- All tests in `test_batch_config.py` and `test_batch_orchestrator.py`
- Run: `pytest tests/ -v`

### Phase 2: Additional Unit Tests (To Add)
1. `test_batch_config_edge_cases.py` — Edge cases for config classes
2. `test_validator_edge_cases.py` — Additional validator scenarios
3. `test_orchestrator_edge_cases.py` — Orchestrator edge cases
4. `test_state_edge_cases.py` — State serialization edge cases

### Phase 3: Integration Tests (To Add)
1. `test_integration.py` — End-to-end batch flow tests

### Phase 4: Regression & Robustness
1. Property-based tests (hypothesis) for config parsing
2. Stress tests for large batch sizes
3. Concurrency tests

## Test Conventions

- Use `pytest` with class-based test organization
- Use `tmp_path` fixture for file-based tests
- Use `MagicMock` for callback verification
- Use `asyncio.run()` for async test methods
- Helper function `_make_config()` for config creation
- Test class naming: `Test<ClassName>` or `Test<Feature>`
- Test method naming: `test_<scenario>`
