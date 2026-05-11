# Phase 2 Tasks

- [ ] Task 1: Add `filing_contents` table and ORM model
  - What: Extend the database schema with a `filing_contents` table to store parsed XBRL facts and HTML text. Add a SQLAlchemy ORM model `FilingContent` in `models.py`. The table needs columns for `filing_id` (FK), `content_type` (xbrl/html), `content_data` (JSON/text), `parse_status` (success/partial/failed), `parse_error` (nullable string), and `parsed_at` (datetime).
  - Files: `sec_importer/models.py`, `sec_importer/storage.py`
  - Done when: `FilingContent` model exists in `models.py`, `init_db()` creates the table, `storage.py` has `upsert_filing_content(session, filing_id, content_type, content_data)` and `get_filing_content(session, filing_id)` helpers, and the existing `companies`/`filings` tables still work unchanged.

- [ ] Task 2: Implement XBRL/iXBRL parser
  - What: Create `sec_importer/parser/xbrl_parser.py` that downloads XBRL instance documents from SEC EDGAR (using the accession number to build the URL) and parses iXBRL facts. Extract at least 20 financial facts per filing including: revenue, cost of revenue, gross profit, operating income, net income, EPS (basic & diluted), total assets, total liabilities, total equity, cash and equivalents, accounts receivable, inventory, property plant equipment, long-term debt, current portion of debt, operating cash flow, investing cash flow, financing cash flow, shares outstanding, and effective tax rate. Handle malformed XBRL gracefully — return partial facts with `parse_status="partial"` and a descriptive error, never crash.
  - Files: `sec_importer/parser/xbrl_parser.py`
  - Done when: `parse_xbrl(accession_number, session)` downloads the XBRL document, extracts 20+ financial facts as a dict keyed by concept name, returns `{"facts": {...}, "parse_status": "success"|"partial"|"failed", "parse_error": str|None}`. Gracefully handles missing tags, malformed XML, and network errors.

- [ ] Task 3: Implement HTML text extraction parser
  - What: Create `sec_importer/parser/html_parser.py` that downloads HTML filing documents from SEC EDGAR and extracts structured text sections. Use BeautifulSoup to parse HTML and extract key sections: MD&A (Management Discussion & Analysis), Risk Factors, Business Overview, Financial Statements, and General Body Text. Return a dict with section keys and extracted text content.
  - Files: `sec_importer/parser/html_parser.py`
  - Done when: `parse_html(accession_number, session)` downloads the HTML filing, extracts at least 5 named sections (MD&A, Risk Factors, Business, Financial Statements, Body), returns `{"sections": {"mda": str, "risk_factors": str, "business": str, "financial_statements": str, "body": str}, "parse_status": "success"|"partial"|"failed", "parse_error": str|None}`. Handles malformed HTML gracefully.

- [ ] Task 4: Create unified parser interface and download helpers
  - What: Create `sec_importer/parser/__init__.py` as the unified parser module. It should expose: `download_filing_document(accession_number, session)` — downloads the primary document (XBRL or HTML) from SEC EDGAR given an accession number; `parse_filing(accession_number, session)` — auto-detects filing type and dispatches to the right parser (XBRL for 10-K/10-Q, HTML for 8-K/others); `parse_and_store(accession_number, filing_id, session)` — parses and stores results in the `filing_contents` table. Also add `get_filing_document_url(accession_number)` helper that constructs the SEC EDGAR download URL.
  - Files: `sec_importer/parser/__init__.py`
  - Done when: `parse_filing(accession_number)` auto-dispatches to XBRL or HTML parser based on filing type and returns a unified result dict. `parse_and_store(accession_number, filing_id)` parses and writes to DB. `download_filing_document(accession_number)` returns the raw document bytes. All functions are importable from `sec_importer.parser`.

- [ ] Task 5: Add `sec-importer show` CLI command and integrate parsing into `sync`
  - What: Add a `sec-importer show <accession_number>` CLI command that looks up the filing by accession number, retrieves parsed content from the database, and displays financial facts (for XBRL) or text sections (for HTML) in a readable format. Also update `sync.py` to call `parse_and_store()` for newly synced filings so that `sec-importer sync` fetches new filings AND parses them end-to-end.
  - Files: `sec_importer/cli.py`, `sec_importer/sync.py`
  - Done when: `sec-importer show <accession>` prints the filing metadata plus parsed financial facts or text sections in a formatted table. `sec-importer sync` now parses newly fetched filings automatically (logging parse status). Running sync on a ticker with existing 10-K filings results in parsed content being stored.

- [ ] Task 6: End-to-end validation — parse at least 3 companies' latest 10-K filings
  - What: Run `sec-importer sync` for at least 3 companies that have recent 10-K filings in the database, then verify that XBRL parsing extracted 20+ facts per filing and that `sec-importer show` displays the data correctly. Also verify that HTML parsing works for at least one 8-K filing. Confirm that malformed XBRL is handled without crashes.
  - Files: No new files — validation via CLI commands and manual inspection.
  - Done when: At least 3 companies have parsed 10-K data in `filing_contents` with 20+ facts each. At least one 8-K has parsed HTML sections. `sec-importer show` displays all data correctly. No crashes on any filing type.