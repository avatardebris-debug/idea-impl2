## Phase 1 — MVP: Data Pipeline + Latency Detection + Manual Dashboard

### Description
Build the foundational data ingestion pipeline that connects to raw sports data feeds, detects broadcast latency gaps, and surfaces actionable signals on a real-time dashboard. No automated execution yet — this phase proves the latency arbitrage opportunity exists and the data pipeline is reliable.

### Deliverable
- **Working data pipeline** ingesting at least 2 raw sports data sources (e.g., SportRadar API, NFL Next Gen Stats, or equivalent venue-level APIs)
- **Latency detector** that measures and logs the delta between raw feed timestamps and broadcast timestamps
- **Real-time dashboard** (Streamlit or Grafana) showing:
  - Live data feeds with timestamps
  - Detected latency gaps (with confidence scores)
  - Historical latency statistics per sport/event
  - Simple rule-based signals (e.g., "if goal scored in raw feed, market price hasn't adjusted in X seconds")
- **Backtesting harness** that replays historical data to quantify the latency window and potential edge

### Dependencies
- API access to at least one raw sports data provider (SportRadar, StatsBomb, NFL Next Gen Stats, or similar)
- Polymarket API documentation and testnet access
- Historical market price data (Polymarket CLOB or Kalshi)

### Success Criteria
- [ ] Data pipeline processes live feeds with <100ms internal latency
- [ ] Latency gaps are detected and logged with >95% accuracy (validated against manual ground truth)
- [ ] Dashboard displays real-time signals with <1 second display lag
- [ ] Backtest on 30 days of historical data shows measurable latency windows (minimum 2 seconds of exploitable gap per event)
- [ ] At least 5 live sports events processed end-to-end without data loss

#