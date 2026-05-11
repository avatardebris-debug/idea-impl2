# Phase 4 Tasks

- [ ] Task 1: Create REST API layer (api.py)
  - What: Build Flask Blueprint with REST endpoints that query the ForensicDatabase and return JSON. Endpoints: GET /api/companies (list all companies), GET /api/companies/<ticker> (company details), GET /api/filings (list filings with optional ticker/date filters), GET /api/fraud-scores (fraud scores over time with ticker/risk filters), GET /api/red-flags (red flags with ticker/risk filters), GET /api/capital-flows (capital flow data for a ticker), GET /api/risk-summary (aggregate risk counts by level). Each endpoint supports query params for ticker, date_range (start/end), and risk_level.
  - Files: src/forensic/api.py (new)
  - Done when: All endpoints return correct JSON data from ForensicDatabase; endpoints accept and apply ticker, date_range, and risk_level filters; endpoints can be imported and registered with a Flask app without errors.

- [ ] Task 2: Create web app entry point (web/app.py)
  - What: Create the Flask application entry point that registers the REST API Blueprint, serves static files, and renders HTML templates. Include a / route that serves the main dashboard template and a /health endpoint that returns app status.
  - Files: src/forensic/web/app.py (new), src/forensic/web/__init__.py (new)
  - Done when: Flask app starts without errors on `python -m forensic.web.app`; / and /health routes return HTTP 200; static files and templates are served correctly.

- [ ] Task 3: Create HTML dashboard templates
  - What: Build the main dashboard HTML template with a filtering bar (ticker input, date range pickers, risk level dropdown), a summary card section (total companies, filings, risk distribution), and container divs for Plotly charts. Also create a company detail template showing fraud score history, red flags table, and capital flow summary.
  - Files: src/forensic/web/templates/dashboard.html (new), src/forensic/web/templates/company_detail.html (new)
  - Done when: Templates render with valid HTML; filtering form elements are present and correctly named for JS submission; chart container divs exist with correct IDs; company detail template includes score chart, red flags table, and capital flow sections.

- [ ] Task 4: Create static assets and Plotly chart rendering
  - What: Create static JS/CSS files for the dashboard. The JS file fetches data from the REST API, applies client-side filtering, and renders Plotly charts: (1) fraud score over time line chart, (2) capital flow bar chart (operating/investing/financing), (3) risk level donut chart. CSS provides responsive layout and styling.
  - Files: src/forensic/web/static/js/dashboard.js (new), src/forensic/web/static/css/style.css (new)
  - Done when: Plotly charts render correctly in a browser with sample data; filtering by ticker, date range, and risk level updates charts without page reload; layout is responsive and readable.

- [ ] Task 5: Update requirements and verify integration
  - What: Add flask, plotly, and uvicorn to requirements.txt and pyproject.toml. Add a `forensic-dashboard` CLI entry point. Write a smoke test that starts the Flask dev server, hits the /health endpoint, and verifies JSON responses from at least one API endpoint.
  - Files: requirements.txt (modify), pyproject.toml (modify), tests/test_api.py (new)
  - Done when: `pip install` succeeds with all new dependencies; CLI entry point launches the dashboard; smoke test passes — server starts, /health returns 200, and at least one API endpoint returns valid JSON.