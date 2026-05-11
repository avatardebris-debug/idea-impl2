# Code Review — Phase 1 (Attempt 2/5)

## Blocking Bugs — RESOLVED

### B1. `insert_or_update` return value on duplicate — FIXED
**File:** `app/repositories/review_repo.py`
**Fix:** Changed return type from `Review` to `Optional[Review]`. Now returns `None` when a duplicate is found, so the caller correctly counts it as "skipped" instead of "synced".

### B2. Session-per-review resource leak — FIXED
**File:** `app/tasks/ingestion_task.py`
**Fix:** Moved `SessionLocal()` outside the review loop. One session is opened for the entire task, and closed in a `finally` block after the loop completes.

### B3. Missing pagination in `get_reviews` — FIXED
**File:** `app/services/google_places_client.py`
**Fix:** `get_reviews` now loops on `next_page_token` to fetch all pages of reviews, returning the complete list instead of just the first page of up to 20.

### B4. Blocking `time.sleep` in rate limiter — FIXED
**File:** `app/services/rate_limiter.py`
**Fix:** `wait()` now detects whether it's running in an async context (via `asyncio.get_running_loop()`) and uses `asyncio.sleep` in that case, falling back to `time.sleep` for synchronous contexts.

## Non-Blocking Notes
None

## Verdict
PASS — all blocking bugs resolved
