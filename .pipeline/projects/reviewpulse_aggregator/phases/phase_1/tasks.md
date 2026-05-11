# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and dependency setup
  - What: Create the project directory structure, virtual environment config, requirements file, and base configuration (PostgreSQL, Redis, Google API key). Set up FastAPI app entry point and SQLAlchemy engine.
  - Files: reviewpulse_aggregator/requirements.txt, reviewpulse_aggregator/config.example, reviewpulse_aggregator/app/__init__.py, reviewpulse_aggregator/app/main.py, reviewpulse_aggregator/app/config.py, reviewpulse_aggregator/app/database.py
  - Done when: `pip install -r requirements.txt` succeeds; `uvicorn app.main:app` starts the FastAPI dev server; config loads DB URL, Redis URL, and Google API key from config file; OpenAPI docs at /docs respond with 200.

- [ ] Task 2: Review model schema and PostgreSQL storage layer
  - What: Define SQLAlchemy models for Review (id, business_id, platform, author, rating, text, published_at, source_url, sentiment_score, sentiment_label, review_hash, created_at, updated_at). Create migration script (Alembic) and idempotent upsert logic keyed on review_hash for dedup.
  - Files: reviewpulse_aggregator/app/models/review.py, reviewpulse_aggregator/app/repositories/review_repo.py, reviewpulse_aggregator/alembic.ini, reviewpulse_aggregator/alembic/env.py, reviewpulse_aggregator/alembic/versions/001_initial.py
  - Done when: Alembic migration creates the reviews table in PostgreSQL; review_repo.py provides insert_or_update() that skips duplicate review_hash entries; a test script can insert and re-insert the same review without creating duplicates.

- [ ] Task 3: Google Places API integration with rate limiting
  - What: Implement a Google Places client that fetches reviews for a given business (by place_id). Use google-api-python-client or requests with the Places API endpoint. Add rate-limiting (exponential backoff on 429, configurable delay between requests). Paginate through all reviews.
  - Files: reviewpulse_aggregator/app/services/google_places_client.py, reviewpulse_aggregator/app/services/rate_limiter.py, reviewpulse_aggregator/tests/test_google_places_client.py
  - Done when: Client fetches >= 50 reviews for a test place_id in one call chain; handles HTTP 429 with retry/backoff; respects a configurable max-retries and delay; returns a list of normalized raw review dicts.

- [ ] Task 4: Normalization pipeline and sentiment analysis
  - What: Build a normalization function that maps Google Places review fields to the unified Review schema (strips HTML, normalizes dates, extracts author name, etc.). Implement sentiment analysis using the VADER sentiment lexicon (from nltk) to produce a compound score and a label (positive/neutral/negative).
  - Files: reviewpulse_aggregator/app/services/normalizer.py, reviewpulse_aggregator/app/services/sentiment_analyzer.py, reviewpulse_aggregator/tests/test_normalizer.py, reviewpulse_aggregator/tests/test_sentiment_analyzer.py
  - Done when: normalizer() transforms raw Google review dicts into clean dicts matching the Review model schema; sentiment_analyzer() returns (score: float, label: str) within < 2 seconds per review; tests cover positive, neutral, and negative review samples with expected label ranges.

- [ ] Task 5: Ingestion worker (Celery) and manual sync CLI
  - What: Create a Celery task that orchestrates the full sync cycle: fetch reviews via GooglePlacesClient -> normalize -> analyze sentiment -> upsert to DB. Wire it as a scheduled task (configurable interval via Celery beat). Build a CLI script (click or argparse) to trigger a manual sync from the command line.
  - Files: reviewpulse_aggregator/app/tasks/ingestion_task.py, reviewpulse_aggregator/app/worker.py, reviewpulse_aggregator/celery_config.py, reviewpulse_aggregator/scripts/sync_reviews.py, reviewpulse_aggregator/tests/test_ingestion_task.py
  - Done when: `celery -A app.worker worker --loglevel=info` starts without errors; Celery beat schedules the ingestion task at the configured interval; `python -m scripts.sync_reviews` runs a one-shot sync that inserts new reviews and skips duplicates; end-to-end test confirms >= 50 reviews are stored with sentiment scores after a sync.

- [ ] Task 6: REST API endpoint for querying reviews with sentiment
  - What: Build a FastAPI endpoint GET /reviews that returns paginated reviews with their sentiment scores and labels. Support optional filters: sentiment_label, rating_min, rating_max, date_from, date_to. Add response validation with Pydantic schemas.
  - Files: reviewpulse_aggregator/app/api/routes/reviews.py, reviewpulse_aggregator/app/api/deps.py, reviewpulse_aggregator/app/schemas/review.py, reviewpulse_aggregator/tests/test_reviews_api.py
  - Done when: GET /reviews returns a JSON list of review objects with sentiment fields; pagination params (page, page_size) work correctly; filter params narrow results as expected; all endpoints documented in /docs; test suite confirms correct filtering and 200/400 status codes.