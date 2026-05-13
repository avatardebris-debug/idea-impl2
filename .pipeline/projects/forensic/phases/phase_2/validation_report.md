# Validation Report — Phase 2
## Summary
- Tests: 172 passed, 99 failed
## Verdict: FAIL

### Details
- 271 tests collected and executed.
- 172 tests passed.
- 99 tests failed across multiple test modules:
  - `tests/test_models.py`: Failures due to `AttributeError` (missing `to_json`, `to_dict` methods) and `pydantic_core.ValidationError` on `AnalysisResult`, `FraudReport`, `RedFlag`, and `Recommendation` models.
  - `tests/test_normalization.py`: Failures due to `assert None == <value>` — normalization extraction functions returning `None` instead of expected values.
  - `tests/test_scoring.py`: Failures due to `pydantic_core.ValidationError` on `RedFlag` model.
- Core files are present in the workspace (src/forensic/ contains all expected modules including pipeline.py, scoring.py, red_flags.py, normalization.py, models.py, etc.).
- The failures indicate bugs in the implementation: missing model methods, Pydantic validation errors, and normalization extraction returning None.
