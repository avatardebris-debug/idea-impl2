# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and data models
  - What: Create the project structure, Python package, and core data models for invoices and line items
  - Files: invoice_processor/__init__.py, invoice_processor/models.py, invoice_processor/exceptions.py
  - Done when: Package is importable; Invoice, LineItem, and Ledger dataclasses exist with fields for vendor, date, total, currency, line_items (list of LineItem with description, quantity, unit_price, amount), and source_file; Ledger can hold a list of invoices

- [x] Task 2: Invoice file parser (text-based)
  - What: Build a parser that reads invoice files (PDF text extraction via PyMuPDF or pdfminer, plus plain-text/CSV support) and extracts key fields (vendor, date, total, line items)
  - Files: invoice_processor/parsers/base.py, invoice_processor/parsers/pdf_parser.py, invoice_processor/parsers/csv_parser.py, invoice_processor/parsers/__init__.py
  - Done when: Parser interface accepts a file path and returns an Invoice object; PDF parser extracts text and parses vendor/total/date; CSV parser reads rows and maps columns to line items; graceful fallback when fields are missing

- [ ] Task 3: Ledger with CSV export
  - What: Implement the Ledger class that stores parsed invoices and supports CSV export
  - Files: invoice_processor/ledger.py
  - Done when: Ledger can add invoices, list all invoices, filter by vendor/date range; export_to_csv writes a CSV with columns: invoice_id, vendor, date, total, currency, source_file; CSV can be read back and reconstruct the same data

- [ ] Task 4: CLI entry point
  - What: Build a command-line interface to process a directory of invoice files and export the ledger
  - Files: invoice_processor/cli.py
  - Done when: Running `python -m invoice_processor.cli --input <dir> --output <csv>` processes all supported files in the directory, parses them, and writes a CSV ledger; prints summary of processed/skipped files; exits with non-zero code on errors

- [ ] Task 5: Core functionality integration and smoke test
  - What: Wire all components together and verify end-to-end with sample data
  - Files: tests/test_smoke.py (or scripts/demo.py), requirements.txt
  - Done when: requirements.txt lists all dependencies; a sample invoice PDF/CSV can be processed end-to-end through CLI to produce a valid CSV ledger; smoke test passes confirming importability and core feature correctness