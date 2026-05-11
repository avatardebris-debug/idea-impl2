# Validation Report — Phase 1
## Summary
- Tests: 30 passed, 0 failed
## Verdict: PASS

All 30 tests passed covering:
- **CveCache** (4 tests): get/set, missing key, invalidate, TTL expiration
- **Integration** (7 tests): CLI help, directory scan, nonexistent file, npm JSON/text, pip JSON/text
- **Parsers** (8 tests): NpmParser (empty, malformed, missing, v1, v3), PipParser (empty, missing, Pipfile, requirements, comments)
- **Reports** (4 tests): JSON and text generators (empty and populated)
- **VulnScorer** (5 tests): critical/high/low/medium scoring, sorting

All required Phase 1 files are present:
- `pyproject.toml` — project config with click dependency
- `depvuln/__init__.py`, `depvuln/__main__.py`, `depvuln/cli.py` — CLI entry point
- `depvuln/parsers/base.py`, `npm_parser.py`, `pip_parser.py` — dependency parsers
- `depvuln/cve/fetcher.py`, `depvuln/cve/cache.py` — CVE fetcher with SQLite caching
- `depvuln/scorer.py` — vulnerability scorer
- `depvuln/reports/json_report.py`, `depvuln/reports/text_report.py` — report generators
- `tests/test_cache.py`, `tests/test_integration.py`, `tests/test_parsers.py`, `tests/test_reports.py`, `tests/test_scorer.py` — test suite
- `tests/sample_projects/package-lock.json`, `tests/sample_projects/requirements.txt` — sample projects
- `README.md` — documentation
