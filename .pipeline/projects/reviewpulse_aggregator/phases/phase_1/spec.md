## Phase 1 — MVP: Single-Platform Review Ingestion + Basic Sentiment

### Description
Build the foundational pipeline: ingest reviews from **one platform** (Google Places API), store them in a database, and run a basic sentiment analysis pipeline. This gives a working end-to-end flow: reviews flow in, get scored, and are queryable.

### Deliverables
- [ ] Google Places API integration (authenticated, rate-limited)
- [ ] Review model schema and PostgreSQL storage layer
- [ ] Normalization pipeline (standardizes review format across fields)
- [ ] Basic sentiment analysis (VADER or lightweight transformer model)
- [ ] REST API endpoint to retrieve reviews with sentiment scores
- [ ] Scheduled ingestion worker (Celery task, configurable interval)
- [ ] Basic CLI or admin script to trigger manual sync

### Dependencies
- Google Cloud API key with Places API enabled
- PostgreSQL instance
- Redis instance (for Celery broker)
- Python 3.11+, FastAPI, SQLAlchemy, Celery, VADER/sentiment library

### Success Criteria
- [ ] Ingests and stores ≥ 50 reviews from a test business within one sync cycle
- [ ] Sentiment scores are generated within 2 seconds per review
- [ ] API returns structured review objects with sentiment (positive/neutral/negative + score)
- [ ] Zero data loss on restart (idempotent ingestion via review hash dedup)
- [ ] Manual trigger and scheduled sync both work reliably

### Estimated Effort
~2–3 weeks

---