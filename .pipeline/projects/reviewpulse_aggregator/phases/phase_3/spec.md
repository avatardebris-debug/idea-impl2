# Phase 3 Specification: Business Owner Dashboard + Notifications + Intelligence

## 1. Overview
In Phase 3, we build out the full business owner experience for the ReviewPulse Aggregator. While Phase 1 and 2 established a robust backend pipeline for ingesting, analyzing, and drafting responses to reviews across multiple platforms (Google, Yelp, Facebook), this phase delivers the interactive frontend and advanced intelligence features.

The key additions are a polished React-based dashboard, real-time WebSocket notifications for incoming reviews, automated email digests, sentiment trend analytics, and a production-ready Docker Compose deployment setup.

## 2. Architecture & Components

### 2.1 Frontend (React Dashboard)
- **Tech Stack**: React, Vite, Tailwind CSS, Recharts (for analytics).
- **Core Views**:
  - **Overview Board**: Aggregated sentiment scores, recent reviews, platform breakdown.
  - **Reviews Inbox**: Feed of all reviews across platforms, filtering by sentiment/platform, and a quick-reply interface.
  - **Analytics**: Weekly/monthly sentiment trends, response rate metrics.
  - **Settings**: Manage business profiles, response tone preferences, and API keys.
- **Real-Time Updates**: WebSocket connection to the backend to receive instant alerts when new reviews arrive.

### 2.2 Backend Additions (FastAPI)
- **WebSockets**: A new router (`/api/ws/notifications`) to push real-time alerts to connected frontend clients.
- **Exporting**: Endpoints to generate and download CSV reports of reviews and sentiment data.
- **Feedback Loop**: An endpoint to flag misclassified sentiment (updating the database to be used for future model retraining).
- **Multi-Business Support**: Enhance query models to properly partition data by `business_id` so an agency or chain can manage multiple locations.

### 2.3 Email Digests & Automation
- **Digest Task**: A daily/weekly Celery beat task that queries new reviews, aggregates sentiment, and sends an HTML email report using an SMTP server or SendGrid/Resend API.

### 2.4 Deployment
- **Docker Compose**: A full `docker-compose.yml` that spins up the FastAPI app, React frontend (via Nginx or serve), PostgreSQL database, Redis, and Celery workers/beat.

## 3. Data Models
- Update existing `Review` and `BusinessProfile` models to ensure `owner_id` or `agency_id` is supported if needed for multi-tenant access (simplifying for MVP: multi-business support per account).

## 4. Acceptance Criteria
1. Business owner can log into the React dashboard and view all aggregated reviews.
2. New reviews trigger a real-time WebSocket notification in the frontend.
3. Response drafts can be selected and marked as "published/approved".
4. CSV export of reviews works.
5. Daily email digests are generated via Celery Beat.
6. The entire stack boots cleanly via `docker-compose up`.
