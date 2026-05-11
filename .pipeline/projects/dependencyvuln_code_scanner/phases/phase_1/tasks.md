# Phase 1 Tasks

- [x] Task 1: Project skeleton and CLI entry point
  - What: Set up the project structure, pyproject.toml, dependency declarations, and the click-based CLI with the `depvuln scan` command skeleton (argument parsing, --format flag, --cache flag).
  - Files: pyproject.toml, depvuln/__init__.py, depvuln/cli.py, depvuln/__main__.py, tests/__init__.py
  - Done when: Running `python -m depvuln scan --help` prints CLI help; `depvuln scan ./some-path` runs without import errors and prints a placeholder message; pyproject.toml declares click as a dependency; `pip install -e .` installs the package.

- [x] Task 2: Dependency parsers for npm and pip
  - What: Implement the `DependencyParser` base class with a `parse()` method signature, then concrete `NpmParser` (reads package-lock.json and yarn.lock) and `PipParser` (reads requirements.txt and Pipfile.lock). Each parser returns a list of dicts with keys: `name`, `version`, `ecosystem` (npm or pip).
  - Files: depvuln/parsers/__init__.py, depvuln/parsers/base.py, depvuln/parsers/npm_parser.py, depvuln/parsers/pip_parser.py
  - Done when: NpmParser correctly extracts ≥3 packages from a sample package-lock.json; PipParser correctly extracts ≥3 packages from a sample requirements.txt; both parsers handle missing files gracefully (return empty list); unit tests cover happy path and edge cases (malformed JSON, empty files).

- [x] Task 3: CVE fetcher with OSV API integration and SQLite caching
  - What: Implement `CveFetcher` that queries the OSV API (https://api.osv.dev/v1/query) for each dependency and caches results in a local SQLite database with a TTL-based expiration strategy. The fetcher should batch requests where possible and respect rate limits with simple debouncing.
  - Files: depvuln/cve/__init__.py, depvuln/cve/fetcher.py, depvuln/cve/cache.py
  - Done when: Fetcher returns a list of CVE records (with id, severity/CVSS, affected version ranges, descriptions) for a known vulnerable package; cached results are served without HTTP calls on a second fetch within TTL; uncached results expire after TTL; unit tests mock HTTP responses and verify cache hit/miss behavior.

- [x] Task 4: Vulnerability scorer and report generators
  - What: Implement `VulnScorer` that extracts CVSS v3.1 scores from OSV data and maps them to severity labels (CRITICAL ≥ 9.0, HIGH ≥ 7.0, MEDIUM ≥ 4.0, LOW < 4.0). Implement `ReportGenerator` with `to_json()` and `to_text()` methods that produce prioritized (descending severity) output. Text format must include severity bracket, package==version, CVE ID, CVSS score, description, and fix suggestion.
  - Files: depvuln/scorer.py, depvuln/reports/__init__.py, depvuln/reports/json_report.py, depvuln/reports/text_report.py
  - Done when: VulnScorer correctly maps CVSS scores to severity labels for all four tiers; JSON output is valid, parseable JSON with fields: severity, package, version, cve_id, cvss, description, fix; text output matches the example format from the spec; unit tests verify scoring boundaries and report serialization.

- [x] Task 5: Integration tests, README, and packaging
  - What: Write integration tests using sample npm and pip projects that verify end-to-end scan output (≥3 CVE findings each). Write a README with installation instructions, usage examples, and output samples. Ensure the package is buildable as a wheel and installable via pip.
  - Files: tests/integration/, tests/sample_projects/package-lock.json, tests/sample_projects/requirements.txt, README.md
  - Done when: Integration tests pass against sample projects; `depvuln scan` against sample npm project returns ≥3 CVE findings; `depvuln scan` against sample pip project returns ≥3 CVE findings; JSON output is valid; text output is human-readable; `pip install .` and `pip wheel .` both succeed; README covers install, usage, --format, --cache flags, and output examples.