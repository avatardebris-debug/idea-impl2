# Phase 1 Tasks

- [ ] Task 1: Project scaffolding
  - What: Create the Python package structure with pyproject.toml, package directory, and __init__.py
  - Files: pyproject.toml, url_health_checker/__init__.py, url_health_checker/__main__.py
  - Done when: `python -m url_health_checker --help` runs without error and shows help text

- [ ] Task 2: URL checker core module
  - What: Implement the `check_url` function that sends a HEAD request to a URL, captures status code, response time, and determines if the URL is up or down. Handle timeouts and connection errors gracefully.
  - Files: url_health_checker/checker.py
  - Done when: `check_url("https://httpbin.org/status/200")` returns a result dict with keys `url`, `status_code`, `response_time_ms`, and `is_up`; timeouts raise a configurable exception

- [ ] Task 3: Concurrent URL checking
  - What: Implement `check_urls_concurrent` that takes a list of URLs and a thread count, checks all URLs concurrently using `concurrent.futures.ThreadPoolExecutor`, and returns a list of results in the original URL order
  - Files: url_health_checker/checker.py (add function)
  - Done when: `check_urls_concurrent(["https://httpbin.org/status/200", "https://httpbin.org/status/404"], max_workers=4)` returns a list of result dicts in the same order as the input; runs faster than sequential for multiple URLs

- [ ] Task 4: CLI interface
  - What: Implement the CLI entry point that reads URLs from a text file (one URL per line), runs concurrent checks, and prints a formatted report table showing URL, status code, response time, and up/down status. Support --workers and --timeout flags.
  - Files: url_health_checker/cli.py, url_health_checker/__main__.py (update)
  - Done when: Running `python -m url_health_checker urls.txt` prints a table with headers and one row per URL; `--workers 8` and `--timeout 5` flags work correctly

- [ ] Task 5: Unit tests with mock HTTP responses
  - What: Write unit tests for `check_url`, `check_urls_concurrent`, and the CLI using `unittest.mock` to simulate HTTP responses without real network calls. Test happy path, timeouts, 4xx/5xx responses, and concurrent ordering.
  - Files: tests/test_checker.py, tests/test_cli.py, tests/__init__.py
  - Done when: `pytest tests/` passes all tests with 100% mock-based assertions (no real network requests); covers status codes 200, 404, 500, timeout, and connection error