# Phase 1 Tasks

- [ ] Task 1: Project scaffolding
  - What: Create the full directory structure, package init files, configuration, and project metadata for the forensic suite.
  - Files: Create `src/forensic/__init__.py`, `src/forensic/__main__.py`, `config.yaml`, `requirements.txt`, `README.md`; create `tests/__init__.py`
  - Done when: All files exist; `python -m forensic` runs without import errors; `requirements.txt` lists all dependencies (sec_importer, pydantic, pyyaml, requests, beautifulsoup4); `config.yaml` has database and logging settings

- [ ] Task 2: Forensic Pydantic models
  - What: Define Pydantic models for fraud scoring outputs — red flag entries, composite fraud score, and the full analysis report.
  - Files: Create `src/forensic/models.py`
  - Done when: Models (`RedFlagEntry`, `FraudScore`, `AnalysisReport`) validate with sample data; `RedFlagEntry` has fields for flag_name, severity (low/medium/high), evidence_excerpt, and score_contribution; `FraudScore` has fraud_score (0–100), risk_level (low/medium/high/critical), and top_red_flags; `AnalysisReport` wraps score + red_flags list + summary; all models serialize to JSON via `.model_dump()`

- [ ] Task 3: Data ingestion layer
  - What: Build the ingestion pipeline that fetches a company's latest 10-K via sec_importer, parses it, and stores results in the SQLite database.
  - Files: Create `src/forensic/ingest.py`
  - Done when: `ingest_company(ticker, db_path)` resolves ticker→CIK, fetches latest 10-K metadata, downloads filing text, parses it into `FilingItemModel` objects via `FilingParser`, upserts company/filing/items into `SECDatabase`, and returns the parsed items + filing metadata; function is idempotent (re-running with same ticker does not duplicate data)

- [ ] Task 4: Red-flag detection rules
  - What: Implement at least 5 distinct fraud detection checks against parsed filing items.
  - Files: Create `src/forensic/red_flags.py`
  - Done when: Checks implemented: (1) Revenue vs. receivables growth mismatch, (2) Related-party transaction flags, (3) Auditor change / going-concern warnings, (4) Restatement / amendment history, (5) Unusual segment reporting changes; each check returns a list of `RedFlagEntry` with flag_name, severity, evidence_excerpt, and score_contribution; `run_all_checks(parsed_items)` returns combined findings; checks are deterministic (same input → same output)

- [ ] Task 5: Scoring engine and CLI
  - What: Compute a composite fraud score (0–100) from red-flag findings and build the CLI entry point.
  - Files: Create `src/forensic/scoring.py`, `src/forensic/cli.py`; update `src/forensic/__main__.py`
  - Done when: `compute_fraud_score(red_flags)` returns a `FraudScore` with deterministic 0–100 score, risk_level, and top 3 red flags; `cli.py` implements `argparse` with `analyze <TICKER>` subcommand that runs ingestion → red-flag detection → scoring → outputs JSON to stdout; `__main__.py` delegates to `cli.main()`; running `python -m forensic analyze AAPL` produces valid JSON with fraud_score, risk_level, summary, and red_flags list

- [ ] Task 6: Tests
  - What: Write unit tests for ingestion, red-flag detection, and scoring modules.
  - Files: Create `tests/test_ingest.py`, `tests/test_red_flags.py`, `tests/test_scoring.py`
  - Done when: `test_ingest.py` tests ticker resolution, filing fetch, parsing, and DB upsert (mocked HTTP calls); `test_red_flags.py` tests each of the 5 red-flag checks with controlled input data; `test_scoring.py` tests score computation, risk level mapping, and top-3 flag selection; all tests pass with `pytest`