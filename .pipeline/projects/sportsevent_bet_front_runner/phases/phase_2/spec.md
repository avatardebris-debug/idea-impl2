## Phase 2 — RL Prediction Engine + Automated Execution on One Platform

### Description
Train RL-based prediction models that ingest the raw data pipeline outputs and generate probabilistic forecasts of market-moving events. Connect automated execution to one platform (Polymarket) to capture the edge in real time.

### Deliverable
- **RL-trained prediction model** (PPO or SAC agent) that:
  - Takes state vectors (current score, time, play context, momentum indicators) as input
  - Outputs probability distributions over next market-moving events (goal, turnover, score, etc.)
  - Is trained on historical data from Phase 1's backtesting harness
  - Includes confidence calibration (Brier score tracking)
- **Automated execution engine** for Polymarket:
  - Place/adjust/cancel orders within the latency window
  - Implements Kelly criterion position sizing
  - Includes circuit breakers (max drawdown, max position size per event)
- **Live trading bot** running in production on at least one sport (e.g., NFL or NBA)
- **Performance monitoring** with real-time P&L tracking, signal accuracy, and latency metrics

### Dependencies
- Phase 1 data pipeline and latency detection working reliably
- Sufficient historical data for RL training (minimum 6 months of play-by-play + market data)
- Polymarket API keys and sufficient test capital
- GPU infrastructure for model training (or cloud GPU credits)

### Success Criteria
- [ ] RL model achieves >55% accuracy on next-event prediction (baseline: ~50% = random)
- [ ] Model confidence calibration within 5% Brier score of ground truth
- [ ] Automated execution places orders within the detected latency window (target: <200ms from signal to order submission)
- [ ] Live trading bot achieves positive expected value over minimum 100 trades
- [ ] Circuit breakers trigger correctly in stress scenarios (tested via simulation)
- [ ] System uptime >99% during live events

### Risks & Mitigations
| Risk | Mitigation |
|------|-----------|
| RL model overfits to historical patterns | Use out-of-sample validation; ensemble with rule-based fallback; continuous online learning with decay |
| Polymarket API changes or downtime | Implement retry logic with exponential backoff; maintain manual fallback workflow |
| Latency window closes as more players enter the arbitrage | Continuously monitor gap sizes; diversify to less-efficient markets (Kalshi, local exchanges) |
| Regulatory/legal concerns around automated betting | Consult legal counsel; structure as personal trading; avoid terms-of-service violations where possible |
| Model drift during live play | Implement concept drift detection; automatic model retraining pipeline; human-in-the-loop override |

---

