# Invoice Processor

A Python tool for parsing invoices from CSV and PDF files, managing them in a ledger, and exporting/importing data.

## Features

- **CSV Parser**: Parse invoice data from CSV files with support for multiple invoices per file
- **PDF Parser**: Extract invoice data from PDF files using PyMuPDF
- **Ledger**: Store and manage invoices with filtering by vendor and date range
- **CSV Export/Import**: Round-trip ledger data to/from CSV files
- **CLI**: Command-line interface for processing files and managing ledgers
- **Validation**: Input validation on all data models
- **Retry Logic**: Configurable retry mechanism for resilient operations
- **Logging**: Configurable logging with file and console handlers

## Installation

```bash
pip install -r requirements.txt
```

### Requirements

- Python 3.10+
- PyMuPDF (for PDF parsing)

## Usage

### CLI

```bash
# Process a single file
python -m invoice_processor.cli process --file invoice.csv

# Process all files in a directory
python -m invoice_processor.cli process --directory ./invoices

# Export ledger to CSV
python -m invoice_processor.cli export --output ledger.csv

# Import ledger from CSV
python -m invoice_processor.cli import --input ledger.csv

# List all invoices
python -m invoice_processor.cli list

# Filter by vendor
python -m invoice_processor.cli list --vendor "Acme Corp"

# Filter by date range
python -m invoice_processor.cli list --date-from 2024-01-01 --date-to 2024-12-31

# Clear ledger
python -m invoice_processor.cli clear
```

### Programmatic API

```python
from invoice_processor.ledger import Ledger
from invoice_processor.parsers.csv_parser import CSVParser
from invoice_processor.ledger_exporter import LedgerExporter

# Parse a CSV file
parser = CSVParser()
invoices = parser.parse("invoices.csv")

# Add to ledger
ledger = Ledger()
for invoice in invoices:
    ledger.add_invoice(invoice)

# Filter
acme_invoices = ledger.filter_by_vendor("acme")
recent_invoices = ledger.filter_by_date_range(start_date, end_date)

# Export
exporter = LedgerExporter()
exporter.export_to_csv(ledger, "output.csv")

# Import
imported_ledger = exporter.import_from_csv("output.csv")
```

## Data Models

### Invoice
- `vendor`: str - Vendor name
- `invoice_date`: date - Invoice date
- `total`: float - Total amount
- `currency`: str - Currency code (e.g., "USD")
- `line_items`: list[LineItem] - List of line items
- `source_file`: str - Source file path
- `invoice_id`: str - Auto-generated unique ID
- `invoice_number`: str - Invoice number

### LineItem
- `description`: str - Item description
- `quantity`: int - Quantity
- `unit_price`: float - Unit price
- `amount`: float - Total amount (quantity × unit_price)

## CSV Format

The expected CSV format for import:

```csv
invoice_id,Vendor,Date,Total,Currency,Description,Quantity,Unit Price,Amount
INV-001,Acme Corp,2024-01-15,150.00,USD,Widget A,2,50.00,100.00
INV-001,Acme Corp,2024-01-15,150.00,USD,Widget B,1,50.00,50.00
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=invoice_processor --cov-report=term-missing
```

## Project Structure

```
invoice_processor/
├── __init__.py
├── cli.py              # CLI interface
├── exceptions.py       # Custom exceptions
├── ledger.py           # Ledger and LedgerExporter
├── logging_config.py   # Logging configuration
├── models.py           # Data models
├── retry.py            # Retry logic
└── parsers/
    ├── __init__.py
    ├── base.py         # Base parser class
    ├── csv_parser.py   # CSV parser
    └── pdf_parser.py   # PDF parser
tests/
├── conftest.py         # Test fixtures
├── test_comprehensive.py  # Comprehensive tests
└── test_smoke.py       # Smoke tests
```

## License

MIT
