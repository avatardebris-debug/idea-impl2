## Phase 1 — Core Prediction Engine (MVP)

### Description

Build the foundational prediction engine that can ingest real-world data, create a simplified world model, generate predictions, and measure prediction accuracy. This phase focuses on a **single domain**: financial/SEC data. The MVP creates a 1-step-ahead prediction system for stock price movements and SEC filing events, using a small hypothesis pool (5-10 models).

### Deliverable

A working prediction engine with:
- **Data pipeline**: Integration with `sec_importer` to ingest SEC filings, financial statements, and market data
- **Simplified world model**: A 2D state-space representation of financial entities (companies, stocks, markets)
- **Single-domain predictor**: Predicts next-step financial state (e.g., stock price direction, filing content) for 1-5 companies
- **Surprise calculator**: Quantifies the gap between predicted and actual outcomes (mean absolute error, classification accuracy)
- **Hypothesis pool**: 5-10 diverse prediction models (linear regression, LSTM, transformer-based, graph neural network)
- **RL minimization loop**: Basic RL that updates hypothesis weights based on surprise scores
- **Dashboard**: Simple web UI showing predictions, actuals, surprise metrics, and hypothesis performance

### Dependencies

- `sec_importer` (existing): SEC data ingestion, parsing, and database storage
- `forensic` (planned): Basic forensic analysis of financial anomalies
- Python 3.10+, PyTorch, PostgreSQL, Redis
- Existing pipeline framework (`pipeline/` directory)

### Success Criteria

| Criterion | Target |
|-----------|--------|
| Data ingestion | Ingest ≥10,000 SEC filings with full parsing |
| Prediction accuracy | ≥60% directional accuracy on 1-step-ahead stock predictions (baseline: 50% random) |
| Surprise measurement | Surprise score computed for ≥95% of predictions |
| Hypothesis diversity | ≥5 distinct model architectures running in parallel |
| RL convergence | Hypothesis weight distribution converges within 50 training epochs |
| End-to-end latency | Prediction → surprise → update cycle completes in <5 minutes |
| MVP demo | Live demo showing prediction of next-day stock direction with surprise tracking |

### Tasks

- [ ] Extend `sec_importer` to support real-time streaming of new filings
- [ ] Build state-space representation of financial entities (graph-based)
- [ ] Implement 5 baseline prediction models
- [ ] Build surprise calculator with multiple metrics (MAE, classification accuracy, Brier score)
- [ ] Implement basic RL weight update loop (bandit algorithm or PPO)
- [ ] Create hypothesis pool manager (spawn, monitor, score, prune, evolve)
- [ ] Build simple web dashboard (Streamlit or FastAPI + React)
- [ ] Write integration tests and evaluation harness
- [ ] Document and demo

---