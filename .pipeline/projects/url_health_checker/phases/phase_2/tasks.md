# Phase 2 Tasks

- [ ] Task 6: Add structured logging (JSON or text)
  - What: Create a logging module that configures structured logging (JSON format by default) for the URL Health Checker. Log every URL check result (url, status_code, response_time_ms, is_up) at INFO level, errors at ERROR level, and startup/shutdown events. Add a --log-file CLI flag to write logs to a file (default: stdout).
  - Files: src/url_health_checker/logging_config.py (new), src/url_health_checker/cli.py (modify — add --log-file flag, wire logger), src/url_health_checker/checker.py (modify — accept and use logger), src/url_health_checker/concurrent.py (modify — log per-url results)
  - Done when: CLI accepts --log-file flag; every check produces a JSON log line with keys {timestamp, level, url, status_code, response_time_ms, is_up}; logs written to file when --log-file is set; existing CLI output (table) is unaffected

- [ ] Task 7: Support multiple output formats (JSON, CSV, HTML)
  - What: Add a --format CLI flag (default: "table") supporting "table" (current text table), "json" (array of result objects), "csv" (header + rows), and "html" (styled HTML table). Move format logic into a dedicated output module.
  - Files: src/url_health_checker/output.py (new), src/url_health_checker/cli.py (modify — add --format flag, delegate to output module)
  - Done when: --format json outputs valid JSON array; --format csv outputs RFC 4180-compatible CSV with header row; --format html outputs a complete HTML document with a styled table; --format table (default) preserves existing aligned text table; all formats include url, status_code, response_time_ms, is_up fields

- [ ] Task 8: Add retry logic with configurable attempts
  - What: Add retry support to URLChecker.check() with configurable max_attempts and delay_between_attempts. On ConnectionError or Timeout, retry up to max_attempts times before returning a failed result. Add --retries and --retry-delay CLI flags.
  - Files: src/url_health_checker/checker.py (modify — add retry loop with configurable attempts/delay), src/url_health_checker/concurrent.py (modify — pass retry params to URLChecker), src/url_health_checker/cli.py (modify — add --retries and --retry-delay flags)
  - Done when: URLChecker retries on ConnectionError/Timeout up to max_attempts times; --retries flag sets max attempts (default 1 = no retry); --retry-delay flag sets seconds between retries (default 1); successful retry returns the successful result; exhausted retries return is_up=False with last error info

- [ ] Task 9: Add rate limiting / delay between requests
  - What: Add rate limiting to concurrent checking so that no more than N requests are sent per second. Use a token-bucket or fixed-delay approach. Add --rate-limit CLI flag.
  - Files: src/url_health_checker/concurrent.py (modify — add rate limiter using threading.Semaphore or time.sleep between submissions), src/url_health_checker/cli.py (modify — add --rate-limit flag)
  - Done when: --rate-limit flag accepts requests-per-second (default unlimited); when set, the checker enforces the rate by spacing out request submissions; concurrent behavior is preserved (multiple workers still run in parallel, just rate-limited at submission)

- [ ] Task 10: Add Dockerfile and CI/CD pipeline
  - What: Create a multi-stage Dockerfile that builds a slim Python image with the package installed. Add a GitHub Actions workflow that runs linting (flake8), unit tests (pytest), and builds the Docker image on push/PR.
  - Files: Dockerfile (new), .github/workflows/ci.yml (new), pyproject.toml (modify — add dev dependencies for linting if needed)
  - Done when: Dockerfile builds successfully with `docker build`; CI workflow runs on push/PR and passes linting + tests; Docker image runs `url-health-checker --help` successfully

- [ ] Task 11: Add integration tests against real URLs
  - What: Add integration test file that checks a small set of well-known URLs (e.g., httpbin.org/status/200, http://example.com) to verify end-to-end CLI behavior with real HTTP responses. Use pytest with a marker to skip in CI if network is unavailable.
  - Files: tests/test_integration.py (new)
  - Done when: Integration tests verify that known-up URLs return is_up=True and known-down URLs return is_up=False; tests run with `pytest tests/test_integration.py --run-integration`; tests are skippable via --run-integration flag or environment variable

- [ ] Task 12: Publish to PyPI
  - What: Prepare the package for PyPI release: verify pyproject.toml metadata, add LICENSE, update README, and publish.
  - Files: LICENSE (new), README.md (new or update), pyproject.toml (verify metadata), setup.cfg or twine config (if needed)
  - Done when: Package builds with `python -m build` producing sdist and wheel; metadata (name, version, description, dependencies) is correct; package installs cleanly via `pip install dist/url_health_checker-*.whl`; README documents usage with all Phase 2 features