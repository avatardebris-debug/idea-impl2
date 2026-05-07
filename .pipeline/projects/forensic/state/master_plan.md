# Forensic Accounting Suite — Master Implementation Plan

## Overview

A forensic accounting suite for detecting corporate fraud, predicting earnings,
understanding capital flows, and analyzing SEC filing data. The system ingests
structured data from the `sec_importer` project, runs a variety of analytical
methods to detect plausible fraud, flags red-flags and anomalies, rates findings
using a composite fraud score, and produces both high-level summaries and
detailed evidence.

---

## Architecture Notes

### Dependency Integration

The suite depends on `sec_importer` (`/workspace/idea impl/.pipeline/projects/sec_importer/workspace`).
The following modules, classes, and functions will be imported and used:

| sec_importer Module | Imported Items | Usage in Forensic Suite |
|---|---|---|
| `sec_importer.fetcher` | `resolve_ticker_to_cik`, `get_cik_submissions`, `get_latest_filing`, `download_filing_text` | Fetching ticker→CIK mappings, retrieving filing metadata, downloading raw filing text |
| `sec_importer.parser` | `FilingParser`, `parse_filing` | Parsing raw filing text into structured `FilingItemModel` sections (Item labels, content, types) |
| `sec_importer.models` | `CompanyModel`, `FilingModel`, `FilingItemModel` | Pydantic validation models for companies, filings, and parsed filing items |
| `sec_importer.repository` | `SECDatabase`, `CompanyRepository`, `FilingRepository`, `FilingItemRepository`, `DeduplicationManager` | SQLite-backed CRUD with deduplication for companies, filings, and filing items |
| `sec_importer.schema` | `init_db`, `CREATE_COMPANIES_TABLE`, `CREATE_FILINGS_TABLE`, `CREATE_FILING_ITEMS_TABLE`, `CREATE_INDEXES` | Database schema initialization (DDL) |
| `sec_importer.config` | `Config` | Loading YAML config with defaults for DB path, rate limits, logging |
| `sec_importer.rate_limiter` | `RateLimiter` | Token-bucket rate limiting for SEC API calls |

**Key integration contract**: The forensic suite will use `SECDatabase` as its
data store, `FilingParser` to parse fetched filings, and `Config` for
configuration. All data models are Pydantic-based and will be used directly.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Forensic Suite                     │
│                                                       │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Data     │  │  Analysis    │  │  Scoring &    │  │
│  │  Ingestion│  │  Engine      │  │  Reporting    │  │
│  │  Layer    │  │              │  │  Layer        │  │
│  └────┬──────┘  └──────┬───────┘  └───────┬───────┘  │
│       │                │                   │          │
│  sec_importer         │              Composite       │
│  fetcher/parser/      │              Fraud Score     │
│  repository           │              + Red-Flag      │
│                       │              Detail Reports  │
│  ┌────────────────────┴──────────────────────────┐  │
│  │           SQLite Database (sec_importer)       │  │
│  │  companies │ filings │ filing_items            │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

### Technology Choices

- **SQLite** — Shared with sec_importer; no new DB needed
- **Pydantic** — Reused sec_importer models for validation
- **Python standard library** — Statistics, csv, json, datetime
- **numpy / pandas** — For numerical analysis and time-series operations
- **matplotlib** — Optional charting for capital flow visualization

---

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| SEC EDGAR rate limits slow bulk analysis | High | Reuse sec_importer's `RateLimiter`; batch analysis offline |
| Filing text parsing is imperfect | Medium | Use sec_importer's `FilingParser` which handles XBRL and text; add fallback heuristics |
| Financial data normalization across companies is hard | High | Start with a curated set of 10-K/10-Q fields; extensible schema |
| Fraud detection is inherently subjective | Medium | Composite scoring with transparent, documented weights; allow user overrides |
| Large filings consume memory | Medium | Chunk-based parsing; lazy loading of filing items |

---

## Phase 1 — MVP: Data Ingestion + Single-Company Fraud Score

**Goal**: A working pipeline that ingests SEC filings for a single company,
runs a basic fraud detection analysis, and outputs a composite fraud score
with red-flag details.

### Deliverable

- CLI command `forensic analyze <TICKER>` that:
  1. Uses `sec_importer.fetcher` to resolve ticker → CIK and fetch the latest 10-K.
  2. Uses `sec_importer.parser.FilingParser` to parse the filing into structured items.
  3. Stores parsed data in `sec_importer.repository.SECDatabase`.
  4. Runs a **basic fraud detection module** that checks for:
     - Revenue recognition anomalies (revenue vs. receivables growth mismatch)
     - Related-party transaction flags
     - Auditor change / going-concern warnings
     - Restatement / amendment history
     - Unusual segment reporting changes
  5. Computes a **composite fraud score** (0–100) from weighted red-flag indicators.
  6. Outputs a JSON report with:
     - High-level summary (fraud score, risk level, top 3 red flags)
     - Detailed red-flag entries with evidence excerpts and severity

### Dependencies

- `sec_importer.fetcher` — `resolve_ticker_to_cik`, `get_latest_filing`, `download_filing_text`
- `sec_importer.parser` — `FilingParser`, `parse_filing`
- `sec_importer.repository` — `SECDatabase`
- `sec_importer.models` — `FilingModel`, `FilingItemModel`
- `sec_importer.config` — `Config`

### File Structure (Phase 1)

```
forensic/
├── state/
│   └── master_plan.md
├── src/
│   └── forensic/
│       ├── __init__.py
│       ├── __main__.py          # CLI entry point
│       ├── cli.py               # argparse CLI (analyze command)
│       ├── ingest.py            # Data ingestion using sec_importer
│       ├── red_flags.py         # Red-flag detection rules (basic set)
│       ├── scoring.py           # Composite fraud score computation
│       └── models.py            # Forensic-specific Pydantic models
├── tests/
│   ├── __init__.py
│   ├── test_ingest.py
│   ├── test_red_flags.py
│   └── test_scoring.py
├── config.yaml
├── requirements.txt
└── README.md
```

### Success Criteria

- [ ] `forensic analyze AAPL` completes end-to-end without errors.
- [ ] Output JSON contains a `fraud_score` (0–100), `risk_level`, `summary`, and `red_flags` list.
- [ ] At least 5 distinct red-flag checks run against the filing.
- [ ] Composite score is deterministic given the same input data.
- [ ] All tests pass.

---

## Phase 2 — Multi-Company Analysis + Earnings Prediction

**Goal**: Extend the suite to analyze multiple companies, compare them, and
add an earnings prediction module based on historical filing data.

### Deliverable

- CLI command `forensic compare <TICKER1> <TICKER2> ...` that:
  1. Ingests latest 10-K and 10-Q filings for all specified tickers.
  2. Normalizes financial line items across companies (revenue, COGS, operating
     income, net income, total assets, total liabilities, cash flow from ops,
     capex, working capital).
  3. Runs the Phase 1 red-flag checks on each company.
  4. Computes a **comparative fraud score** (relative ranking).
  5. Runs an **earnings prediction module** that:
     - Extracts historical quarterly earnings data from 10-Q filings.
     - Fits a simple linear regression or moving-average model.
     - Predicts next quarter's EPS and revenue.
     - Flags prediction confidence intervals.
  6. Outputs a comparative JSON report with:
     - Per-company fraud scores and red flags.
     - Comparative ranking.
     - Earnings predictions with confidence intervals.

### Dependencies

- All Phase 1 modules.
- `numpy` / `pandas` — For regression and time-series analysis.

### File Structure (Phase 2 additions)

```
forensic/
├── src/
│   └── forensic/
│       ├── compare.py           # Multi-company comparison logic
│       ├── earnings.py          # Earnings prediction module
│       ├── normalization.py     # Financial line-item normalization
│       └── ... (Phase 1 files)
├── tests/
│   ├── test_compare.py
│   ├── test_earnings.py
│   └── test_normalization.py
```

### Success Criteria

- [ ] `forensic compare AAPL MSFT GOOGL` completes end-to-end.
- [ ] Comparative report includes per-company fraud scores and rankings.
- [ ] Earnings predictions include point estimates and confidence intervals.
- [ ] Normalization handles at least 8 standard financial line items.

---

## Phase 3 — Capital Flow Analysis + Advanced Red Flags

**Goal**: Add capital flow analysis (operating, investing, financing cash flows)
and advanced red-flag detection (Benford's Law, M-Score, Beneish indicators).

### Deliverable

- CLI command `forensic capital <TICKER>` that:
  1. Extracts cash flow statement data from 10-K/10-Q filings.
  2. Analyzes capital flows:
     - Operating vs. investing vs. financing cash flow trends.
     - Capex-to-revenue ratios.
     - Debt issuance / repayment patterns.
     - Dividend and share repurchase trends.
  3. Runs advanced red-flag checks:
     - **Benford's Law test** on numerical values in filing text.
     - **M-Score** (Dechow et al.) for earnings manipulation detection.
     - **Beneish M-Score** for earnings manipulation detection.
     - **Altman Z-Score** for bankruptcy risk.
  4. Outputs a capital flow analysis report with:
     - Cash flow trend charts (JSON-encoded data for downstream viz).
     - Advanced red-flag results with scores and interpretations.

### Dependencies

- All Phase 1–2 modules.
- `matplotlib` — Optional charting support.

### File Structure (Phase 3 additions)

```
forensic/
├── src/
│   └── forensic/
│       ├── capital_flow.py      # Capital flow analysis
│       ├── advanced_flags.py    # Benford, M-Score, Beneish, Altman
│       └── ... (Phase 1–2 files)
├── tests/
│   ├── test_capital_flow.py
│   └── test_advanced_flags.py
```

### Success Criteria

- [ ] `forensic capital AAPL` completes end-to-end.
- [ ] At least 4 advanced red-flag checks run and produce interpretable results.
- [ ] Capital flow data is extractable and comparable across periods.

---

## Phase 4 — Dashboard + Web Interface (Optional)

**Goal**: Provide a lightweight web dashboard for interactive exploration.

### Deliverable

- Flask/FastAPI-based web app that:
  1. Serves the SQLite database via REST API.
  2. Renders interactive charts (capital flows, fraud scores over time).
  3. Allows filtering by ticker, date range, and risk level.

### Dependencies

- `flask` or `fastapi` + `uvicorn`
- `plotly` or `matplotlib` for charting

### File Structure (Phase 4 additions)

```
forensic/
├── src/
│   └── forensic/
│       ├── api.py               # REST API endpoints
│       └── web/
│           ├── app.py           # Web app entry point
│           └── templates/       # HTML templates
└── ...
```

### Success Criteria

- [ ] Web app starts and serves data without errors.
- [ ] Charts render correctly in a browser.

---

## Phase 5 — Continuous Monitoring + Alerts (Optional)

**Goal**: Add scheduled monitoring of SEC filings for new red flags.

### Deliverable

- Scheduled job that:
  1. Polls SEC EDGAR for new filings of monitored tickers.
  2. Runs red-flag checks on new filings.
  3. Sends email/Slack alerts for high-severity red flags.

### Dependencies

- `schedule` or `celery` for job scheduling.
- `smtplib` / `requests` for alerting.

---

## Implementation Order (Phased)

1. **Phase 1** — MVP: Data Ingestion + Single-Company Fraud Score
2. **Phase 2** — Multi-Company Analysis + Earnings Prediction
3. **Phase 3** — Capital Flow Analysis + Advanced Red Flags
4. **Phase 4** — Dashboard + Web Interface (Optional)
5. **Phase 5** — Continuous Monitoring + Alerts (Optional)

Each phase builds on the previous one. Phases 4–5 are optional and can be
deferred based on priority.

---

## Configuration

All configuration is loaded via `sec_importer.config.Config`. The forensic
suite adds the following to the config:

```yaml
forensic:
  fraud_score_weights:
    revenue_receivables_mismatch: 0.15
    related_party_transactions: 0.10
    auditor_change: 0.10
    restatement_history: 0.15
    segment_reporting_changes: 0.05
    benfords_law_deviation: 0.10
    m_score_high: 0.10
    beneish_m_score_high: 0.10
    altman_z_low: 0.05
    cash_flow_anomaly: 0.10
  risk_levels:
    low: [0, 30]
    medium: [31, 60]
    high: [61, 85]
    critical: [86, 100]
  earnings_prediction:
    model: "linear_regression"
    confidence_level: 0.95
```

---

## Testing Strategy

- **Unit tests**: Each red-flag check, scoring function, and normalization
  function is tested in isolation with mock data.
- **Integration tests**: End-to-end pipeline tests using a small set of
  real SEC filings (cached in `tests/fixtures/`).
- **Property tests**: Fraud score determinism, red-flag count consistency.
- **Coverage target**: ≥ 80% for core modules.

---

## Open Questions

1. **Data source granularity**: Should we ingest all 10-K/10-Q filings or
   just the latest? → Phase 1: latest only. Phase 2+: historical.
2. **XBRL vs. text parsing**: sec_importer's `FilingParser` handles both.
   Should we prefer XBRL for numerical data? → Yes, where available.
3. **Fraud score calibration**: How to calibrate weights? → Start with
   expert-derived weights; allow user overrides via config.
4. **Earnings prediction model complexity**: Linear regression vs. more
   complex models? → Start simple (linear/moving average); extensible.
5. **Alerting channels**: Email vs. Slack vs. webhook? → Configurable.

---

## Summary

This master plan delivers a phased, incremental approach to building a
forensic accounting suite. Phase 1 provides immediate value with a working
single-company fraud detection pipeline. Subsequent phases add multi-company
comparison, earnings prediction, capital flow analysis, and optional web
dashboard and monitoring features. All phases leverage the existing
`sec_importer` dependency for data ingestion, parsing, and storage.
