# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and package structure
  - What: Create the Python package layout with __init__.py, core modules, and a requirements file
  - Files: financial_document_analyzer/__init__.py, financial_document_analyzer/core.py, financial_document_analyzer/parsers.py, financial_document_analyzer/reporters.py, financial_document_analyzer/cli.py, requirements.txt
  - Done when: Package can be imported (import financial_document_analyzer) without errors; requirements.txt lists dependencies (pandas, tabula-py, reportlab or similar)

- [ ] Task 2: CSV parser for financial documents
  - What: Build a CSV parser that reads financial CSV files and extracts key metrics — revenue, cost of goods, gross profit, operating income, net income, and basic ratios (gross margin, operating margin, net margin)
  - Files: financial_document_analyzer/parsers.py
  - Done when: parse_csv(file_path) returns a dict with keys: filename, metrics (revenue, cogs, gross_profit, operating_income, net_income), margins (gross_margin, operating_margin, net_margin), and raw_rows count; works with a sample CSV containing standard financial columns

- [ ] Task 3: PDF parser for financial documents
  - What: Build a PDF parser that extracts financial tables from PDFs using tabula-py or similar, then parses the extracted text into the same metric dict format as the CSV parser
  - Files: financial_document_analyzer/parsers.py (add parse_pdf function)
  - Done when: parse_pdf(file_path) returns a dict with the same structure as parse_csv; extracts revenue, margins, and key ratios from a sample financial PDF (e.g., an income statement)

- [ ] Task 4: Report generator
  - What: Build a reporter module that takes parsed metric dicts and produces a structured text summary report — prints formatted output with metric values, margins, and a brief trend indicator (e.g., "▲" or "▼" if comparing two periods)
  - Files: financial_document_analyzer/reporters.py
  - Done when: generate_report(metrics_dict) returns a formatted string with all key metrics displayed clearly; works with sample data from Tasks 2 and 3

- [ ] Task 5: CLI entry point
  - What: Build a CLI using argparse that accepts a file path (PDF or CSV), runs the appropriate parser, generates a report, and prints it to stdout
  - Files: financial_document_analyzer/cli.py
  - Done when: Running `python -m financial_document_analyzer.cli --file <path>` prints a structured summary report to stdout for both CSV and PDF inputs; exit code 0 on success, non-zero on file-not-found or parse errors