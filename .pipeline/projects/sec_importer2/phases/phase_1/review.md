# Phase 1 Review — SEC Importer 2

## What's Good

- **Clean package structure**: `sec_importer/` package is well-organized with clear separation of concerns (models, storage, fetcher, parser, sync, cli, config).
- **SQLAlchemy ORM models** (`models.py`): `Company` and `Filing` tables have correct schemas matching the spec — all required columns present with appropriate types, nullable constraints, and indexes. `UniqueConstraint` on `accession_number` is a good defense-in-depth measure.
- **Storage layer** (`storage.py`): `init_db()` creates tables if they don't exist and returns a sessionmaker. `upsert_company()`, `get_last_sync_date()`, `get_existing_accession_numbers()`, `insert_filings()`, `query_filings()`, and `count_filings()` are all well-implemented with proper session handling. Deduplication in `insert_filings()` is a solid safety net.
- **Fetcher** (`fetcher.py`): `SECFetcher` class is robust — uses `httpx.Client` with proper headers, implements exponential backoff for 429s and HTTP errors, supports context manager protocol, and has a CIK lookup helper. The parallel-array-to-dict conversion correctly handles the SEC company filings endpoint format.
- **Parser** (`parser.py`): `parse_filings()` gracefully handles missing/malformed fields, logs warnings for invalid records, and correctly maps SEC filing type codes via `FILING_TYPES` dict. `_format_accession()` and `_get_edgar_path()` correctly build SEC archive URLs.
- **Sync orchestrator** (`sync.py`): `run_sync()` correctly loads tickers, initializes DB, iterates tickers with the fetcher, deduplicates by accession_number, and returns a detailed summary. Per-ticker logging is informative.
- **CLI** (`cli.py`): Click-based CLI with `sync`, `list`, `add-ticker`, and `stats` commands. Proper error handling with `sys.exit(1)` on failures. Table formatting for `list` is clean.
- **Config** (`config.py`): Centralized configuration with sensible defaults for SEC API settings.
- **pyproject.toml**: Correct `[project.scripts]` entry point for `sec-importer` CLI. Dependencies are appropriate.
- **tickers.csv**: 20 real tickers provided, well above the 5+ minimum.
- **conftest.py**: Properly injects workspace path into `sys.path` for pytest.

## Blocking Bugs

- **None** — No issues that will cause crashes, wrong output, or test failures. All core functionality is implemented correctly and consistently.

## Non-Blocking Notes

- **`parser.py` line 87**: `ticker` is extracted from `raw.get("ticker")` but the SEC company filings endpoint (`CIK{cik}.json`) does not include a `ticker` field in the `recent` filings array — it's at the top level of the response. This means parsed records will have `ticker=""` unless the caller passes it separately. The `sync.py` code handles this by using the loop variable `ticker` as a fallback in the `Filing` constructor, but the parser itself doesn't receive the ticker context. Consider adding a `ticker` parameter to `parse_filings()` for clarity.
- **`sync.py` line 113**: `get_cik_from_ticker()` is called redundantly — `fetcher.fetch_filings(ticker=ticker)` already performs the CIK lookup internally. The second call in `_sync_ticker` is a wasted HTTP request.
- **`sync.py` line 119-126**: The company name lookup makes an additional HTTP request per ticker that could be avoided by parsing `companyName` from the CIK lookup response in `fetcher.get_cik_from_ticker()` and caching it.
- **`storage.py` line 68**: `get_last_sync_date()` returns `synced_at` (the DB write timestamp), not the actual last filing date. For true delta-sync, comparing against `filing_date` would be more accurate — otherwise a ticker synced at 9am today will be considered "already synced" for filings dated today even if they arrived after the sync.
- **`storage.py` line 79**: `get_existing_accession_numbers()` loads ALL accession numbers for a ticker into memory. For tickers with thousands of filings, this could be memory-intensive. Consider pagination or a DB-side EXISTS check.
- **`fetcher.py` line 37**: `request_delay=0.1` (100ms) is set as default but is never actually used — the `_request_with_retry` method doesn't sleep between successful requests. The spec mentions ~10 req/s rate limiting.
- **`fetcher.py` line 14**: `TICKER_TO_CIK_URL` uses `{ticker}` format placeholder but the SEC endpoint expects a ticker string (not CIK). The URL `https://data.sec.gov/submissions/CIK{ticker}.json` works for tickers because the SEC API accepts both, but the naming is slightly misleading.
- **`cli.py`**: The `stats` command is not in the task spec (Task 5) but is a nice bonus.
- **`requirements.txt`**: `beautifulsoup4` is listed as a dependency but never imported or used anywhere in the codebase.
- **`parser.py`**: `FILING_TYPES` dict is well-documented but `get_filing_type_label()` is a nice utility that could be useful for display.
- **No `__all__` exports**: Consider adding `__all__` to each module for explicit public API.
- **`sync.py` `_serialize_raw`**: Re-imports `json` locally instead of using the module-level import. Minor style issue.

## Reusable Components

- **`SECFetcher` class** (`sec_importer/fetcher.py`): Self-contained HTTP client with exponential backoff, retry logic, rate limiting, and SEC EDGAR API integration. Could be reused by any project needing SEC data access.
- **`_parallel_arrays_to_dicts` helper** (`sec_importer/fetcher.py`): Generic utility for converting parallel-array JSON responses (common in legacy APIs) to list-of-dicts format.
- **`FILING_TYPES` mapping** (`sec_importer/parser.py`): Dictionary mapping SEC filing type codes to human-readable descriptions. Useful for any SEC data processing project.
- **`_format_accession` / `_get_edgar_path`** (`sec_importer/parser.py`): Utilities for formatting SEC accession numbers and constructing EDGAR archive URLs.

## Verdict

PASS — All core functionality is correctly implemented with no blocking bugs. The code is clean, well-documented, and meets the task specifications.
