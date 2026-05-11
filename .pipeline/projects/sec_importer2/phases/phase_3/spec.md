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