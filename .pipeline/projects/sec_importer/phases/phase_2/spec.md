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

