# Phase 1 Review — Invoice Processor

### What's Good
- Clean data model design: `Invoice`, `LineItem`, and `Ledger` are well-structured dataclasses with sensible defaults (auto-generated `invoice_id`, "USD" currency, empty line_items list).
- `Ledger` class (in models.py) provides useful filtering methods: `filter_by_vendor` (case-insensitive partial match), `filter_by_date_range` (inclusive), `clear`, and `list_invoices`.
- `LedgerExporter` in `ledger.py` handles both export and import of CSV data, enabling round-trip fidelity — verified by the smoke test `test_csv_export_import_roundtrip`.
- `CSVParser` has robust column detection with `_find_column` that supports multiple candidate names per column, and handles both explicit total columns and computed totals (qty × price).
- `CSVParser` also groups rows by `invoice_id` when available, supporting multi-invoice CSV files.
- `PDFParser` uses PyMuPDF (`fitz`) for text extraction and has multiple regex patterns for extracting vendor, date, total, currency, invoice number, and line items — good defensive parsing with fallbacks.
- `get_parser` factory function in `parsers/__init__.py` cleanly dispatches to the right parser based on file extension.
- `CLI` (`cli.py`) correctly handles both `Invoice` and `List[Invoice]` return types from parsers, prints per-file status, and exits with non-zero code on errors.
- `conftest.py` injects the workspace into `sys.path` so local imports work in pytest.
- All 7 smoke tests pass with 0 failures.
- Custom exception hierarchy (`InvoiceProcessorError` → `ParsingError`, `LedgerError`) is clean and informative.

## Blocking Bugs
None

## Non-Blocking Notes
- `PDFParser._extract_date` returns a `datetime` object but the type hint says `Optional[datetime]` — the `Invoice.invoice_date` field expects a `date`. This works because `datetime` is a subclass of `date`, but the return type should be `Optional[date]` for clarity. (pdf_parser.py: line with `def _extract_date`)
- `CSVParser.parse` returns `Union[Invoice, List[Invoice]]` which is inconsistent with `BaseParser.parse`'s documented return type. The base class should be updated or the union should be documented. (csv_parser.py, base.py)
- `Ledger` is defined in `models.py` but `LedgerExporter` is in `ledger.py` — the separation is fine, but `Ledger` in models.py is a simple list wrapper while `LedgerExporter` handles persistence. Consider whether `Ledger` should have export/import methods or if the current separation is intentional.
- `PDFParser._extract_line_items` uses a regex that requires exactly 4 fields (description, qty, price, amount) on one line — this may miss line items formatted differently. Not a bug, but a limitation.
- `requirements.txt` only lists `pytest` but the code depends on `PyMuPDF` (imported as `fitz`). This should be listed as a dependency. (requirements.txt)
- `CSVParser._build_invoice_from_rows` defaults `invoice_date` to `date(1970, 1, 1)` when no date is found — this epoch date could be confusing downstream. Consider `None` or a sentinel.
- `test_csv_parser` asserts `invoice.total == 1500.0` but the sample CSV has a header row with "total" column name. The parser treats the "total" column as the invoice total (first non-empty value = 1500.00), which is correct. However, the line items in the CSV also have amounts that sum to 2100.00 (600+100+50+900), not 1500.00. The invoice total (1500) and line item sum (2100) are inconsistent in the sample data. This is a data quality issue in the sample, not a code bug.
- `PDFParser._extract_currency` returns the first currency code found anywhere in the text, which could be a false positive if a currency code appears in a line item description.

## Reusable Components
- **CSVParser**: Self-contained CSV parsing logic with intelligent column detection, multi-format date/number parsing, and invoice grouping. Could be reused for any CSV-based data import. (source: invoice_processor/parsers/csv_parser.py)
- **LedgerExporter**: Generic CSV export/import with round-trip fidelity. Handles both flat records and nested line-item data. Could be reused for any ledger-like data export. (source: invoice_processor/ledger.py)
- **get_parser factory**: Extension-based file-type dispatching pattern. Simple and reusable for any multi-format parser system. (source: invoice_processor/parsers/__init__.py)
- **Custom exception hierarchy**: `InvoiceProcessorError` base with `ParsingError` and `LedgerError` subclasses. Reusable pattern for any tool with parsing and processing stages. (source: invoice_processor/exceptions.py)

## Verdict
PASS — All 7 tests pass, no blocking bugs found. Code is functional and well-structured.
