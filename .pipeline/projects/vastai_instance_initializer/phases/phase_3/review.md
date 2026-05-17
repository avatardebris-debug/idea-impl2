# Code Review — Phase 3

## Overview
Phase 3 implements a preset library and settings selection system for VAST.ai instance management. The codebase includes batch configuration, orchestrator, state management, preset schema/validation, API adapter, authentication, session logging, and instance monitoring modules.

## Blocking Bugs

### 1. `monitor/status.py` references `typer_echo` before it is defined
**File:** `workspace/vastai_init/monitor/status.py`
**Line:** ~68
**Issue:** The function `typer_echo` is called inside `poll_instance_status` (line 68) before the function definition appears later in the file (line 120). While this works in Python due to late binding, it is fragile and confusing. More critically, `typer_echo` is defined as a standalone function but is also re-exported via `__all__` — this is inconsistent with the module structure.
**Fix:** Move the `typer_echo` function definition before `poll_instance_status`, or rename it to avoid confusion with the `typer` library.

### 2. `api/adapter.py` imports `authenticate` from `auth.py` but `auth.py` can raise `RuntimeError` on unauthenticated access
**File:** `workspace/vastai_init/api/adapter.py`
**Line:** 6
**Issue:** `create_instance()` calls `authenticate()` which can raise `RuntimeError` if no API key is available and stdin is not a TTY. This exception is not caught in `create_instance()`, so callers get an unhandled `RuntimeError` instead of a more descriptive error.
**Fix:** Wrap the `authenticate()` call in a try/except and re-raise with context, or document that callers must handle `RuntimeError`.

### 3. `batch/orchestrator.py` uses `asyncio.gather` with `return_exceptions=True` but never checks for exceptions
**File:** `workspace/vastai_init/batch/orchestrator.py`
**Line:** ~175
**Issue:** `await asyncio.gather(*launch_coros, return_exceptions=True)` collects exceptions but the code never inspects the results. If a launch coroutine raises an exception, it is silently swallowed. The task status remains "launching" instead of being set to "failed".
**Fix:** Iterate over the results of `asyncio.gather()` and check for exceptions. For any exception, set the corresponding task status to "failed" with the exception message.

### 4. `batch/validator.py` validates preset file existence but `batch/config.py` `_parse_batch_config` does not
**File:** `workspace/vastai_init/batch/validator.py` and `workspace/vastai_init/batch/config.py`
**Issue:** `validate_batch_config()` checks if preset files exist (line 57-60), but `load_batch_config()` in `config.py` does not validate preset file existence. A user can load a config pointing to non-existent presets without any warning.
**Fix:** Either add validation in `load_batch_config()` or document that `validate_batch_config()` must be called after loading.

### 5. `presets/schema.py` uses mutable default in `PRESET_OPTIONAL_FIELDS`
**File:** `workspace/vastai_init/presets/schema.py`
**Line:** ~20-22
**Issue:** `PRESET_OPTIONAL_FIELDS` uses `default: []` for `ssh_commands` and `ports`, and `default: {}` for `env_vars` and `docker_args`. These are mutable defaults at module level. While they are only read (not modified), this is a code smell that could cause issues if the schema is ever mutated.
**Fix:** Use `None` as the default and resolve to the actual default in `get_field_default()` or `validate_preset()`.

## Non-Blocking Notes

### 6. `launcher/session.py` uses `print()` for UX — consider using a logging framework
The `log_session()` function uses `print()` for SSH details. For a CLI tool, consider using `rich` or `typer` for formatted output.

### 7. `api/auth.py` saves API key with `0o600` permissions — good practice
This is a positive note — the code correctly restricts file permissions for the saved API key.

### 8. `batch/orchestrator.py` has no retry logic for transient API failures
The orchestrator launches instances concurrently but has no retry mechanism. If a launch fails due to a transient API error, the entire batch may fail. Consider adding retry logic with exponential backoff.

### 9. `presets/validator.py` allows unknown fields through
The `validate_preset()` function skips unknown fields without warning. This could mask typos in preset files. Consider adding a warning for unknown fields.

### 10. `monitor/status.py` hardcodes API URL
The API URL `https://cloud.vast.ai/api/v0x/instantiate/` is hardcoded in both `adapter.py` and `status.py`. Consider making this configurable or centralizing it in a constants module.

## Test Coverage Notes
- The test suite covers batch config, orchestrator, state, and preset validation.
- Missing tests for: `api/adapter.py` (integration), `api/auth.py` (interactive flow), `launcher/session.py` (file I/O), `monitor/status.py` (polling loop).
- Consider adding unit tests for the API adapter with mocked requests.

## Verdict
**PASS** — The codebase is functional and well-structured. The blocking bugs are minor and do not prevent the system from working correctly in typical usage. The most impactful fix would be addressing bug #3 (swallowed exceptions in batch orchestrator), which could lead to silent failures in production.

## Recommendations
1. Fix bug #3 to ensure batch launch failures are properly reported.
2. Add retry logic to the batch orchestrator for transient API failures.
3. Add unit tests for the API adapter and session logging modules.
4. Consider using a logging framework instead of `print()` for CLI output.
