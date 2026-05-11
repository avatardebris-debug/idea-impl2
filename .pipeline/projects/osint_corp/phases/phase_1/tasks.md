# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and package structure
  - What: Create the Python package skeleton with proper module layout, requirements, and entry points
  - Files: osint_corp/__init__.py, osint_corp/cli.py, osint_corp/core.py, osint_corp/sources/__init__.py, osint_corp/models/__init__.py, pyproject.toml, requirements.txt
  - Done when: `pip install -e .` succeeds and `osint-corp --help` prints usage info; package is importable as `import osint_corp`

- [ ] Task 2: Core data models for corporate entities
  - What: Define dataclasses/Pydantic models for the core domain: Company, Filing, Relationship, Location, Manifest, Contract, JobPosting
  - Files: osint_corp/models/entities.py, osint_corp/models/__init__.py
  - Done when: All models are defined with fields matching their real-world counterparts; models can be instantiated and serialized to/from JSON; `from osint_corp.models import Company, Filing, Relationship, Location, Manifest, Contract, JobPosting` works

- [ ] Task 3: SEC filing importer
  - What: Build a module that fetches and parses SEC EDGAR filings (10-K, 10-Q, 8-K) and extracts structured data (company name, CIK, ticker, filing date, financials, material events)
  - Files: osint_corp/sources/sec_importer.py
  - Done when: Given a CIK or ticker, the importer fetches at least one filing from EDGAR's public API, parses the XML/HTML, and returns a `Filing` model instance; handles network errors gracefully

- [ ] Task 4: Corporate registry data source
  - What: Build a module that queries public corporate registry data (e.g., state secretary of state APIs, OpenCorporates public endpoints) and extracts company registration details
  - Files: osint_corp/sources/corporate_registry.py
  - Done when: Given a company name or jurisdiction, the module returns a `Company` model with registration details; handles missing data and API errors

- [ ] Task 5: Data correlation engine
  - What: Build the core logic that links entities across data sources — matching companies by name/ticker/CIK, correlating filings with relationships, and building a basic graph of connections
  - Files: osint_corp/core.py (correlation functions)
  - Done when: Given a list of companies and filings, the engine produces a set of `Relationship` objects linking them; cross-source matching works (e.g., SEC filing company matches registry company); `osint_corp.core.correlate()` is a clean public API

- [ ] Task 6: CLI interface for core workflow
  - What: Build a command-line interface that lets a user run the full MVP workflow: import SEC data, query registry, correlate, and output results
  - Files: osint_corp/cli.py
  - Done when: `osint-corp import --ticker AAPL` fetches SEC filings and prints summary; `osint-corp correlate --ticker AAPL` shows linked relationships; `osint-corp search --name "Apple"` returns registry matches; all commands exit cleanly with non-zero on error