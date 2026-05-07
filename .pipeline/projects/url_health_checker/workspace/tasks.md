# Phase 1 Tasks

- [x] Task 1: Create project structure and package setup
  - What: Create the Python package directory layout, __init__.py, and pyproject.toml for the url_health_checker package
  - Files: pyproject.toml, src/url_health_checker/__init__.py, src/url_health_checker/__main__.py
  - Done when: Package is importable via `python -m url_health_checker` and pyproject.toml defines the project metadata and entry point

- [x] Task 2: Implement URL checker core logic
  - What: Create the URLChecker class with HEAD request support, timeout handling, and response analysis
  - Files: src/url_health_checker/checker.py
  - Done when: URLChecker.check() returns a dict with url, status_code, response_time_ms, and is_up fields for valid URLs and handles timeouts/errors gracefully

- [x] Task 3: Implement concurrent URL checking
  - What: Create the concurrent checking module using ThreadPoolExecutor for parallel URL checks
  - Files: src/url_health_checker/concurrent.py
  - Done when: check_urls_concurrent() accepts a list of URLs and max_workers, returns results in input order, and properly manages thread lifecycle

- [x] Task 4: Implement CLI interface
  - What: Create the command-line interface with argparse for input file, timeout, and worker count options
  - Files: src/url_health_checker/cli.py
  - Done when: CLI accepts --input, --timeout, and --workers flags, reads URLs from file, runs checks, and prints a formatted table to stdout

- [x] Task 5: Write unit tests
  - What: Create comprehensive unit tests for all modules using pytest
  - Files: tests/test_checker.py, tests/test_concurrent.py, tests/test_cli.py
  - Done when: All tests pass with `python -m pytest tests/` and cover happy paths, error paths, and edge cases

# Phase 2 Tasks

- [x] Task 6: Add structured JSON logging
  - What: Create logging_config.py with JSONFormatter, setup_logging, log_check_result, and log_error
  - Files: src/url_health_checker/logging_config.py
  - Done when: Structured JSON logs are emitted to file or stdout with URL, status_code, response_time_ms, and is_up fields

- [x] Task 7: Add multi-format output (JSON, CSV, HTML)
  - What: Extend output.py with format_json, format_csv, format_html and format_results dispatcher
  - Files: src/url_health_checker/output.py
  - Done when: format_results(fmt="json"/"csv"/"html"/"table") produces correct output for each format

- [x] Task 8: Add CLI flags for logging, output format, retries, retry-delay, and rate-limit
  - What: Extend cli.py with --log-file, --log-level, --format, --retries, --retry-delay, --rate-limit
  - Files: src/url_health_checker/cli.py
  - Done when: All new flags are wired through to the checker and concurrent modules

- [x] Task 9: Update tests for Phase 2 changes
  - What: Update test_timeout_passed_to_checker and add tests for new functionality
  - Files: tests/test_checker.py, tests/test_cli.py, tests/test_concurrent.py
  - Done when: All 24 tests pass with `python -m pytest tests/`

- [x] Task 10: Code review, reusable components, and shared_libs
  - What: Write review.md, identify reusable components, copy to shared_libs, update reusable_tools.md
  - Files: phases/phase_2/review.md, shared_libs/*, state/reusable_tools.md
  - Done when: Review written with PASS verdict, 3 components copied to shared_libs, reusable_tools.md updated
