## Phase 1 — MVP: Single-Filing Fetcher & Parser

### Description
Build the smallest useful thing: a command-line tool that fetches and parses one filing (e.g., the latest 10-K for Apple) and outputs the key data in a readable format.

### Deliverable
- A CLI tool (`sec_importer`) that:
  - Takes a ticker symbol and filing type as arguments
  - Resolves ticker → CIK via SEC's CIK lookup
  - Fetches the latest filing of the requested type
  - Parses the filing's text content to extract key fields (filing date, company name, items, summary)
  - Outputs parsed data as JSON to stdout or a file
- No database yet — just fetch + parse + output

### Dependencies
- None (pure Python, `requests`, `BeautifulSoup` for HTML parsing)

### Success Criteria
- [ ] Can resolve a ticker (e.g., "AAPL") to a CIK number
- [ ] Can fetch the latest 10-K filing for that CIK
- [ ] Can parse the filing text and extract: filing type, filing date, company name, item headings, and body text
- [ ] Outputs valid JSON with all extracted fields
- [ ] Handles basic errors (ticker not found, no filing available, network errors)
- [ ] Runs end-to-end in under 30 seconds on a standard connection

### Tasks
- [ ] Set up project structure (src/sec_importer/, tests/, requirements.txt)
- [ ] Implement CIK resolution from ticker (SEC EDGAR company search)
- [ ] Implement filing index lookup (fetch latest filings for a CIK)
- [ ] Implement filing text download (SEC full-text API)
- [ ] Implement filing text parser (extract metadata, items, content)
- [ ] Implement CLI interface (argparse with ticker, filing_type, output options)
- [ ] Write unit tests for parser logic
- [ ] Write integration test (end-to-end fetch + parse)
- [ ] Documentation: README with usage examples

---