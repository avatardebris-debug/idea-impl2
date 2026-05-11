# Phase 2 Tasks

- [ ] Task 1: Create test suite skeleton and unit tests for core utilities
  - What: Create a `tests/` directory with `__init__.py`, `conftest.py`, and unit tests for the core module functions (`_safe_divide`, `_normalize_key`, `_extract_numeric`, `build_metrics_dict`).
  - Files: `tests/__init__.py`, `tests/conftest.py`, `tests/test_core.py`
  - Done when: All core utility function tests pass with `pytest tests/test_core.py` — covering normal inputs, edge cases (zero denominator, None values, currency symbols, parenthetical negatives, empty strings), and `build_metrics_dict` output structure validation.

- [ ] Task 2: Create unit tests for CSV parser
  - What: Write tests for `parse_csv` covering: standard format CSV, transposed CSV, missing columns, non-existent file (FileNotFoundError), and the computed gross profit fallback (revenue - cogs when gross_profit column is missing).
  - Files: `tests/test_parsers.py`
  - Done when: All CSV parser tests pass with `pytest tests/test_parsers.py` — including at least 8 test functions covering normal parsing, transposed detection, error handling, and edge cases.

- [ ] Task 3: Create unit tests for PDF parser and report generator
  - What: Write tests for `parse_pdf` (mocking pdfplumber to avoid real PDF dependency) and `generate_report` (formatting, currency formatting, trend indicators, margin display).
  - Files: `tests/test_parsers.py` (append), `tests/test_reporters.py`
  - Done when: All PDF parser mock tests and reporter tests pass — including currency formatting for B/M/K/few values, trend indicators (up/down/flat), and report structure validation.

- [ ] Task 4: Add error handling improvements to parsers and CLI
  - What: Add input validation and graceful error handling: validate file extensions before parsing, add try/except around pandas read_csv with descriptive messages, add validation for empty DataFrames, and improve CLI error messages for edge cases (empty file, malformed CSV).
  - Files: `financial_document_analyzer/parsers.py`, `financial_document_analyzer/cli.py`
  - Done when: Parser raises descriptive exceptions for empty files and malformed data; CLI catches and prints user-friendly errors; existing tests still pass.

- [ ] Task 5: Write comprehensive README documentation
  - What: Create a `README.md` with: project overview, installation instructions, usage examples (CSV, PDF, trend comparison), CLI help text, project structure, test instructions, and dependencies.
  - Files: `README.md`
  - Done when: README covers all sections above, includes runnable code examples matching the actual CLI interface, and is formatted with proper markdown.

- [ ] Task 6: Run full test suite and verify everything passes
  - What: Install dependencies, run the complete test suite with pytest, verify all tests pass, and confirm the CLI works end-to-end with the sample files.
  - Files: No new files — verification step.
  - Done when: `pytest tests/` runs with all tests passing (green), and `python -m financial_document_analyzer.cli --file sample_financial.csv` produces a valid report.