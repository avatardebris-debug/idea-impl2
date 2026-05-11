# Phase 2 Review

## Overview

Phase 2 adds a SQLite database layer, Pydantic models, configuration management, rate limiting, and a filing parser to the existing SEC Importer fetcher module. The goal is to persist fetched filings locally and provide programmatic access to them.

---

## What's Good

### Schema and Database Layer
- **Clear DDL in `schema.py`**: The `SECDatabase` class creates tables with appropriate constraints (`UNIQUE` on `accession_no`, `FOREIGN KEY` on `filing_items.filing_id`). The `PRAGMA foreign_keys = ON` is correctly set.
- **Repository pattern**: `CompanyRepository`, `FilingRepository`, and `FilingItemRepository` encapsulate SQL queries, keeping the database logic out of the business logic layer.
- **DeduplicationManager**: The `seen_ciks` and `seen_accessions` tables with `PRIMARY KEY` constraints provide a clean, database-level deduplication mechanism. The `mark_*_seen` methods return booleans indicating whether the insert was new, which is useful for callers.
- **Context manager support**: `SECDatabase` supports `with` statements, ensuring connections are closed even on exceptions.

### Rate Limiter
- **Token bucket algorithm**: The `RateLimiter` class implements a proper token bucket with configurable `requests_per_second`, `delay`, `max_retries`, and `base_backoff`. This is appropriate for SEC EDGAR's rate limits.
- **Retry with exponential backoff**: `execute_with_retry` adds jitter to backoff delays, which is a best practice for avoiding thundering herds.
- **Context manager**: The `__enter__`/`__exit__` methods reset the limiter on exit, which is convenient for batch operations.

### Configuration
- **YAML config**: `config.yaml` centralizes settings for database path, rate limiting, logging, and importer batch size. This is a good practice for making the tool configurable without code changes.

### Parser
- **Regex-based section splitting**: `FilingParser.ITEM_PATTERNS` maps common 10-K item headings to labels. This is a pragmatic approach for plain-text filings.
- **XBRL support**: `parse_xbrl` handles basic XBRL fact extraction, which is useful for structured filings.

### CLI
- **Simple argument parsing**: The CLI in `cli.py` provides a straightforward interface for fetching and storing a single filing.

---

## What Needs Improvement

### 1. Critical: `FilingRepository.bulk_insert` Returns Incorrect IDs

```python
def bulk_insert(self, items: List[FilingItemModel]) -> List[int]:
    cursor = self.conn.executemany(...)
    self.conn.commit()
    base_rowid = cursor.lastrowid if cursor.lastrowid else 0
    return list(range(base_rowid, base_rowid + len(items)))
```

**Problem**: `cursor.lastrowid` in `executemany` only returns the rowid of the **first** inserted row, not all of them. The returned list `range(base_rowid, base_rowid + len(items))` assumes contiguous rowids, which is not guaranteed if there are concurrent inserts or deletes. This is a subtle but serious bug that will cause callers to receive incorrect IDs.

**Fix**: Either return `None`/empty list and let callers query by `accession_no`, or use `RETURNING` clause (SQLite 3.35+):

```python
def bulk_insert(self, items: List[FilingItemModel]) -> List[int]:
    cursor = self.conn.executemany(
        """INSERT INTO filing_items (filing_id, accession_no, item_label, item_content, item_type)
           VALUES (?, ?, ?, ?, ?)
           RETURNING id""",
        [(item.filing_id, item.accession_no, item.item_label, item.item_content, item.item_type)
         for item in items],
    )
    self.conn.commit()
    return [row[0] for row in cursor.fetchall()]
```

### 2. Critical: `FilingRepository.get_filing_items_by_filing_id` Uses Wrong Column Name

```python
def get_filing_items_by_filing_id(self, filing_id: str) -> List[dict]:
    cursor = self.conn.execute(
        "SELECT * FROM filing_items WHERE filing_id = ?", (filing_id,)
    )
```

**Problem**: The `filing_id` parameter is typed as `str` but should be `int` since the `filings.id` column is `INTEGER PRIMARY KEY AUTOINCREMENT`. This is a type inconsistency.

### 3. High: `SECDatabase.add_filing` Uses `INSERT OR IGNORE` but Always Returns the ID

```python
cursor.execute("""
    INSERT OR IGNORE INTO filings ...
""", (accession_no, ...))
...
cursor.execute("SELECT id FROM filings WHERE accession_no = ?", (accession_no,))
```

**Problem**: `INSERT OR IGNORE` silently discards duplicates. If a filing already exists, the insert is ignored, and the subsequent `SELECT` returns the existing row's ID. This is actually correct behavior for idempotency, but the method name `add_filing` is misleading—it should be `get_or_add_filing` or similar. More importantly, the method **never** returns `None` in the success path because the `SELECT` will always find the row (either just inserted or pre-existing). The `return row['id'] if row else None` is dead code for the `else` branch.

**Fix**: Rename to `get_or_add_filing` and clarify docstring.

### 4. High: `FilingRepository.bulk_insert` is Never Called

The `SECDatabase.add_filing_items` method uses a loop with individual `INSERT` statements:

```python
def add_filing_items(self, filing_id: int, items: List[FilingItemModel]):
    cursor = self.conn.cursor()
    for item in items:
        cursor.execute("INSERT INTO filing_items ...", (...))
    self.conn.commit()
```

This is inefficient for large filings. The `FilingRepository.bulk_insert` method exists but is never used. Either use it or remove it.

### 5. High: `FilingParser.parse` Hardcodes `filing_id=0` and `accession_no=""`

```python
items.append(FilingItemModel(
    filing_id=0,
    accession_no="",
    item_label=label,
    item_content=content,
    item_type="text",
))
```

**Problem**: The parser has no knowledge of the filing context. When items are stored in the database, the `filing_id` and `accession_no` fields are meaningless (0 and ""). The caller (`cli.py`) does not update these fields after parsing. This means the `filing_items` table contains rows with `filing_id=0` and empty `accession_no`, which violates the semantic intent of the schema.

**Fix**: Pass `filing_id` and `accession_no` into the parser:

```python
def parse(self, text: str, filing_type: str = "10-K",
          filing_id: int = 0, accession_no: str = "") -> List[FilingItemModel]:
    ...
    items.append(FilingItemModel(
        filing_id=filing_id,
        accession_no=accession_no,
        ...
    ))
```

### 6. High: `SECDatabase.add_filing_items` Does Not Validate `filing_id`

```python
def add_filing_items(self, filing_id: int, items: List[FilingItemModel]):
    cursor = self.conn.cursor()
    for item in items:
        cursor.execute("INSERT INTO filing_items ...", (filing_id, ...))
```

If `filing_id` does not correspond to an existing row in `filings`, the `FOREIGN KEY` constraint will fail (since `PRAGMA foreign_keys = ON` is set). This will raise an `sqlite3.IntegrityError` with no clear error message. The method should validate the filing exists first or handle the exception gracefully.

### 7. Medium: `RateLimiter.execute_with_retry` Has a Logic Bug in Backoff Calculation

```python
delay = min(
    self.delay if self.delay > 0 else 0.5
    * (self.base_backoff ** attempt),
    10.0,
)
```

**Problem**: Due to operator precedence, this is parsed as:

```python
delay = min(
    (self.delay if self.delay > 0 else 0.5) * (self.base_backoff ** attempt),
    10.0,
)
```

This is actually correct, but the intent is unclear. If `self.delay > 0`, the backoff formula is ignored entirely, which may not be the desired behavior. The config.yaml sets `delay: 0.1` and `base_backoff: 1.0`, so the backoff is effectively disabled. This is a configuration issue, but the code should make this explicit.

**Fix**: Clarify the logic or restructure:

```python
if self.delay > 0:
    delay = self.delay
else:
    delay = 0.5 * (self.base_backoff ** attempt)
delay = min(delay, 10.0)
```

### 8. Medium: `FilingParser` Patterns Are Fragile

The regex patterns in `ITEM_PATTERNS` and `SECTION_PATTERNS` are hardcoded and will miss variations in filing text (e.g., "Item 1A" vs "Item 1A." vs "Item 1A :"). SEC filings can also have different formatting across years and companies.

**Fix**: Consider using a more robust parsing library or allowing pattern customization via configuration.

### 9. Medium: No Logging in `SECDatabase` or `FilingRepository`

Database operations (inserts, selects) produce no logs. This makes debugging difficult, especially in production. The `config.yaml` specifies a logging format, but it's never used.

**Fix**: Add logging to key operations:

```python
import logging
logger = logging.getLogger(__name__)

class SECDatabase:
    def add_filing(self, ...):
        logger.info("Adding filing %s", accession_no)
        ...
```

### 10. Medium: `TICKER_MAP` in `fetcher.py` Is Hardcoded and Outdated

```python
TICKER_MAP = {
    "0000320193": "AAPL",
    ...
}
```

**Problem**: This map is tiny and will quickly become outdated. The fallback to the SEC EDGAR API is good, but the map should be documented as a cache with a clear TTL or removal strategy.

### 11. Low: `FilingRepository.get_filing_items_by_filing_id` Returns `List[dict]` Instead of `List[FilingItemModel]`

Inconsistent return types across the repository. `FilingRepository.get_filings_by_cik` returns `List[dict]`, while `FilingItemRepository.get_filing_items_by_filing_id` (in the provided code) returns `List[dict]` as well. The `SECDatabase.get_filing_items` method returns `List[FilingItemModel]`. This inconsistency is confusing for callers.

**Fix**: Standardize on returning `List[FilingItemModel]` from all repository methods that return items.

### 12. Low: `SECDatabase` Constructor Does Not Validate `db_path`

```python
def __init__(self, db_path: str = "sec_filings.db"):
    self.db_path = db_path
    self.conn = sqlite3.connect(db_path)
```

If `db_path` is invalid (e.g., a directory), `sqlite3.connect` will raise an obscure error. Consider validating the path or catching the exception with a clearer message.

### 13. Low: `config.yaml` Is Never Loaded

The `config.yaml` file exists but is never read by any Python code. The `SECDatabase` constructor defaults to `"sec_filings.db"`, and the `RateLimiter` uses hardcoded defaults. The configuration file is dead code.

**Fix**: Add a `Config` class that loads `config.yaml` and provides settings:

```python
import yaml

class Config:
    def __init__(self, path: str = "config.yaml"):
        with open(path) as f:
            self._data = yaml.safe_load(f)

    @property
    def db_path(self) -> str:
        return self._data["database"]["db_path"]

    @property
    def rate_limiting(self) -> dict:
        return self._data["rate_limiting"]
```

### 14. Low: No Tests

There are no tests for any of the new code. Given the complexity of the database layer, rate limiter, and parser, tests are essential.

**Fix**: Add tests for:
- `RateLimiter.acquire()` and `execute_with_retry()`
- `SECDatabase.add_filing()` and `get_filing()`
- `FilingParser.parse()` with sample 10-K text
- `FilingRepository.bulk_insert()` (after fixing the bug)

---

## Summary of Required Fixes

| Priority | Issue | File |
|----------|-------|------|
| Critical | `bulk_insert` returns incorrect IDs | `schema.py` |
| Critical | Parser hardcodes `filing_id=0` | `parser.py` |
| High | `add_filing` misleading name | `schema.py` |
| High | `add_filing_items` doesn't validate `filing_id` | `schema.py` |
| High | `bulk_insert` unused, inefficient path exists | `schema.py` |
| Medium | Rate limiter backoff logic unclear | `rate_limiter.py` |
| Medium | No logging | Multiple files |
| Medium | `TICKER_MAP` outdated | `fetcher.py` |
| Medium | Config file never loaded | `config.yaml` |
| Low | Inconsistent return types | `schema.py` |
| Low | No path validation | `schema.py` |
| Low | No tests | All files |

---

## Recommendations for Phase 3

1. **Fix the `bulk_insert` bug** immediately—it will cause data integrity issues.
2. **Load `config.yaml`** into a `Config` class and use it throughout.
3. **Add logging** to all database operations.
4. **Write tests** for the database layer and parser.
5. **Consider using an ORM** like `SQLAlchemy` or `peewee` to reduce boilerplate and improve type safety.
6. **Add error handling** for network failures in the fetcher (currently only `requests.exceptions.RequestException` is caught implicitly).
7. **Add a `--batch` flag** to the CLI to import multiple filings at once, leveraging the rate limiter's retry logic.
