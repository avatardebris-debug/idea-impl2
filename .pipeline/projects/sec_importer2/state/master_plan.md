# SEC Importer 2 — Master Implementation Plan

## Idea Summary

Build a system that imports the latest data from SEC filings for US publicly traded companies. This covers fetching, parsing, and storing structured data from SEC filings (10-K, 10-Q, 8-K, S-1, DEF 14A, etc.) so downstream consumers can query financial, governance, and disclosure information.

## Core Deliverable

A reliable, up-to-date SEC filing data pipeline that:
- Fetches the latest filings for any US public company
- Parses filing metadata and structured content (XBRL/HTML/XML)
- Stores results in a queryable format
- Supports incremental/delta updates (only fetch what is new)

---

## Architecture Notes

### Data Sources
- **SEC EDGAR Full-Text Search API** — free, no API key, rate-limited (~10 req/s)
- **SEC EDGAR JSON API** — free, returns filing metadata in JSON
- **SEC XBRL Instance Documents** — structured financial data in inline XBRL (iXBRL)
- **SEC EDGAR Filing HTML/XML** — raw filing documents

### Key Design Decisions
1. **Use SEC free APIs** — no paid data vendor dependency (Bloomberg, Refinitiv, etc.)
2. **Store raw + parsed** — keep original filings alongside parsed structures for auditability
3. **Delta-first** — only fetch new filings since last sync to minimize API calls
4. **Modular parser pipeline** — different filing types have different structures; each gets its own parser
5. **PostgreSQL for storage** — relational structure for company/filing metadata, JSONB for flexible filing content

### High-Level Architecture

```
+-----+-----+----+---------+---------+-----+--------+
|                  SEC Importer 2                      |
+-----+-----+----+---------+---------+-----+--------+
|                                                      |
|  +---------+    +---------+    +---------------+    |
|  |  Fetcher|----|  Parser |----|   Storage     |    |
|  |  Layer  |    |  Layer  |    |   Layer       |    |
|  +---------+    +---------+    +---------------+    |
|       |               |               |              |
|       v               v               v              |
|  SEC EDGAR       XBRL/HTML      PostgreSQL          |
|  APIs (JSON/     /XML/JSON      (companies,        |
|   RSS/XML)       parsers        filings, facts)     |
|                                                      |
|  +-----+-----+----+---------+---------+-----+--------+|
|  |           Scheduler / Orchestrator            |    |
|  |  (cron / Airflow / lightweight task queue)    |    |
|  +-----+-----+----+---------+---------+-----+--------+|
|                                                      |
|  +-----+-----+----+---------+---------+-----+--------+|
|  |              API / Query Layer                |    |
|  |  (REST or GraphQL endpoint for consumers)     |    |
|  +-----+-----+----+---------+---------+-----+--------+|
+-----+-----+----+---------+---------+-----+--------+
```

### Tech Stack (Recommended)
- **Language**: Python 3.11+
- **HTTP Client**: `httpx` (async) or `requests`
- **XBRL Parser**: `xbrlutil` or custom iXBRL extraction
- **HTML Parser**: `BeautifulSoup` / `lxml`
- **Database**: PostgreSQL + SQLAlchemy
- **Scheduling**: `APScheduler` or cron
- **Caching**: Redis or file-based TTL cache
- **Storage**: Local filesystem (S3/GCS optional for scale)

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| SEC API rate limits (10 req/s) | Medium | Implement exponential backoff, request batching, and local caching |
| SEC API schema changes | Medium | Version the API client; add integration tests against live SEC data |
| XBRL parsing complexity | High | Start with metadata-only (no XBRL) in Phase 1; add XBRL in Phase 2 |
| Filing HTML/XML format drift | Medium | Store raw documents; write robust, versioned parsers with tests |
| Data volume grows quickly | Medium | Pagination, delta-sync, and tiered storage (hot/warm/cold) |
| Missing or malformed filings | Low | Graceful error handling; mark incomplete filings; retry logic |
| Legal / terms of service | Low | SEC data is public domain; comply with EDGAR usage guidelines |

---

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

## Phase 2 — Filing Content Parser

**Goal**: Download and parse the actual content of filings — both structured (XBRL financial data) and unstructured (text from 8-K, 10-K MD&A, etc.).

### Description
- Download filing documents (HTML, XML, XBRL) from SEC EDGAR based on stored accession numbers
- Parse XBRL iXBRL data to extract financial statement facts (revenue, EPS, assets, liabilities, etc.)
- Parse HTML filings to extract text content (MD&A, risk factors, management discussion)
- Store parsed content in the database alongside metadata
- Add a filing detail view: `sec-importer show <accession_number>`

### Deliverable
- `sec_importer/parser/xbrl_parser.py` — XBRL fact extraction (income statement, balance sheet, cash flow)
- `sec_importer/parser/html_parser.py` — text extraction from HTML filings
- `sec_importer/parser/__init__.py` — unified parser interface
- Database schema updated with `filing_contents` table (JSONB for XBRL facts)
- CLI: `sec-importer show <accession>` displays parsed financial data
- Sample parsed data for at least 3 companies latest 10-K

### Dependencies
- Phase 1 (metadata + storage must exist)
- `xbrlutil` or custom XBRL parsing library
- `lxml` / `BeautifulSoup` for HTML parsing

### Success Criteria
- [ ] Successfully downloads and parses XBRL data for 10-K and 10-Q filings
- [ ] Extracts at least 20 financial facts per filing (revenue, net income, total assets, etc.)
- [ ] HTML text extraction works for 8-K and 10-K filings
- [ ] Parsed data stored and queryable via CLI
- [ ] Parser handles malformed XBRL gracefully (marks partial parse, does not crash)
- [ ] End-to-end: `sec-importer sync` fetches new filings AND parses them

---

## Phase 3 — Query API & Production Hardening

**Goal**: Expose a queryable API for consumers, add production-grade features (logging, monitoring, alerting), and support broad ticker coverage.

### Description
- Build a REST API (FastAPI) with endpoints for:
  - `GET /companies/{ticker}` — company info + latest filings
  - `GET /companies/{ticker}/filings` — list of filings with filters (type, date range)
  - `GET /filings/{accession}` — full filing details with parsed data
  - `GET /financials/{ticker}/{period}` — structured financial data
  - `GET /search` — search filings by keyword
- Add production features:
  - Structured logging (JSON logs)
  - Health check endpoint
  - Rate limiting on API side
  - Configuration via environment variables
  - Docker support
- Broad coverage: support all ~5,000+ US public companies
- Add a scheduler for automatic periodic sync (daily or hourly)

### Deliverable
- `sec_importer/api/` — FastAPI application with all endpoints
- `sec_importer/scheduler/` — periodic sync job (APScheduler or cron wrapper)
- `Dockerfile` + `docker-compose.yml`
- `config.example` with all config options
- API documentation (OpenAPI/Swagger)
- Integration tests against live SEC data
- README with deployment instructions

### Dependencies
- Phase 2 (parsers must work correctly)
- `fastapi`, `uvicorn`
- `docker` + `docker-compose`

### Success Criteria
- [ ] All API endpoints return correct data for all filing types
- [ ] API responds in under 200ms for cached queries, under 2s for fresh queries
- [ ] Scheduler runs automatically and detects new filings within 24 hours
- [ ] Docker compose brings up the full stack (API + DB + scheduler)
- [ ] Over 5,000 tickers can be queried
- [ ] Integration tests pass against live SEC data
- [ ] Graceful degradation: API returns 500s with error details for failed filings

---

## Summary Table

| Phase | Scope | Duration (est.) | Key Output |
|-------|-------|-----------------|------------|
| 1 — MVP | Metadata fetcher + SQLite store | 1-2 weeks | CLI tool, working sync, sample data |
| 2 — Content Parser | XBRL + HTML parsing | 2-3 weeks | Parsed financial data, filing details |
| 3 — API + Production | REST API, scheduler, Docker | 2-3 weeks | Queryable API, production deployment |

## Open Questions / Future Work
- Should we support historical data (backfill years of filings)?
- Should we add SEC insider trading (Form 4) import?
- Should we support non-US filings (SEDAR, etc.)?
- Should we add a web UI / dashboard?
- Should we cache parsed XBRL in a graph database for cross-company analysis?
- Should we add anomaly detection on financial data?
