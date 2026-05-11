# Phase 2 Review — SEC Importer 2

## Overview

Phase 2 delivers a functional CLI tool (`sec-importer`) that fetches SEC EDGAR filings via the JSON API, parses them, stores them in SQLite, and supports delta-sync. The architecture is clean: `fetcher` → `parser` → `storage` → `sync` → `cli`.

---

## ✅ Strengths

### 1. Clean Architecture & Separation of Concerns
- `fetcher.py` handles only HTTP/EDGAR API interaction with rate limiting and retry logic.
- `parser/xbrl_parser.py` handles only XBRL XML parsing.
- `storage.py` handles only database operations.
- `sync.py` orchestrates the pipeline.
- `cli.py` handles only user interaction.

This makes each module independently testable and maintainable.

### 2. Robust Error Handling in Fetcher
- `SECFetcher` implements exponential backoff for 429 rate limits.
- `httpx` is used with proper timeout configuration.
- CIK lookup from ticker is graceful (returns `None` on failure rather than crashing).
- Context manager (`__enter__`/`__exit__`) ensures session cleanup.

### 3. Delta-Sync Logic
- `sync.py` correctly deduplicates by `accession_number` using `get_existing_accession_numbers()`.
- Per-ticker summary in CLI output is user-friendly.
- `upsert_company()` ensures company metadata is kept current.

### 4. CLI Design
- Click-based CLI with `--db-path` and `--log-level` options.
- `add-ticker` command for easy ticker management.
- `stats` command provides quick database introspection.
- `list` command with optional ticker filter.

### 5. Database Schema
- `Filing` model has all necessary fields from the SEC API.
- `Company` model supports ticker → CIK/name mapping.
- Indexes on `ticker`, `filing_date`, and `accession_number` support efficient queries.

---

## ⚠️ Issues

### 🔴 Critical

#### 1. `xbrl_parser.py` — Incomplete XBRL Parsing (No HTML Parsing)
**File:** `sec_importer/parser/xbrl_parser.py`

The `XBRLParser` class only handles XBRL XML content. It does **not** handle HTML filings (e.g., 10-K text, 8-K items, proxy statements). The `parse_filings()` function in `__init__.py` only calls `XBRLParser.parse_xbrl()` for `.xml` files. HTML filings are silently ignored.

**Impact:** Users get no parsed content for the majority of filing types (8-K, DEF 14A, 10-K text sections, etc.).

**Recommendation:** 
- Add an `HTMLParser` class that extracts text from HTML filings using `BeautifulSoup`.
- Update `parse_filings()` to route `.html` files to the HTML parser.
- Consider extracting structured data from HTML (e.g., table data from financial statements).

#### 2. `sync.py` — CIK Lookup Race Condition
**File:** `sec_importer/sync.py`, line ~85

```python
cik = fetcher.get_cik_from_ticker(ticker)
company_name = None
if cik:
    ticker_url = TICKER_TO_CIK_URL.format(ticker=ticker.upper())
    try:
        resp = fetcher._session.get(ticker_url)
```

`get_cik_from_ticker()` already fetches the same URL internally. This code fetches it **again**, doubling API calls per ticker.

**Impact:** Unnecessary API load, potential rate limiting.

**Recommendation:** Remove the duplicate fetch. Use the CIK and company name returned by `get_cik_from_ticker()` directly, or modify `get_cik_from_ticker()` to return the company name as well.

#### 3. `storage.py` — `upsert_company()` Uses `INSERT ... ON CONFLICT` but `Company` Table Has No Unique Constraint on `ticker`
**File:** `sec_importer/storage.py`, line ~100

```python
session.execute(text("""
    INSERT INTO company (ticker, cik, name)
    VALUES (:ticker, :cik, :name)
    ON CONFLICT(ticker) DO UPDATE SET cik = :cik, name = :name
"""))
```

The `Company` table is created without a `UNIQUE` constraint on `ticker`:

```python
CREATE TABLE IF NOT EXISTS company (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    cik TEXT,
    name TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Impact:** `ON CONFLICT(ticker)` will never trigger because there's no unique constraint. Duplicate rows will be inserted, causing data integrity issues.

**Recommendation:** Add `UNIQUE(ticker)` to the `CREATE TABLE` statement:

```python
CREATE TABLE IF NOT EXISTS company (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL UNIQUE,
    cik TEXT,
    name TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 🟡 Medium

#### 4. `parser/__init__.py` — No HTML Parsing Support
**File:** `sec_importer/parser/__init__.py`

```python
def parse_filings(raw_filings: list[dict]) -> list[dict]:
    ...
    for filing in raw_filings:
        ...
        if filing_type in ("10-K", "10-Q", "20-F"):
            # Only XBRL parsers are called for these types
            if filename.endswith(".xml"):
                ...
```

- No HTML parser is imported or used.
- Filing types like `8-K`, `DEF 14A`, `S-1`, `424B2` are never parsed.
- The `parsed` list only contains XBRL-parsed filings, losing all other filing data.

**Recommendation:** Add HTML parsing support and include all filing types in the parsed output.

#### 5. `sync.py` — `limit_per_ticker` Applied After Parsing, Not Before Fetching
**File:** `sec_importer/sync.py`, line ~70

```python
parsed = parse_filings(raw_filings)
if not parsed:
    ...
parsed = parsed[:limit]  # Applied after parsing
```

The `limit` is applied to the **parsed** results, not the fetched results. If `parse_filings()` filters out invalid filings, the effective limit may be lower than intended. Also, the fetcher already returns `limit` filings, so this is redundant.

**Recommendation:** Apply the limit at the fetcher level (already done) and remove the post-parse slicing, or clarify the intent.

#### 6. `fetcher.py` — `get_cik_from_ticker()` Returns CIK but Not Company Name
**File:** `sec_importer/fetcher.py`, line ~140

```python
def get_cik_from_ticker(self, ticker: str) -> Optional[str]:
    ...
    cik = data.get("cik")
    ...
    return cik_str
```

The SEC API response includes `companyName`, but it's discarded. This forces the caller (`sync.py`) to fetch the same URL again (see Issue #2).

**Recommendation:** Return both CIK and company name:

```python
def get_cik_from_ticker(self, ticker: str) -> Optional[tuple[str, str]]:
    ...
    cik = data.get("cik")
    name = data.get("companyName")
    if cik:
        return (str(cik).zfill(10), name)
    return None
```

#### 7. `storage.py` — `get_last_sync_date()` Returns `None` for New Tickers, Causing Full Re-sync
**File:** `sec_importer/storage.py`, line ~130

```python
def get_last_sync_date(session, ticker: str) -> Optional[str]:
    result = session.execute(text("""
        SELECT MAX(filing_date) FROM filings WHERE ticker = :ticker
    """), {"ticker": ticker}).scalar()
    return result  # Returns None if no filings exist
```

For new tickers, `last_sync` is `None`, which means the fetcher fetches the **latest** filings (since `fetch_filings()` uses the SEC API's "recent" endpoint, not a date-filtered one). This is actually correct behavior for delta-sync (fetch recent filings), but the variable name `last_sync_date` is misleading — it's not a sync date, it's the most recent filing date in the DB.

**Recommendation:** Rename to `get_most_recent_filing_date()` for clarity.

#### 8. `cli.py` — `add-ticker` Command Doesn't Validate Ticker Format
**File:** `sec_importer/cli.py`, line ~110

```python
ticker = ticker.strip().upper()
if not ticker:
    ...
```

No validation that the ticker is a valid SEC ticker format (e.g., 1-5 uppercase letters). Users can add invalid tickers like `""`, `"123"`, or `"A B"`.

**Recommendation:** Add basic validation:

```python
import re
if not re.match(r'^[A-Z]{1,5}$', ticker):
    click.echo(click.style(f"Invalid ticker format: {ticker}", fg="red"))
    sys.exit(1)
```

### 🟢 Low Priority

#### 9. `xbrl_parser.py` — Namespace Handling Is Fragile
**File:** `sec_importer/parser/xbrl_parser.py`, line ~70

```python
nsmap = {
    "xbrli": "http://www.xbrl.org/2003/instance",
    ...
}
for elem in soup.find_all(True):
    tag = elem.name
    if "xbrli" in tag.lower() or elem.get("contextRef") or elem.get("unitRef"):
```

The check `"xbrli" in tag.lower()` is fragile. XBRL elements may use different namespace prefixes (e.g., `xbrldi`, `xbrlnt`). The `contextRef`/`unitRef` check is better but still incomplete.

**Recommendation:** Use namespace-aware queries:

```python
for elem in soup.find_all(nsmap={"xbrli": "http://www.xbrl.org/2003/instance"}):
    ...
```

#### 10. `xbrl_parser.py` — `_get_fact_label()` Searches All `link:label` Elements Without Namespace
**File:** `sec_importer/parser/xbrl_parser.py`, line ~130

```python
for label_elem in soup.find_all("link:label"):
    if label_elem.get("conceptName") == concept:
```

The `link:` namespace may not be defined in the document, or the label may be in a different role. This will miss many labels.

**Recommendation:** Search for labels in all linkbase namespaces or use the XBRL taxonomy's standard label roles.

#### 11. `storage.py` — `insert_filings()` Uses Raw SQL Instead of ORM
**File:** `sec_importer/storage.py`, line ~150

```python
session.execute(text("""
    INSERT INTO filings (ticker, filing_type, filing_date, ...)
    VALUES (:ticker, :filing_type, :filing_date, ...)
"""))
```

The ORM `Filing` model is defined but not used for inserts. Raw SQL is used instead, which bypasses ORM validation and makes schema changes harder.

**Recommendation:** Use ORM for inserts:

```python
filing = Filing(
    ticker=record["ticker"],
    filing_type=record["filing_type"],
    ...
)
session.add(filing)
session.commit()
```

#### 12. `sync.py` — No Progress Indication During Long Syncs
**File:** `sec_importer/sync.py`

For tickers with many filings, the sync runs silently. Users have no feedback on progress.

**Recommendation:** Add progress logging:

```python
for i, record in enumerate(new_filings):
    if i % 10 == 0:
        logger.info(f"  Processing filing {i}/{len(new_filings)}...")
```

#### 13. `config.py` — `DEFAULT_DB_PATH` Uses `..` Which Is Fragile
**File:** `sec_importer/config.py`, line ~8

```python
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "sec_importer.db")
```

This resolves to the parent directory of `sec_importer/`, which is the project root. This is fragile if the package is installed in a different location.

**Recommendation:** Use `Path` and resolve relative to the current working directory or a config directory:

```python
DEFAULT_DB_PATH = os.path.join(os.getcwd(), "sec_importer.db")
```

---

## 📋 Summary

| Severity | Count | Key Issues |
|----------|-------|------------|
| 🔴 Critical | 3 | No HTML parsing, duplicate CIK fetch, missing UNIQUE constraint |
| 🟡 Medium | 5 | No HTML parser in `__init__.py`, limit applied post-parse, fragile CIK return, misleading variable name, no ticker validation |
| 🟢 Low | 5 | Fragile namespace handling, missing label search, raw SQL vs ORM, no progress indication, fragile DB path |

## 🎯 Recommended Priority

1. **Fix UNIQUE constraint on `Company.ticker`** (Issue #3) — Data integrity risk.
2. **Add HTML parsing support** (Issues #1, #4) — Core functionality gap.
3. **Fix duplicate CIK fetch** (Issues #2, #6) — Performance/rate-limiting risk.
4. **Add ticker validation** (Issue #8) — User experience.
5. **Use ORM for inserts** (Issue #11) — Maintainability.
