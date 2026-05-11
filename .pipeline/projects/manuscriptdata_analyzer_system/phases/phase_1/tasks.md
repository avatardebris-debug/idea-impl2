# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and CLI foundation
  - What: Create the `manuscriptdata_analyzer` Python package with project structure, `pyproject.toml`, and a CLI entry point using `click` or `argparse`. Implement `--help` output listing available commands (import, summary).
  - Files: `pyproject.toml`, `manuscriptdata_analyzer/__init__.py`, `manuscriptdata_analyzer/cli.py`, `manuscriptdata_analyzer/__main__.py`
  - Done when: `pip install -e .` succeeds, `manuscriptdata-analyzer --help` prints available commands (import, summary), and the CLI exits cleanly.

- [ ] Task 2: SQLite schema and database layer
  - What: Define the SQLite schema for storing manuscript analytics data. Create tables for `sales_data`, `demographics_data`, and `content_metrics` with appropriate columns, types, and indexes. Implement a `Database` class with methods to create tables, insert rows, and query data.
  - Files: `manuscriptdata_analyzer/database.py`
  - Done when: Database class creates all three tables with correct schema on first use, inserts rows successfully, and queries return proper data. Tables have indexes on commonly queried columns (e.g., book title, date, chapter).

- [ ] Task 3: CSV parser with auto-detection for three data types
  - What: Build a CSV parser module that reads a CSV file, inspects its header columns, and auto-detects the data type (sales, demographics, or content metrics). Implement import functions for each type that validate required columns and normalize data before returning structured records.
  - Files: `manuscriptdata_analyzer/csv_parser.py`
  - Done when: Parser correctly identifies sales data (columns: Date, Book Title, Units Sold, Revenue, Platform), demographics data (columns: Age Group, Gender, Country, Rating, Review Count), and content metrics (columns: Chapter, Word Count, Read-Through Rate, Completion Rate). Invalid or unrecognized CSVs raise a clear error.

- [ ] Task 4: CLI import command wired to parser and database
  - What: Implement the `import` CLI command that accepts a CSV file path, uses the CSV parser to detect and parse the data, and stores the records in the SQLite database via the database layer. Print a confirmation message with record count and detected type.
  - Files: `manuscriptdata_analyzer/cli.py` (add import command), `manuscriptdata_analyzer/database.py` (add insert method if needed)
  - Done when: Running `manuscriptdata-analyzer import <file.csv>` on each of the three CSV types stores all rows in the correct table and prints a summary (e.g., "Imported 15 rows of sales_data").

- [ ] Task 5: CLI summary command with formatted output
  - What: Implement the `summary` CLI command that queries the SQLite database and outputs formatted summary statistics: total sales (units sold, avg revenue, platform breakdown) for sales data; age/gender/country breakdowns with percentages for demographics data; chapter-level word count and completion stats for content metrics.
  - Files: `manuscriptdata_analyzer/cli.py` (add summary command), `manuscriptdata_analyzer/database.py` (add query methods)
  - Done when: `manuscriptdata-analyzer summary` prints a neatly formatted report with total sales, average revenue, demographic breakdowns, and content metrics when data exists in the database.

- [ ] Task 6: Unit tests with fixture CSV files
  - What: Create fixture CSV files for all three data types and write unit tests that verify: CSV parser auto-detection and parsing, database table creation and data insertion, and summary command output correctness.
  - Files: `tests/fixtures/sales.csv`, `tests/fixtures/demographics.csv`, `tests/fixtures/content_metrics.csv`, `tests/test_csv_parser.py`, `tests/test_database.py`, `tests/test_cli.py`
  - Done when: All tests pass with `pytest`. Tests cover parser detection for each type, database CRUD operations, and summary output formatting.