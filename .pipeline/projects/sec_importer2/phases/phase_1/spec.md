## Phase 1 — MVP: Metadata Fetcher & Store

**Goal**: Fetch and store filing metadata (ticker, filing type, date, URL, accession number) for a configurable list of companies.

### Description
- Build a fetcher that queries the SEC EDGAR JSON API for the latest filings per ticker
- Store filing metadata in a local database (SQLite for simplicity, PostgreSQL-ready schema)
- Support a configurable ticker list (CSV input or config file)
- Implement delta-sync: only fetch filings newer than the last known date
- Provide a CLI or simple API to trigger imports and list stored filings

### Deliverable
- `sec_importer/` Python package with:
  - `fetcher.py` — SEC EDGAR JSON API client with rate limiting & retry
  - `parser.py` — metadata extractor (no XBRL yet)
  - `storage.py` — SQLite (or PostgreSQL) schema + ORM models
  - `sync.py` — delta-sync orchestrator
  - `cli.py` — CLI: `sec-importer sync`, `sec-importer list`, `sec-importer add-ticker`
- SQLite database with sample data for 5+ tickers
- README with setup instructions

### Dependencies
- None (pure Python, standard library + `httpx`, `sqlalchemy`, `sqlite3`)

### Success Criteria
- [ ] Can fetch latest 10-K, 10-Q, 8-K metadata for any ticker
- [ ] Stores at least 500 filing records across 5 tickers
- [ ] Delta-sync correctly identifies new filings (no duplicates)
- [ ] CLI `sec-importer sync` completes for 10 tickers in under 5 minutes
- [ ] No rate-limit errors (exponential backoff works)
- [ ] `sec-importer list` returns all stored filings with correct fields

---