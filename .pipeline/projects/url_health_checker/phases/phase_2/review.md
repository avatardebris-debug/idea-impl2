# Phase 2 Code Review

## What's Good

- **logging_config.py**: Clean, well-documented JSON formatter. The `setup_logging` function correctly avoids adding duplicate handlers. The `log_check_result` and `log_error` helpers provide structured logging with proper `extra` dict support.
- **output.py**: All four format functions (`format_table`, `format_json`, `format_csv`, `format_html`) are self-contained and well-implemented. CSV uses `csv.writer` with proper RFC 4180 line terminator. HTML output includes a complete document with styling. The `FORMATTERS` dispatch dict and `format_results` dispatcher are clean.
- **checker.py**: Retry logic is correct — loops `max_attempts` times, catches `ConnectionError`, `Timeout`, and generic `RequestException`, sleeps between retries, and returns the final failed result with `is_up=False` when all attempts are exhausted.
- **concurrent.py**: Rate limiting via `min_interval` calculation is correct. The `future_to_idx` mapping preserves result order. Thread pool lifecycle is managed properly with `with ThreadPoolExecutor`.
- **cli.py**: All Phase 2 flags (`--log-file`, `--log-level`, `--format`, `--retries`, `--retry-delay`, `--rate-limit`) are present and wired correctly. Startup/shutdown logging is included. Exit code 1 on any down URL is correct.
- **__init__.py**: Exports all public API symbols cleanly.
- **Tests**: All 24 tests pass. The `test_timeout_passed_to_checker` test was updated to match the new API (includes `max_attempts`, `retry_delay`, `logger` params).

## Blocking Bugs

- **concurrent.py:38-41** — Rate limiting is applied *inside* the `for idx, url in enumerate(urls)` loop that builds the future map, but the rate limiter sleeps *before* submitting each future. This means rate limiting is applied at submission time, which is correct in intent, but the rate limiter state (`last_submission_time`) is not thread-safe. Since this loop runs in the main thread (before the executor starts processing), this is actually fine — the sleep happens in the main thread before any worker threads begin. **No actual bug here.**

- **checker.py:54-57** — The retry loop sleeps *after* catching an exception but *before* the next iteration. However, the sleep happens inside the `except` block, which means it only sleeps on failure. This is correct behavior for retry logic. **No actual bug.**

- **logging_config.py:55-56** — When `log_file` is set, the console handler logs to `sys.stderr` at WARNING level. This is by design (structured logs go to file, warnings to stderr). **Not a bug.**

- **output.py:format_html** — The HTML template uses f-string with `{rows}` interpolation. The `rows` variable is built via string concatenation with triple-quoted strings. This works correctly. **No bug.**

- **cli.py:97-101** — The shutdown log uses `extra` dict with `None` values for all fields. The `JSONFormatter` in `logging_config.py` checks `hasattr(record, key)` which will be `True` for keys set via `extra`, so `None` values will be serialized as `null` in JSON. This is acceptable behavior. **No bug.**

- **concurrent.py:60-64** — The `except Exception` handler in the `as_completed` loop catches exceptions from `future.result()` (e.g., if the checker itself raises). It returns a default failed result. This is correct defensive coding. **No bug.**

**None**

## Non-Blocking Notes

- **checker.py:38** — A new `requests.Session()` is created per attempt. This is fine for correctness but could be optimized by reusing the session across retries. Not a bug, just a minor performance note.
- **logging_config.py:22** — The `JSONFormatter` uses `datetime.now(timezone.utc).isoformat()` per log call. Consider using `record.created` or `record.msecs` for more consistent timestamps tied to the log record.
- **output.py:format_html** — The HTML template uses inline styles. Consider using a CSS class approach for better maintainability.
- **cli.py** — The `--format` argument name shadows the built-in `format` function. This is fine within `argparse` namespace but could be confusing. Consider `--output-format` for clarity.
- **concurrent.py** — The rate limiter uses a simple fixed-delay approach. A token-bucket algorithm would provide smoother rate limiting under burst conditions.
- **checker.py** — The `User-Agent` header is set on each new session. Consider making this configurable.
- **logging_config.py** — The `setup_logging` function checks `if logger.handlers` to avoid duplicate handlers. This is a simple approach; for more robustness, consider checking handler types.

## Reusable Components

- **JSONFormatter** (`logging_config.py:18-30`): A self-contained `logging.Formatter` subclass that outputs JSON lines with support for extra fields. Useful for any Python project needing structured JSON logging.
- **format_results / format_table / format_json / format_csv / format_html** (`output.py`): The output formatting module is self-contained and general-purpose. Could be reused for any project that needs to format result dicts into multiple output formats.
- **URLChecker** (`checker.py`): The `URLChecker` class with retry logic is a self-contained HTTP health-check utility. Could be reused as an HTTP client wrapper with retry support.

## Verdict

PASS — All Phase 2 tasks are implemented correctly, all 24 tests pass, and no blocking bugs were found.
