## Phase 3 — ML Integration & Advanced Scoring

**Goal:** Connect the taste profile system to machine learning pipelines and add advanced scoring methods.

### Description

Add ML capabilities and sophisticated ranking:
- **ML export pipeline:** Export taste profiles and signal histories in ML-ready formats (CSV, JSONL, vector embeddings)
- **Model training hooks:** Interfaces for training custom models on taste data (scikit-learn compatible)
- **Hybrid scoring:** Combine rule-based taste profiles with ML model predictions (weighted ensemble)
- **Collaborative filtering:** Population-level taste aggregation for cold-start and recommendation
- **A/B testing framework:** Compare ranking strategies and measure preference prediction accuracy
- **Advanced decay models:** Per-feature decay rates, domain-specific decay curves
- **Profile similarity:** Compute similarity between taste profiles for clustering and recommendations
- **Monitoring:** Metrics for profile health, signal density, prediction accuracy

### Deliverable

Extensions to `ranker_core/`:
- `ranker_core/ml_export.py` — ML export pipeline (CSV, JSONL, embeddings)
- `ranker_core/ml_hooks.py` — Model training hooks (scikit-learn compatible)
- `ranker_core/hybrid_scorer.py` — Rule + ML hybrid scoring
- `ranker_core/collaborative.py` — Population-level taste aggregation
- `ranker_core/ab_test.py` — A/B testing framework for ranking strategies
- `ranker_core/decay_advanced.py` — Per-feature and domain-specific decay
- `ranker_core/similarity.py` — Taste profile similarity computation
- `ranker_core/monitoring.py` — Profile health and signal density metrics
- `examples/ml_integration.py` — Example: train a model on taste data
- `examples/collaborative_filtering.py` — Example: population-level recommendations
- `docs/` — Architecture docs, API reference, ML integration guide

### Dependencies

- Phase 2 (full ranker_core with API)
- scikit-learn (for ML hooks)
- numpy (for vector operations)
- Optional: vector database for embeddings (e.g., FAISS)

### Success Criteria

- [ ] Taste profiles export to CSV/JSONL with ≥95% data fidelity
- [ ] ML model trained on exported data produces meaningful predictions
- [ ] Hybrid scoring (rule + ML) outperforms rule-only on held-out test data
- [ ] Collaborative filtering produces recommendations for cold-start users
- [ ] A/B testing framework measures ranking strategy differences
- [ ] Profile similarity produces sensible clustering (validated on synthetic data)
- [ ] Monitoring dashboard shows signal density and profile health
- [ ] End-to-end ML pipeline demo runs without errors

---

## Summary of Phases

| Phase | Scope | Key Deliverable | Complexity |
|---|---|---|---|
| **1 — Core Signal Engine** | MVP: data model, aggregation, scoring | Working ranker with CLI | Low |
| **2 — Persistence & Domains** | Production features: SQLite, domains, API, plugins | Full ranker with API and dashboard | Medium |
| **3 — ML Integration** | ML pipelines, hybrid sco