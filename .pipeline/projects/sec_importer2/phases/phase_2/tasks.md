# Phase 2 Tasks

- [ ] Task 1: Add `FilingContent` model and `filing_contents` table
  - What: Add a `FilingContent` SQLAlchemy ORM model in `models.py` with columns: `id`, `filing_id` (FK), `content_type` (xbrl/html), `content_data` (JSON/text), `parse_status` (success/partial/failed), `parse_error` (nullable string), `parsed_at` (datetime). Also add `upsert_filing_content` and `get_filing_content_data` helpers in `storage.py`.
  - Files: `sec_importer/models.py`, `sec_importer/storage.py`
  - Done when: `FilingContent` model exists in `models.py`, `init_db()` creates the `filing_contents` table, `storage.py` has `upsert_filing_content(session, filing_id, content_type, content_data, parse_status, parse_error)` and `get_filing_content_data(session, filing_id, content_type)` helpers, and the existing `companies`/`filings` tables still work unchanged.

- [ ] Task 2: Expand XBRL parser to extract 20+ financial facts
  - What: Extend `KEY_CONCEPTS` in `xbrl_parser.py` to cover at least 20 financial concepts including: revenue, cost of revenue, gross profit, operating income, net income, EPS (basic & diluted), total assets, total liabilities, total equity, cash and equivalents, accounts receivable, inventory, property plant equipment, long-term debt, current portion of debt, operating cash flow, investing cash flow, financing cash flow, shares outstanding, effective tax rate, operating expenses, interest expense, income tax expense, goodwill, intangible assets, retained earnings, current portion of long-term debt, short-term debt.
  - Files: `sec_importer/parser/xbrl_parser.py`
  - Done when: `KEY_CONCEPTS` maps at least 20 metric names to US-GAAP XBRL concept URIs. `_extract_key_metrics` returns all 20+ metrics. The parser handles missing concepts gracefully (skips them, does not crash).

- [ ] Task 3: Add `parse_filings` batch function and integrate parsing into `sync`
  - What: Add a `parse_filings` function in `parser/__init__.py` that takes a list of filing dicts and parses each one (auto-detecting XBRL vs HTML based on filing type). Update `sync.py` to call `parse_filings` after storing new filings so that `sec-importer sync` fetches new filings AND parses them end-to-end.
  - Files: `sec_importer/parser/__init__.py`, `sec_importer/sync.py`
  - Done when: `parse_filings(filing_list)` returns a list of parse results. `run_sync` in `sync.py` calls `parse_filings` for newly inserted filings and stores the parsed content via `upsert_filing_content`. Running `sec-importer sync` produces parsed XBRL/HTML content in the DB.

- [ ] Task 4: Add CLI `show` command to display parsed filing content
  - What: Add a `show` CLI command in `cli.py` that takes a filing ID or accession number and displays the parsed content (XBRL metrics or HTML sections) in a readable format.
  - Files: `sec_importer/cli.py`
  - Done when: `sec-importer show <filing_id>` prints parsed XBRL metrics as a table or HTML sections as text. `sec-importer show <accession_number>` works the same way.

- [ ] Task 5: Add tests for the parser and sync integration
  - What: Write unit tests for `XBRLParser`, `HTMLParser`, `parse_filings`, and the sync integration. Use mock HTTP responses for SEC endpoints.
  - Files: `tests/test_parser.py`, `tests/test_sync.py`
  - Done when: All parser tests pass. Sync integration tests verify end-to-end flow with mocked SEC API responses.