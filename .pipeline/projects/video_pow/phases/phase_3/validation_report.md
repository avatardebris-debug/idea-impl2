# Validation Report — Phase 3
## Summary
- Tests: 55 passed, 14 failed
- Total test files: test_cli.py, test_core.py, test_describer.py, test_pipeline.py
- Phase 3 specific test files (test_harness_capabilities.py, test_dependency_system.py, test_all.py): NOT PRESENT
- Core files present: videopow/cli.py, videopow/core.py, videopow/pipeline.py, videopow/describer.py, and supporting modules

## Failures
14 tests failed across:
- test_cli.py: 9 failures (TypeError on result dict access, missing SystemExit raises)
- test_core.py: 4 failures (blur/brightness/contrast effects return None, overlay positions assertion)
- test_pipeline.py: 1 failure (assertion mismatch on effect name)

## Verdict: FAIL
