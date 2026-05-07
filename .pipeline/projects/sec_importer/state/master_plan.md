# SEC Importer — Master Implementation Plan

## Idea Summary

Build a system that imports all the latest SEC filing data for US companies — fetching, parsing, normalizing, and storing structured data from SEC filings (10-K, 10-Q, 8-K, etc.) so it can be queried programmatically.

## Core Deliverable

A working SEC filing importer that can:
- Fetch filings from the SEC EDGAR database
- Parse filing metadata and XBRL/text content
- Store structured data in a local database
- Query and export the data

---

## Architecture Notes

### Data Sources
- **Primary:** SEC EDGAR Full-Text Text Files API (`https://www.sec.gov/Archives/edgar/full-text/`)
- **Secondary:** SEC EDGAR JSON API (`https://efts.sec.gov/LATEST/search-index-json/`)
- **Fallback:** SEC EDGAR RSS feeds for filing notifications

### Key SEC APIs & Endpoints
- **Company/Filing Index:** `https://data.sec.gov/submissions/CIK{cik}.json`
- **Full-Text Files:** `https://www.sec.gov/Archives/edgar/full-text/{accession_no}.txt`
- **JSON Index:** `https://data.sec.gov/submissions/{cik_str}.json`
- **XBRL Reports:** `https://www.sec.gov/Archives/edgar/xbrl/{cik}/{accession}/{file}`

### Proposed Stack
- **Language:** Python 3.11+
- **HTTP Client:** `requests` + `aiohttp` for async fetching
- **XBRL Parsing:** `xmldocs` or `xbrlutil`
- **Database:** SQLite (MVP) → PostgreSQL (production)
- **ORM:** `sqlite3` stdlib (MVP) → `SQLAlchemy` (production)
- **Data Model:** Pydantic for schema validation
- **Scheduling:** `APScheduler` or cron

### Data Model (high-level)
```
Company (cik, name, ticker, sic, industry, state)
Filing (accession_no, cik, filing_type, filing_date, accepted_date, file_url, is_xbrl)
FilingItem (filing_id, item_label, item_content, item_type)
XBRLFact (filing_id, tag, context, value, unit, label)
```

### Risks
| Risk | Mitigation |
|------|-----------|
| SEC EDGAR rate limits (10 req/sec) | Implement request throttling with exponential backoff |
| XBRL parsing complexity | Start with text-based filings (8-K, 10-Q text), add XBRL in Phase 3 |
| Large filing sizes (10-K can be 500MB+) | Stream downloads, chunk processing, disk-space monitoring |
| SEC API changes / downtime | Multi-source fallback (RSS → JSON → Full-Text), retry logic |
| Schema drift in SEC data | Pydantic validation with graceful degradation |

---

## Phase 1 — MVP: Single-Filing Fetcher & Parser

### Description
Build the smallest useful thing: a command-line tool that fetches and parses one filing (e.g., the latest 10-K for Apple) and outputs the key data in a readable format.

### Deliverable
- A CLI tool (`sec_importer`) that:
  - Takes a ticker symbol and filing type as arguments
  - Resolves ticker → CIK via SEC's CIK lookup
  - Fetches the latest filing of the requested type
  - Parses the filing's text content to extract key fields (filing date, company name, items, summary)
  - Outputs parsed data as JSON to stdout or a file
- No database yet — just fetch + parse + output

### Dependencies
- None (pure Python, `requests`, `BeautifulSoup` for HTML parsing)

### Success Criteria
- [ ] Can resolve a ticker (e.g., "AAPL") to a CIK number
- [ ] Can fetch the latest 10-K filing for that CIK
- [ ] Can parse the filing text and extract: filing type, filing date, company name, item headings, and body text
- [ ] Outputs valid JSON with all extracted fields
- [ ] Handles basic errors (ticker not found, no filing available, network errors)
- [ ] Runs end-to-end in under 30 seconds on a standard connection

### Tasks
- [ ] Set up project structure (src/sec_importer/, tests/, requirements.txt)
- [ ] Implement CIK resolution from ticker (SEC EDGAR company search)
- [ ] Implement filing index lookup (fetch latest filings for a CIK)
- [ ] Implement filing text download (SEC full-text API)
- [ ] Implement filing text parser (extract metadata, items, content)
- [ ] Implement CLI interface (argparse with ticker, filing_type, output options)
- [ ] Write unit tests for parser logic
- [ ] Write integration test (end-to-end fetch + parse)
- [ ] Documentation: README with usage examples

---

## Phase 2 — Database Storage & Multi-Filing Support

### Description
Add persistent storage and scale to handle multiple companies and multiple filing types. Build the core data pipeline: fetch → parse → store → query.

### Deliverable
- A local SQLite database with the full data model (Company, Filing, FilingItem)
- Batch import capability: import all filings for a list of companies
- Query API: retrieve filings by company, type, date range
- A sync script that can run as a one-shot or periodic import job

### Dependencies
- Phase 1 must be complete and working
- `sqlite3` (stdlib), `APScheduler` or `cron` for scheduling

### Success Criteria
- [ ] SQLite database schema is defined and migrations work
- [ ] Can import filings for 10+ companies in a single run
- [ ] Can query: "all 10-K filings for AAPL in 2024"
- [ ] Can query: "all 8-K filings in the last 7 days across all imported companies"
- [ ] Batch import of 50 companies completes in under 5 minutes
- [ ] Deduplication works (re-running doesn't create duplicates)
- [ ] Rate limiting is enforced (respects SEC's 10 req/sec limit)
- [ ] Error recovery: failed filings are retried, not lost

### Tasks
- [ ] Design and implement SQLite schema (Company, Filing, FilingItem tables)
- [ ] Implement Pydantic models for data validation
- [ ] Implement database ORM layer (raw SQL or SQLAlchemy)
- [ ] Extend Phase 1 fetcher to support batch imports
- [ ] Implement deduplication logic (by accession number)
- [ ] Implement rate limiter with SEC-compliant throttling
- [ ] Implement query API (filter by company, type, date range)
- [ ] Implement sync script with --companies, --types, --date-range flags
- [ ] Add logging and progress reporting
- [ ] Write integration tests for DB operations
- [ ] Add configuration file (YAML) for settings (rate limits, paths, etc.)

---

## Phase 3 — XBRL Parsing, API, & Production Hardening

### Description
Add XBRL (structured financial data) parsing, expose a query API, add scheduling, and harden for production use. This phase transforms the tool from a CLI utility into a service.

### Deliverable
- XBRL parsing for financial statement data (balance sheet, income statement, cash flow)
- A REST API (FastAPI) for querying imported data
- Scheduled imports (daily or configurable)
- Docker support for easy deployment
- Comprehensive error handling, monitoring, and documentation

### Dependencies
- Phase 2 must be complete and working
- `fastapi`, `uvicorn`, `xmldocs` or `xbrlutil`, `docker`

### Success Criteria
- [ ] Can parse XBRL data from filings that include it (10-K, 10-Q with XBRL)
- [ ] Extracted financial data matches source filing (verified against at least 5 filings)
- [ ] REST API serves queries with < 200ms response time for typical queries
- [ ] Scheduled imports run automatically and report success/failure
- [ ] Docker container builds and runs (`docker build` + `docker run`)
- [ ] API is documented (OpenAPI/Swagger UI)
- [ ] Graceful handling of SEC API outages (queue retries, alert on extended downtime)
- [ ] Database can handle 100+ companies with all their filings (performance test)

### Tasks
- [ ] Implement XBRL parser (use xmldocs library)
- [ ] Add XBRL facts to database schema (XBRLFact table)
- [ ] Validate XBRL data against known financial statements
- [ ] Build FastAPI application with query endpoints
- [ ] Implement scheduled import runner (APScheduler)
- [ ] Add health check endpoint
- [ ] Add Dockerfile and docker-compose.yml
- [ ] Add monitoring: request logs, import success rates, DB size
- [ ] Write production deployment guide
- [ ] Performance test with 100+ companies
- [ ] Final documentation and release

---

## Phase Summary

| Phase | Scope | Key Outcome |
|-------|-------|-------------|
| **1 — MVP** | Fetch + parse one filing | CLI tool that gets and parses a single SEC filing |
| **2 — Storage & Scale** | DB + batch + query | Multi-company importer with persistent storage and queries |
| **3 — Production** | XBRL + API + scheduling | Full service: structured data, REST API, auto-schedule |

## Open Questions
- Should we support SEC EDGAR RSS feeds as a notification trigger for new filings?
- Do we need to handle Form 4 (insider trading) and other niche filing types?
- Should we cache SEC data locally for offline use?
- Is PostgreSQL needed early, or can SQLite serve until 100+ companies?
- Should we expose a GraphQL API instead of REST for flexible queries?

## Assumptions
- SEC EDGAR APIs remain publicly accessible and stable
- Filing data is publicly available (no authentication required)
- SQLite is sufficient for the expected data volume (millions of rows max)
- Users have Python 3.11+ available
