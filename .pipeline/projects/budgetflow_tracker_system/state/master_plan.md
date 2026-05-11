# BudgetFlow Tracker System — Master Implementation Plan

## 1. Idea Analysis

### Core Deliverable
A **local-first personal finance application** that ingests bank transactions, automatically categorizes them, forecasts future cash flow, and alerts the user when spending deviates from their budgets. The entire system runs on the user's machine with no external data dependencies — privacy-preserving by design.

### Key Capabilities
| Capability | Description |
|---|---|
| **Transaction Ingestion** | Import CSV/OFX bank exports; future: direct bank sync via Plaid |
| **Auto-Categorization** | Rule-based + ML-assisted categorization engine |
| **Budget Management** | Create, edit, and track budgets per category and time period |
| **Cash Flow Forecasting** | Time-series analysis to predict future income/expenses |
| **Deviation Alerts** | Threshold-based alerts when spending exceeds budget |
| **Reporting & Visualization** | Dashboards, charts, and exportable reports |

### Architecture Notes
- **Local-first storage:** SQLite database on disk; all data stays on the user's machine.
- **Tech stack:** Python (fastapi for optional API, pandas for data processing, sqlite3 for storage), with a CLI-first design and optional web UI (via a lightweight frontend or terminal UI).
- **Categorization engine:** Two-tier — (1) deterministic rules (keyword matching, merchant whitelists), (2) ML model (fine-tuned lightweight classifier like fastText or scikit-learn RandomForest) trained on user's historical categorizations.
- **Forecasting engine:** Exponential smoothing (Holt-Winters) and linear regression on time-bucketed data.
- **Alert system:** Cron-based or background service that periodically checks budgets vs. actuals and fires notifications (system tray, email, or push).

### Risks & Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Bank CSV formats vary wildly | High | Build a robust parser with format detection; provide a manual mapping wizard |
| ML model accuracy on small datasets | Medium | Start with rule-based only; ML is opt-in after enough training data |
| User adoption friction | Medium | CLI-first with zero-config defaults; progressive disclosure of complexity |
| Performance on large transaction histories | Low | SQLite indexing + pagination; lazy loading |
| Security of local data | Medium | Optional SQLite encryption (SQLCipher); file-level encryption at rest |

---

## 2. Phase Breakdown

### Phase 1 — MVP: Core Transaction Engine & Categorization
> *"The smallest useful thing: ingest transactions, categorize them, and see where money went."*

#### Description
Build the foundational data layer and categorization pipeline. Users can import bank transaction CSVs, have them auto-categorized, and view spending summaries by category. This is the irreducible core — without it, nothing else works.

#### Deliverables
1. **SQLite schema & migration system** — Tables for `accounts`, `transactions`, `categories`, `budgets`, `transaction_rules`.
2. **CSV import pipeline** — Auto-detects bank format, maps columns, validates data, bulk-inserts into SQLite.
3. **Rule-based categorization engine** — User defines rules (e.g., "merchant contains 'Starbucks' → Category: Food & Drink"); engine applies rules to imported transactions.
4. **CLI dashboard** — Terminal-based view showing spending by category over a configurable date range.
5. **Budget creation UI (CLI)** — Set monthly budgets per category; view progress bars showing spend vs. budget.

#### Dependencies
- None (this is the foundation phase).

#### Success Criteria
- [ ] User can import a CSV from any major US bank (Chase, Wells Fargo, Bank of America, Capital One) and see transactions loaded.
- [ ] Auto-categorization correctly classifies ≥80% of transactions on first pass (using default rules).
- [ ] User can view a spending summary by category for any date range in the CLI.
- [ ] Budget creation and progress tracking works for at least 3 categories.
- [ ] All data is stored locally in SQLite — no network calls.

---

### Phase 2 — Cash Flow Forecasting & Visualization
> *"Now that we know where money went, predict where it's going."*

#### Description
Extend the system with forecasting capabilities. Using historical categorized transaction data, the system models income and expense patterns to predict future cash flow. Adds a visualization layer so users can see trends, seasonal patterns, and projections.

#### Deliverables
1. **Time-bucketing engine** — Groups transactions into configurable intervals (daily, weekly, monthly) with proper handling of irregular import dates.
2. **Forecasting models** — Implements Holt-Winters exponential smoothing and linear regression; selects best model per category.
3. **Cash flow projection engine** — Produces forward-looking income/expenses for the next 30/60/90 days with confidence intervals.
4. **Visualization module** — Chart generation (matplotlib/plotly) for spending trends, category breakdowns, and forecast curves.
5. **Forecast CLI report** — Text-based or chart-based output showing projected cash position and key inflection points.
6. **Pattern detection** — Identifies recurring transactions (subscriptions, rent, salary) and flags anomalies (unusual charges).

#### Dependencies
- Phase 1 (transaction data + categorization must exist before forecasting can occur).

#### Success Criteria
- [ ] Forecast model achieves ≤15% error rate on backtested 30-day predictions (compared to actuals).
- [ ] User can generate a cash flow chart for any 90-day window.
- [ ] Recurring transaction detection identifies ≥90% of recurring patterns in 6+ months of data.
- [ ] Anomaly detection flags at least 80% of genuinely unusual transactions.
- [ ] All forecasting computations run locally; no external API calls.

---

### Phase 3 — Alert System, Polish & Reporting
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
│  Layer   │  Engine  │  Engine   │  Engine  │  Engine    │
├──────────┴──────────┴───────────┴──────────┴────────────┤
│                   Data Layer (SQLite)                    │
│  transactions │ categories │ budgets │ rules │ accounts │
├──────────────────────────────────────────────────────────┤
│                   Storage Layer (Local-First)            │
│              SQLite + optional SQLCipher                 │
├──────────────────────────────────────────────────────────┤
│                    Delivery Layer                        │
│          CLI (primary) │ Web (optional) │ Daemon         │
└──────────────────────────────────────────────────────────┘
```

### Data Model (Core Tables)
| Table | Key Fields |
|---|---|
| `accounts` | id, name, type (checking/savings/credit), currency |
| `transactions` | id, account_id, date, amount, description, merchant, raw_category, auto_category, confidence_score |
| `categories` | id, name, parent_id, color, budget_limit |
| `budgets` | id, category_id, period (monthly/weekly), amount, rollover |
| `transaction_rules` | id, pattern (regex), category_id, priority, active |
| `alerts` | id, transaction_id, message, severity, read, created_at |
| `forecast_data` | id, category_id, date, predicted_amount, confidence_lower, confidence_upper |

### File Structure (Target)
```
budgetflow_tracker/
├── src/
│   ├── core/
│   │   ├── database.py      # SQLite schema & migrations
│   │   ├── models.py        # Pydantic data models
│   │   └── config.py        # Settings management
│   ├── import/
│   │   ├── csv_parser.py    # Multi-bank CSV detection & parsing
│   │   └── ofx_parser.py    # OFX format support (future)
│   ├── categorize/
│   │   ├── rule_engine.py   # Deterministic rule application
│   │   └── ml_engine.py     # ML-assisted categorization (Phase 2+)
│   ├── forecast/
│   │   ├── bucketing.py     # Time-bucketing engine
│   │   ├── models.py        # Holt-Winters, linear regression
│   │   └── patterns.py      # Recurring transaction detection
│   ├── alerts/
│   │   ├── monitor.py       # Budget deviation checker
│   │   ├── notifier.py      # Multi-channel notification delivery
│   │   └── predictor.py     # Forecast-based alert generation
│   ├── reports/
│   │   ├── generators.py    # Report generation (PDF/CSV)
│   │   └── charts.py        # Chart rendering
│   └── ui/
│       ├── cli.py           # Terminal dashboard
│       └── web.py           # Optional web UI
├── tests/
├── data/
│   └── default_rules.db     # Default categorization rules
├── config/
│   └── budgetflow.yaml      # User configuration
├── scripts/
│   └── daemon.py            # Background monitoring service
├── pyproject.toml
└── README.md
```

---

## 5. Risk Register

| # | Risk | Phase Affected | Severity | Mitigation |
|---|---|---|---|---|
| R1 | CSV format fragmentation across banks | Phase 1 | High | Build format auto-detection; provide manual column mapping wizard |
| R2 | Rule-based categorization accuracy < 80% | Phase 1 | Medium | Include comprehensive default rule set; allow easy rule editing |
| R3 | Forecasting inaccuracy on volatile income | Phase 2 | Medium | Separate income/expense forecasting; use wider confidence intervals for volatile categories |
| R4 | Alert fatigue (too many notifications) | Phase 3 | Medium | Smart alert throttling; digest mode; configurable sensitivity |
| R5 | User abandons after initial setup | Phase 3 | High | Onboarding wizard; progressive complexity; quick wins (immediate visual feedback) |
| R6 | SQLite concurrency issues with daemon | Phase 3 | Low | WAL mode; connection pooling; single-writer pattern |

---

## 6. Milestones & Timeline (Estimates)

| Milestone | Target | Cumulative Deliverable |
|---|---|---|
| M1: Core engine complete | End of Phase 1 | Import → Categorize → Budget → View |
| M2: Forecasting online | End of Phase 2 | + Forecast → Anomaly Detection |
| M3: Alert system live | End of Phase 3 | + Alerts → Reports → Polish |

---

## 7. Open Questions

1. **Target platform:** CLI only, or desktop app (Electron/Tauri) as well?
2. **Bank sync:** Phase 1 is CSV-only. Should OFX/QIF import be in Phase 1 or deferred?
3. **ML model choice:** fastText, scikit-learn RandomForest, or a small transformer? Trade-off: accuracy vs. dependency size.
4. **Web UI depth:** Minimal (charts + data tables) or full-featured (budget editing, rule management)?
5. **Multi-currency:** Support for non-USD currencies in Phase 1?

---

*Plan created by Idea Planner. Ready for executor handoff.*
