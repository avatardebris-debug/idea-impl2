# Phase 3 Tasks

- [ ] Task 1: Create FastAPI application structure and configuration
  - What: Create `sec_importer/api/` package with `main.py` (FastAPI app), `config.py` (settings via pydantic-settings), and `dependencies.py` (shared dependencies). Add environment variable configuration for: `DATABASE_URL`, `EDGAR_RATE_LIMIT_DELAY`, `LOG_LEVEL`, `API_HOST`, `API_PORT`, `API_DEBUG`. Create `config.py` that loads settings from env vars with sensible defaults.
  - Files: `sec_importer/api/main.py`, `sec_importer/api/config.py`, `sec_importer/api/dependencies.py`, `sec_importer/api/__init__.py`
  - Done when: `config.py` loads all env vars with defaults, `main.py` creates a FastAPI app instance, app starts without errors via `uvicorn sec_importer.api.main:app`, all config values are accessible via `Config()`.

- [ ] Task 2: Implement company and filing list endpoints
  - What: Create API endpoints for querying companies and filings. `GET /companies/{ticker}` returns company info (name, CIK, ticker) plus latest 5 filings. `GET /companies/{ticker}/filings` returns paginated list of filings with optional filters: `filing_type` (e.g., "10-K"), `date_from`, `date_to`, `limit`, `offset`. Use SQLAlchemy queries with proper pagination. Return 404 for unknown tickers.
  - Files: `sec_importer/api/routes/companies.py`, `sec_importer/api/routes/filings.py`, `sec_importer/api/schemas.py`
  - Done when: `GET /companies/AAPL` returns company data with latest filings, `GET /companies/AAPL/filings?filing_type=10-K&limit=10` returns filtered/paginated results, `GET /companies/INVALID` returns 404, all responses use Pydantic schemas for validation.

- [ ] Task 3: Implement filing detail and financial data endpoints
  - What: Create `GET /filings/{accession}` endpoint that returns full filing metadata plus parsed content (XBRL facts or HTML sections) if available. Create `GET /financials/{ticker}/{period}` endpoint that returns structured financial data for a specific period (e.g., "2024-Q4", "2023-12-31") with key metrics: revenue, net income, EPS, total assets, total liabilities, cash, etc. Parse the stored XBRL data and return it in a clean JSON structure.
  - Files: `sec_importer/api/routes/filings.py`, `sec_importer/api/routes/financials.py`, `sec_importer/api/schemas.py`
  - Done when: `GET /filings/0000320193-24-000006` returns full filing with parsed XBRL facts, `GET /financials/AAPL/2024-Q4` returns key financial metrics, endpoints handle missing parsed data gracefully (return null/empty for unparsed filings), schemas validate all response fields.

- [ ] Task 4: Implement search endpoint
  - What: Create `GET /search` endpoint that searches across filing metadata and parsed content. Support query parameters: `q` (search keyword), `filing_type`, `ticker`, `date_from`, `date_to`, `limit`. Search should match against: filing type, form description, company name, ticker, XBRL fact labels/values, and HTML section text. Use SQLAlchemy text search or LIKE queries.
  - Files: `sec_importer/api/routes/search.py`, `sec_importer/api/schemas.py`
  - Done when: `GET /search?q=revenue&filing_type=10-K&limit=20` returns relevant filings, search works across company names and filing content, pagination works correctly, empty query returns all filings (with limit).

- [ ] Task 5: Add production features and API documentation
  - What: Add structured JSON logging using `structlog` or Python's logging with JSON formatter. Add `GET /health` endpoint that returns `{"status": "ok", "database": "connected"|"disconnected"}`. Add rate limiting using `slowapi` or custom middleware (default: 100 requests/minute per IP). Add CORS middleware for cross-origin requests. Add request ID tracking. Enable FastAPI's built-in Swagger UI at `/docs` and ReDoc at `/redoc`. Add proper docstrings to all endpoints, request/response schemas, and error responses with examples.
  - Files: `sec_importer/api/middleware.py`, `sec_importer/api/health.py`, `sec_importer/logging_config.py`, `sec_importer/api/main.py` (updated with docs), `sec_importer/api/schemas.py` (with examples)
  - Done when: `GET /health` returns status with DB connectivity check, rate limiting prevents API abuse (429 after limit), all API logs are in JSON format, CORS headers are set correctly, `/docs` shows interactive Swagger UI with all endpoints and examples, `/redoc` shows ReDoc documentation.

- [ ] Task 6: Create Docker support — Dockerfile and docker-compose
  - What: Create `Dockerfile` that builds a production-ready image with Python 3.12, installs dependencies, and runs the API via uvicorn. Create `docker-compose.yml` that orchestrates the API service and SQLite database (or PostgreSQL for production). Add `.dockerignore` file. Add `docker-compose.dev.yml` for development with hot-reload.
  - Files: `Dockerfile`, `docker-compose.yml`, `docker-compose.dev.yml`, `.dockerignore`
  - Done when: `docker compose up` starts the API and database, API is accessible at `http://localhost:8000`, `docker compose -f docker-compose.dev.yml up` enables hot-reload for development, image builds successfully without errors.

- [ ] Task 7: Create scheduler for automatic periodic sync
  - What: Create `sec_importer/scheduler/` package with a scheduler that runs `sec-importer sync` periodically. Support both APScheduler (in-process) and cron-based (system-level) scheduling. Add configuration for: sync interval (default: daily at 2 AM UTC), tickers file path, limit per ticker, and notification on failure. Create `sec_importer/scheduler/run.py` as the entry point.
  - Files: `sec_importer/scheduler/__init__.py`, `sec_importer/scheduler/run.py`, `sec_importer/scheduler/config.py`
  - Done when: Scheduler runs sync automatically at configured intervals, scheduler logs sync results, scheduler can be started via `sec-importer scheduler start`, scheduler supports both APScheduler and cron modes, configuration via env vars.

- [ ] Task 8: Write integration tests and create deployment documentation
  - What: Create `tests/` directory with integration tests for all API endpoints and scheduler. Use `pytest` with `httpx.AsyncClient` for testing. Test: company lookup, filing listing with filters, filing detail with parsed data, search, health check, error handling (404, 500), scheduler runs sync correctly. Mock SEC API calls where needed. Test against live SEC data for at least 2 tickers. Update `README.md` with project overview, installation instructions (pip, Docker, docker-compose), configuration options (env vars), API usage examples, deployment guide, scheduler setup, and development setup. Create `config.example` file with all environment variables and their defaults. Add `SECURITY.md` with rate limiting and security considerations.
  - Files: `tests/test_api_companies.py`, `tests/test_api_filings.py`, `tests/test_api_search.py`, `tests/test_api_health.py`, `tests/test_scheduler.py`, `tests/conftest.py`, `README.md`, `config.example`, `SECURITY.md`
  - Done when: All API endpoints have integration tests, tests pass against live SEC data for AAPL and MSFT, scheduler tests verify sync runs correctly, test coverage > 80% for API code, `pytest` runs all tests successfully, README covers all deployment methods, config.example lists all env vars with defaults, API examples work correctly, security considerations are documented.

---

## Summary Table

| Phase | Scope | Duration (est.) | Key Output |
|-------|-------|------|------|
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