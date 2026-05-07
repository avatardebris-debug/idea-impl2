# SEC Importer

A system that imports SEC filing data for US companies — fetching, parsing, normalizing, and storing structured data from SEC filings (10-K, 10-Q, 8-K, etc.).

## Dependencies

Install with:

```bash
pip install -r requirements.txt
```

Required packages:
- `requests` — HTTP client for SEC EDGAR API
- `beautifulsoup4` — HTML/XML parsing
- `pytest` — Testing framework

## Usage

### CLI

```bash
# Fetch and display the latest 10-K for Apple (AAPL)
sec_importer AAPL --type 10-K

# Save output to a file
sec_importer AAPL --type 10-K --output aapl_10k.json

# Show help
sec_importer --help
```

### Programmatic API

```python
from sec_importer.fetcher import resolve_ticker_to_cik, get_latest_filing, download_filing_text
from sec_importer.parser import parse_filing

# Resolve ticker to CIK
cik = resolve_ticker_to_cik("AAPL")

# Get latest 10-K filing metadata
filing = get_latest_filing(cik, "10-K")

# Download the filing text
text = download_filing_text(filing["accession_no"])

# Parse the filing
parsed = parse_filing(text)
print(parsed["company_name"])
print(parsed["items"])
```

## Success Criteria

- `python -m sec_importer` runs without import errors
- `sec_importer AAPL --type 10-K` resolves ticker, fetches latest 10-K, parses it, and prints valid JSON
- `--output file.json` writes to a file
- `--help` shows usage
- Full pipeline completes in under 30 seconds
