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