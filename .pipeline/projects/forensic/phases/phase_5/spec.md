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
`sec_importer` dependency for 