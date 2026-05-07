# Phase 1 Review

### What's Good

- **Clean module structure**: `__init__.py`, `__main__.py`, `cli.py`, and `fetcher.py` are well-organized with clear responsibilities.
- **Good docstrings**: `fetcher.py` has thorough docstrings with Args/Returns/Raises sections for every public function.
- **Rate-limiting respect**: The `_throttle()` function with 100ms delay correctly implements SEC EDGAR's 10 req/s rate limit.
- **Robust CIK resolution**: `resolve_ticker_to_cik` handles ticker normalization (strip/upper), zero-padding to 10 digits, and raises `ValueError` when not found.
- **Comprehensive test coverage for fetcher**: `test_fetcher.py` covers happy paths, not-found cases, and HTTP errors for all four public functions.
- **Mock-based tests**: Tests use `unittest.mock.patch` correctly, avoiding real network calls.
- **CLI argument parsing**: `argparse` is used properly with sensible defaults (`--type 10-K`, optional `--output`).
- **`conftest.py` path injection**: Ensures `import sec_importer` works in pytest without needing `PYTHONPATH` set externally.
- **`_fetch_json` and `_fetch_text` helpers**: DRY utility functions for HTTP fetching with consistent error handling.
- **`get_cik_submissions` handles leading-zero stripping**: CIK normalization with `lstrip("0") or "0"` edge case is handled.

## Blocking Bugs

- **`cli.py` is a stub — no actual integration**: `cli.py` (line 23-24) only prints "Fetching..." and "Done." — it never calls `resolve_ticker_to_cik`, `get_latest_filing`, `download_filing_text`, or `parse_filing`. The README claims the CLI resolves ticker, fetches, parses, and prints JSON, but the code does none of that. This means `sec_importer AAPL --type 10-K` will not produce any useful output.
- **`parser.py` does not exist**: The README references `from sec_importer.parser import parse_filing`, but no `src/sec_importer/parser.py` file exists. Any programmatic API usage will crash with `ModuleNotFoundError`.
- **`FULL_TEXT_URL_NO_DASHES` is defined but unused**: `fetcher.py` line 28 defines `FULL_TEXT_URL_NO_DASHES` but never uses it. This is dead code and suggests incomplete implementation (the no-dashes URL variant is needed for some SEC endpoints).
- **`get_latest_filing` assumes flat lists inside `recent` dict**: The code accesses `filings.get("recent", {})` and then treats it as a dict with list values (`accessionNo`, `form`, etc.). However, the SEC submissions JSON schema has `recent` as a dict where each key is an accession number and the value is a dict of fields. The test mocks it as `{"accessionNo": [...], "form": [...]}` which is a different structure. This means the real API response will likely cause a `TypeError` or `KeyError` at runtime.
- **`test_parser.py` is a placeholder**: `test_parser.py` only contains `assert True` — it tests nothing real. The parser module doesn't exist, so there's nothing to test, but this is a gap in coverage.

## Non-Blocking Notes

- **`_throttle()` sleeps in `_fetch_json` and `_fetch_text` but also called again in `resolve_ticker_to_cik`**: The `resolve_ticker_to_cik` function calls `time.sleep` directly (line 73) AND calls `_throttle()` via `_fetch_json`/`_fetch_text` — double throttling is fine but inconsistent.
- **`resolve_ticker_to_cik` parses HTML with regex-like string splitting**: The CIK extraction (`href.split("CIK=")[1].split("&")[0]`) is fragile — if SEC changes the URL format, it will break. Consider using `BeautifulSoup` to find the `<a>` tag with `CIK=` in its href attribute more robustly.
- **`FULL_TEXT_URL` uses the old SEC `/Archives/edgar/full-text/` path**: SEC has migrated to a new URL format (`https://www.sec.gov/Archives/edgar/full-text/{accession_no}.txt` may still work, but the new format is `https://www.sec.gov/ix?doc=/Archives/edgar/data/{cik_first3}/{accession_no}/{doc}` or similar). This may need updating.
- **No user-agent header**: SEC EDGAR requires a valid User-Agent header. `requests.get` without one may get blocked.
- **`get_cik_submissions` strips leading zeros from CIK**: This is correct for the SEC API, but the function mutates the input in a way that could confuse callers who pass the original CIK string expecting it to be preserved.
- **`requirements.txt` lists `pytest` as a dependency**: `pytest` should be in `dev-dependencies` or `requirements-dev.txt`, not in the main `requirements.txt`.
- **No logging configuration**: The module sets up a logger but never configures it, so log messages will be silently dropped.

## Reusable Components

- **`_throttle()` + `_fetch_json()` + `_fetch_text()` pattern**: The combination of rate-limiting delay with generic JSON/text fetchers is a reusable HTTP client pattern for SEC EDGAR or similar APIs. Source: `src/sec_importer/fetcher.py` (lines 38-57)
- **`resolve_ticker_to_cik()` function**: A self-contained ticker-to-CIK resolver using SEC EDGAR HTML parsing. Could be extracted as a general-purpose SEC ticker lookup utility. Source: `src/sec_importer/fetcher.py` (lines 60-87)
- **`get_cik_submissions()` function**: Generic CIK filing index lookup from SEC's JSON endpoint. Reusable for any project needing SEC filing metadata. Source: `src/sec_importer/fetcher.py` (lines 90-102)

## Verdict

FAIL — CLI is a non-functional stub and parser module is missing, so the end-to-end pipeline described in the README cannot work.
