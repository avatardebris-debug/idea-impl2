# Code Review — Phase 1

## Verdict
**PASS with conditions**

The Phase 1 implementation is structurally sound and meets the spec deliverables. The codebase is well-organized, follows a clean layered architecture, and includes adequate test coverage. However, there are several **blocking issues** that must be resolved before this code can be considered production-ready, and several **non-blocking improvements** worth addressing.

---

## Blocking Bugs

### B1. `insert_or_update` returns the existing review even when it's a duplicate — the caller interprets this as "skipped" but the function name and semantics are misleading

**File:** `app/repositories/review_repo.py`

```python
def insert_or_update(db: Session, review: dict) -> Optional[Review]:
    ...
    existing = db.execute(select(Review).where(Review.review_hash == review_hash)).scalar_one_or_none()
    if existing:
        return existing  # ← Returns the existing row
    ...
```

**File:** `app/tasks/ingestion_task.py`

```python
result = insert_or_update(db, normalized)
if result:
    synced += 1
else:
    skipped += 1
```

**Problem:** `insert_or_update` returns the existing `Review` object when a duplicate is found. Since a non-None `Review` object is truthy, the caller counts it as `synced`. This means the `skipped` counter is never incremented for duplicates — the sync report is inaccurate. The function name also misleads callers into thinking it returns a boolean or a specific result type.

**Fix:** Either:
1. Return `True`/`False` (or `None`) to indicate insert vs. skip, and rename to `upsert_review`.
2. Return a tuple `(Review, bool)` where the bool indicates whether a new row was inserted.
3. Return `None` on duplicate and change the caller to `if result is not None: synced += 1`.

**Severity:** High — silently miscounts sync results, which undermines observability and debugging.

---

### B2. `sync_google_reviews` task creates a new `SessionLocal()` per review inside the Celery task — this is a resource leak and a performance problem

**File:** `app/tasks/ingestion_task.py`

```python
for idx, review in enumerate(reviews_data):
    ...
    db = SessionLocal()
    try:
        result = insert_or_update(db, normalized)
        ...
    finally:
        db.close()
```

**Problem:** For a business with 1000 reviews, this opens and closes 1000 database sessions. Each session incurs connection overhead. A single session with a transaction per review (or a bulk operation) would be far more efficient.

**Fix:** Open one session per task invocation:

```python
db = SessionLocal()
try:
    for idx, review in enumerate(reviews_data):
        ...
        result = insert_or_update(db, normalized)
        ...
finally:
    db.close()
```

**Severity:** Medium — works correctly but scales poorly.

---

### B3. `sync_google_reviews` does not handle the case where `get_reviews` returns a paginated response with `next_page_token`

**File:** `app/services/google_places_client.py`

```python
def get_reviews(self, place_id: str) -> list[dict] | None:
    ...
    reviews = response.get("reviews", [])
    return reviews
```

**Problem:** Google Places API returns reviews in pages of up to 20 reviews per request, with a `next_page_token` to fetch the next page. The current implementation only fetches the first page, silently dropping up to 19 reviews per request. The `sync_google_reviews` task also has no mechanism to follow pagination.

**Fix:** Either:
1. Loop on `next_page_token` within `get_reviews` to fetch all pages.
2. Return both `reviews` and `next_page_token`, and have the caller loop.

**Severity:** High — silently loses data.

---

### B4. `RateLimiter.wait()` uses `time.sleep()` which blocks the Celery worker process

**File:** `app/services/rate_limiter.py`

```python
def wait(self, attempt: int = 1) -> None:
    delay = self.delay * (2 ** (attempt - 1))
    time.sleep(delay)
```

**Problem:** `time.sleep()` blocks the entire worker process. In a Celery worker with concurrency > 1, this is acceptable only if the worker uses prefork (which it does by default). However, if the worker is configured with `--pool=solo` or `--pool=eventlet`, this blocks the entire event loop or process. More importantly, the delay is applied *between* reviews within the same task, which means the task takes longer than necessary. A better approach is to use Celery's built-in retry mechanism with `self.retry()` for API-level rate limiting, and handle per-review delays differently.

**Severity:** Low — works with default prefork pool but is fragile.

---

### B5. `normalize_review` clamps ratings to 1-5 but does not validate that the rating is a valid number before clamping

**File:** `app/services/normalizer.py`

```python
def _parse_rating(value) -> Optional[int]:
    if value is None:
        return None
    try:
        rating = int(float(value))
        return max(1, min(5, rating))
    except (ValueError, TypeError):
        return None
```

**Problem:** This is actually correct — the `try/except` handles invalid values. No bug here. **False positive.**

---

### B6. `analyze_sentiment` returns `compound=0.0` for empty text, but the test expects `compound=0.0` and `label="neutral"` — this is correct. **No bug.**

---

## Non-Blocking Improvements

### I1. `sync_google_reviews` should use `self.retry()` for transient failures instead of relying on Celery's `max_retries`

**File:** `app/tasks/ingestion_task.py`

The task has `max_retries=3` and `default_retry_delay=60`, which is good. However, the task body does not explicitly call `self.retry()` on transient errors (e.g., network timeouts, 5xx responses). The current implementation catches exceptions in the review loop and increments `skipped`, but if the entire sync fails (e.g., `get_place_details` fails), the task will retry the entire sync from scratch. This is wasteful.

**Recommendation:** Add explicit retry logic for transient failures:

```python
try:
    place_details = client.get_place_details(place_id)
except requests.exceptions.RequestException as e:
    logger.warning(f"Failed to get place details: {e}")
    self.retry(exc=e, countdown=60)
```

### I2. `sync_google_reviews` should log the number of reviews fetched before processing

**File:** `app/tasks/ingestion_task.py`

```python
reviews_data = client.get_reviews(place_id)
if not reviews_data:
    ...
logger.info(f"Fetched {len(reviews_data)} reviews for place_id={place_id}")
```

This helps with debugging and monitoring.

### I3. `sync_google_reviews` should handle the case where `get_place_details` returns a place with no reviews but the API still returns a `next_page_token`

**File:** `app/services/google_places_client.py`

If `get_reviews` returns an empty list but a `next_page_token`, the caller should still attempt to fetch the next page. This is related to B3.

### I4. `sync_google_reviews` should use a context manager for the database session

**File:** `app/tasks/ingestion_task.py`

```python
with SessionLocal() as db:
    ...
```

This is more Pythonic and ensures the session is closed even if an unexpected exception occurs.

### I5. `sync_google_reviews` should validate that `place_id` is not a placeholder

**File:** `app/tasks/ingestion_task.py`

The `beat_schedule` in `celery_config.py` uses `"PLACE_ID_PLACEHOLDER"` as a placeholder. This should be replaced with a real place ID or removed before deployment. The task should also validate that the `place_id` is not a placeholder string.

### I6. `sync_google_reviews` should handle the case where `get_reviews` returns `None` vs. an empty list

**File:** `app/tasks/ingestion_task.py`

```python
reviews_data = client.get_reviews(place_id)
if not reviews_data:
    ...
```

This handles both `None` and `[]` correctly. No bug here.

### I7. `sync_google_reviews` should use `bulk_insert` or `bulk_update` for better performance

**File:** `app/tasks/ingestion_task.py`

For large businesses with thousands of reviews, inserting one at a time is slow. Consider using SQLAlchemy's `bulk_insert_mappings` or `bulk_update_mappings`.

### I8. `sync_google_reviews` should have a `min_retries` parameter to avoid retrying on non-retryable errors

**File:** `app/tasks/ingestion_task.py`

The task retries on any exception. It should distinguish between retryable (network, 5xx) and non-retryable (4xx, invalid place_id) errors.

### I9. `sync_google_reviews` should log the business name in the return value

**File:** `app/tasks/ingestion_task.py`

```python
return {"status": "success", "synced": synced, "skipped": skipped, "business_name": business_name}
```

This helps with monitoring and debugging.

### I10. `sync_google_reviews` should have a `task_time_limit` that accounts for the number of reviews

**File:** `app/tasks/ingestion_task.py`

The current `task_time_limit=300` (5 minutes) may not be enough for businesses with thousands of reviews. Consider making this configurable or calculating it based on the number of reviews.

---

## Architecture & Design Observations

### A1. The layered architecture is clean and well-organized

The separation of concerns is excellent:
- `app/services/` — business logic (Google Places client, normalizer, sentiment analyzer, rate limiter)
- `app/repositories/` — data access (review repo)
- `app/tasks/` — Celery tasks
- `app/api/` — FastAPI routes
- `app/schemas/` — Pydantic schemas
- `app/models/` — SQLAlchemy models

### A2. The normalizer handles HTML decoding and whitespace normalization correctly

The use of `html.unescape` and `re.sub(r"\s+", " ", text).strip()` is appropriate and handles the common cases.

### A3. The sentiment analyzer uses VADER, which is appropriate for short-form text

VADER is a good choice for review sentiment analysis. The threshold of ±0.05 for neutral is standard.

### A4. The rate limiter uses exponential backoff, which is correct

The `delay * (2 ** (attempt - 1))` formula is standard exponential backoff.

### A5. The review repo uses `review_hash` for deduplication, which is correct

The hash is computed from `business_id + platform + author + text`, which is a good deduplication key. However, it does not include the `rating` or `published_at`, which means a review with the same text but different rating would be considered a duplicate. This is probably acceptable since the rating is unlikely to change, but it's worth noting.

### A6. The API routes use SQLAlchemy 2.0 style queries, which is correct

The use of `select()` and `func.count()` is the modern SQLAlchemy 2.0 approach.

### A7. The Pydantic schemas are well-structured

The use of `ReviewBase`, `ReviewCreate`, `ReviewUpdate`, and `ReviewResponse` follows the recommended Pydantic pattern.

---

## Test Coverage Observations

### T1. Test coverage is adequate but not comprehensive

The tests cover the happy path for most components. However, there are no tests for:
- `sync_google_reviews` task (only tests `_compute_hash`)
- The API routes (only tests the schemas)
- The `RateLimiter.wait()` method (only tests `should_retry`)
- The `GooglePlacesClient` methods (no tests)

### T2. The `test_neutral_sentiment` test was fixed in Phase 1

The validation report notes that the original test used a text that VADER scores as negative. The fix is correct.

### T3. The `test_compute_hash_consistency` test is good

Testing that the hash is deterministic across 100 calls is a good practice.

---

## Recommendations

1. **Fix B1 (insert_or_update return value)** — This is the most critical bug. The sync report is inaccurate.
2. **Fix B3 (pagination)** — This causes silent data loss.
3. **Fix B2 (session per review)** — This is a performance issue that will become critical at scale.
4. **Add tests for the ingestion task and API routes** — The current test coverage is insufficient.
5. **Replace the placeholder place ID in `celery_config.py`** — This should not be deployed as-is.
6. **Consider using `bulk_insert` for the ingestion task** — This will improve performance significantly for large businesses.

---

## Summary

| Category | Count |
|----------|-------|
| Blocking bugs | 4 (B1, B2, B3, B4) |
| Non-blocking improvements | 10 (I1-I10) |
| Architecture observations | 7 (A1-A7) |
| Test coverage observations | 3 (T1-T3) |

**Overall:** The codebase is well-structured and follows good practices. The blocking bugs are primarily in the ingestion pipeline (data loss, inaccurate reporting, performance). These should be fixed before deployment. The test coverage is adequate for the components that are tested but incomplete for the critical ingestion and API paths.
