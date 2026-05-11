## Phase 2 — Filing Content Parser

**Goal**: Download and parse the actual content of filings — both structured (XBRL financial data) and unstructured (text from 8-K, 10-K MD&A, etc.).

### Description
- Download filing documents (HTML, XML, XBRL) from SEC EDGAR based on stored accession numbers
- Parse XBRL iXBRL data to extract financial statement facts (revenue, EPS, assets, liabilities, etc.)
- Parse HTML filings to extract text content (MD&A, risk factors, management discussion)
- Store parsed content in the database alongside metadata
- Add a filing detail view: `sec-importer show <accession_number>`

### Deliverable
- `sec_importer/parser/xbrl_parser.py` — XBRL fact extraction (income statement, balance sheet, cash flow)
- `sec_importer/parser/html_parser.py` — text extraction from HTML filings
- `sec_importer/parser/__init__.py` — unified parser interface
- Database schema updated with `filing_contents` table (JSONB for XBRL facts)
- CLI: `sec-importer show <accession>` displays parsed financial data
- Sample parsed data for at least 3 companies latest 10-K

### Dependencies
- Phase 1 (metadata + storage must exist)
- `xbrlutil` or custom XBRL parsing library
- `lxml` / `BeautifulSoup` for HTML parsing

### Success Criteria
- [ ] Successfully downloads and parses XBRL data for 10-K and 10-Q filings
- [ ] Extracts at least 20 financial facts per filing (revenue, net income, total assets, etc.)
- [ ] HTML text extraction works for 8-K and 10-K filings
- [ ] Parsed data stored and queryable via CLI
- [ ] Parser handles malformed XBRL gracefully (marks partial parse, does not crash)
- [ ] End-to-end: `sec-importer sync` fetches new filings AND parses them

---

