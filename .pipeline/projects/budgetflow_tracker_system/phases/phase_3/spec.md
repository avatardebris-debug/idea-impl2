## Phase 3 — Alert System, Polish & Reporting
> *"The system that watches your money and speaks up when something's wrong."*

#### Description
Add the proactive alerting layer, polish the user experience, and provide comprehensive reporting. This phase transforms the tool from a passive tracker into an active financial guardian. Includes budget deviation alerts, notification delivery, reporting exports, and UX refinements.

#### Deliverables
1. **Budget deviation alert engine** — Monitors spend vs. budget in real-time (or on import); fires alerts at configurable thresholds (e.g., "You've spent 80% of your dining budget").
2. **Notification delivery system** — Supports multiple channels: system tray icon, email (SMTP), terminal notifications, and optional push via a lightweight webhook.
3. **Background monitoring service** — Lightweight daemon that periodically checks budgets and triggers alerts; supports cron or systemd integration.
4. **Reporting module** — Generates PDF/CSV reports (monthly summaries, annual overviews, category deep-dives); exportable via CLI.
5. **Web dashboard (optional)** — Optional lightweight web UI (FastAPI + HTMX or similar) for users who prefer a browser over a terminal.
6. **Settings & configuration UI** — Centralized config for rules, budgets, alert thresholds, notification preferences, and import settings.
7. **Onboarding wizard** — Guided setup for new users: connect bank (CSV), define initial budgets, set alert preferences.

#### Dependencies
- Phase 1 (transaction data, categorization, budgets).
- Phase 2 (forecasting data for predictive alerts, e.g., "Based on your trend, you'll overspend on dining by Friday").

#### Success Criteria
- [ ] Budget deviation alerts fire correctly when thresholds are crossed (tested with synthetic data).
- [ ] Notifications are delivered within 5 minutes of threshold crossing (background service).
- [ ] Predictive alerts (forecast-based) achieve ≥70% precision (few false positives).
- [ ] Monthly report generation completes in <10 seconds for 12 months of data.
- [ ] New user can complete onboarding in <5 minutes.
- [ ] End-to-end: import → categorize → budget → alert cycle works without manual intervention.

---

## 3. Phase Dependency Graph

```
Phase 1 (Core Engine)
    │
    ├──→ Phase 2 (Forecasting)
    │        │
    │        └──→ Phase 3 (Alerts + Polish)
    │
    └──────────────────────→ Phase 3 (Alerts + Polish)
```

- Phase 3 depends on both Phase 1 (for budget data) and Phase 2 (for predictive alerts).
- Phase 2 depends on Phase 1 (for categorized historical data).
- Phases are strictly sequential; each phase's deliverables are prerequisites for the next.

---

## 4. Technical Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    BudgetFlow Tracker                    │
├──────────┬──────────┬───────────┬──────────┬────────────┤
│  Import  │Categorize│ Forecast  │  Alert   │  Report    │
│  Layer   │  Engine  │  Engin