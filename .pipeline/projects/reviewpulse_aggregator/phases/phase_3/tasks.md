# Phase 3 Tasks

- [x] Task 1: FastAPI WebSockets for Real-Time Notifications
  - What: Implement a WebSocket manager to handle connected clients and broadcast new review events.
  - Files:
    - `app/api/ws_manager.py` — WebSocket connection manager class
    - `app/api/routes/notifications.py` — New router for `/api/ws/notifications`
    - `app/main.py` — Include notifications router
    - `app/services/sync_orchestrator.py` — Update to broadcast events when new reviews are upserted
  - Done when:
    - WebSocket clients can connect and receive JSON payloads when new reviews arrive.

- [x] Task 2: Review Export & Feedback Loop API
  - What: Add endpoints to export reviews to CSV and to submit feedback for misclassified sentiment.
  - Files:
    - `app/api/routes/dashboard.py` — Add `/api/dashboard/export` (returns CSV response) and `POST /api/reviews/{review_id}/feedback`
    - `app/models/review.py` — Add `sentiment_feedback` column (Boolean or String) via Alembic migration
    - `alembic/versions/004_sentiment_feedback.py` — Migration
  - Done when:
    - Export endpoint downloads a CSV of reviews matching the given business profile.
    - Feedback endpoint updates the review record correctly.

- [x] Task 3: Email Digest Worker
  - What: Create a Celery task that runs daily/weekly to aggregate review stats and send an email digest.
  - Files:
    - `app/tasks/email_digest.py` — Celery task to compile stats and format HTML email
    - `app/services/email_sender.py` — SMTP/API wrapper for sending emails
    - `celery_config.py` — Schedule the beat task
  - Done when:
    - Celery Beat triggers the task automatically.
    - The task successfully generates an HTML digest and sends it to the business profile's contact email.

- [x] Task 4: Frontend Web Dashboard (React + Vite)
  - What: Scaffold a React frontend using Vite and Tailwind CSS. Implement the core views (Dashboard Overview, Review Inbox, Settings).
  - Files:
    - `frontend/package.json` — Vite + React setup
    - `frontend/src/App.jsx` — Main layout
    - `frontend/src/components/Dashboard.jsx` — Analytics and summary charts
    - `frontend/src/components/ReviewInbox.jsx` — Feed of reviews with reply action
    - `frontend/src/services/api.js` — Axios configuration for backend endpoints
    - `frontend/tailwind.config.js` — Styling configuration
  - Done when:
    - Frontend runs cleanly via `npm run dev`.
    - Dashboard correctly fetches and displays data from the FastAPI backend.
    - WebSocket connection successfully updates the UI upon new reviews.

- [x] Task 5: Docker Compose Production Configuration
  - What: Create a complete Docker setup that runs the frontend, backend, PostgreSQL, Redis, and Celery workers.
  - Files:
    - `Dockerfile.backend` — Production build for FastAPI/Celery
    - `Dockerfile.frontend` — Nginx-based build for the React app
    - `docker-compose.yml` — Multi-container orchestration
    - `nginx.conf` — Reverse proxy configuration (optional, if needed for routing)
  - Done when:
    - `docker-compose up -d` brings up the entire system.
    - The frontend is accessible, and the backend/Celery workers run without connection errors to DB/Redis.
