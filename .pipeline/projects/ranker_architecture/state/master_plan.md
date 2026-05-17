# Ranker Architecture — Master Implementation Plan

## Idea Summary

The Ranker Architecture is a system that accumulates user preferences, weights, and rankings across tool invocations to build a persistent "taste profile." Every tool interaction produces signals (explicit rankings, implicit preferences, weight adjustments) that are aggregated into a scoring model. This model can then power personalized recommendations, adaptive UIs, and ML-driven decision support.

**Core concept:** *Preference accumulation → taste modeling → actionable intelligence.*

---

## Architecture Notes

### High-Level Design

```
┌─────────────────────────────────────────────────────┐
│                   Client / UI Layer                 │
│         (tools, dashboards, APIs)                   │
└──────────────────┬──────────────────────────────────┘
                   │  preference signals
                   ▼
┌─────────────────────────────────────────────────────┐
│               Ranker Core Engine                    │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Signal   │  │ Weight   │  │ Taste Profile    │  │
│  │ Collector│→ │  Agg.    │→ │  Store & Query   │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│       │              │                │              │
│       ▼              ▼                ▼              │
│  ┌─────────────────────────────────────────────┐    │
│  │         Scoring & Ranking Engine            │    │
│  │   (compute, rank, re-rank, recommend)       │    │
│  └─────────────────────────────────────────────┘    │
└──────────────────┬──────────────────────────────────┘
                   │  ranked results / profiles
                   ▼
┌─────────────────────────────────────────────────────┐
│              ML Integration Layer                   │
│    (export, model training hooks, API endpoints)    │
└─────────────────────────────────────────────────────┘
```

### Key Components

| Component | Responsibility |
|---|---|
| **Signal Collector** | Captures preference signals from tool runs (explicit ratings, implicit behavior, weight adjustments) |
| **Weight Aggregator** | Combines signals over time using configurable aggregation strategies (weighted average, exponential decay, etc.) |
| **Taste Profile Store** | Persistent storage of per-user/per-session taste vectors and metadata |
| **Scoring Engine** | Computes scores for items based on taste profiles; supports ranking, filtering, and re-ranking |
| **ML Integration Layer** | Exports data for ML pipelines; accepts model predictions back into the ranking loop |

### Data Model (conceptual)

```python
# A signal is a single preference observation
Signal = {
    "user_id": str,
    "tool_id": str,          # which tool produced the signal
    "item_id": str,          # what was ranked/evaluated
    "timestamp": datetime,
    "signal_type": "explicit" | "implicit",
    "value": float,          # rating or derived score
    "weight": float,         # confidence/importance of this signal
    "metadata": dict,        # contextual info (category, domain, etc.)
}

# A taste profile is an aggregate over signals
TasteProfile = {
    "user_id": str,
    "version": int,
    "domains": {             # taste per domain/category
        "domain_key": {
            "weights": dict,   # feature → weight
            "top_items": list, # most preferred items
            "signal_count": int,
            "last_updated": datetime,
        }
    },
    "global_weights": dict,  # cross-domain aggregate weights
    "created_at": datetime,
    "updated_at": datetime,
}

# A ranking result
RankingResult = {
    "query_id": str,
    "item_scores": [(item_id, score, rank)],
    "profile_version": int,
    "method": str,           # which scoring method was used
    "timestamp": datetime,
}
```

### Design Principles

1. **Tool-agnostic:** Signals come from any tool; the ranker doesn't care what produced them.
2. **Composable weights:** Users can adjust weights at multiple levels (global, domain, feature).
3. **Versioned profiles:** Taste profiles are versioned for auditability and rollback.
4. **ML-ready:** The profile store exports in formats consumable by ML pipelines (JSON, CSV, vector embeddings).
5. **Low coupling:** The ranker is a library-first design; it can be embedded in any application.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Signal sparsity — not enough data to build useful profiles | High | Start with synthetic/test data; provide default profiles; allow manual weight input |
| Profile drift — tastes change over time but model doesn't adapt | Medium | Implement exponential decay on older signals; support manual profile updates |
| Over-engineering early — building ML integration before core works | High | Phase 1 is purely rule-based; ML layer is Phase 3 |
| Storage bloat — unbounded signal accumulation | Medium | Implement signal pruning strategies; configurable retention policies |
| Cold start problem — new users have no profile | Medium | Provide sensible defaults; bootstrap from population-level aggregates |

---

## Phase 1 — Core Signal Engine (MVP)

**Goal:** Build the minimal working system that captures preference signals, aggregates them into a taste profile, and produces ranked outputs.

### Description

Implement the foundational data model and core engine:
- `Signal` and `TasteProfile` data structures
- A `SignalCollector` that accepts preference data from any tool
- A `WeightAggregator` with basic strategies (simple weighted average, recency-weighted average)
- A `TasteProfileStore` backed by JSON file storage (no database dependency)
- A `ScoringEngine` that computes scores for items given a taste profile
- A simple CLI or Python API for interaction

This phase delivers a **working ranker** that can take preference inputs from multiple tools, aggregate them, and produce ranked lists. No ML, no persistence beyond JSON, no UI.

### Deliverable

A Python package `ranker_core/` with:
- `ranker_core/signals.py` — Signal data model and validation
- `ranker_core/profile.py` — TasteProfile data model
- `ranker_core/collector.py` — SignalCollector
- `ranker_core/aggregator.py` — WeightAggregator (weighted_avg, recency_weighted, exponential_decay)
- `ranker_core/store.py` — TasteProfileStore (JSON-backed)
- `ranker_core/scorer.py` — ScoringEngine (compute_scores, rank_items, re_rank)
- `ranker_core/ranker.py` — Unified Ranker class (orchestrates all components)
- `ranker_core/cli.py` — CLI for testing (add_signal, get_profile, rank, export)
- `tests/` — Unit tests for all components
- `examples/basic_ranking.py` — Example: rank items across 3 tools with synthetic data

### Dependencies

- None (pure Python, stdlib + json)

### Success Criteria

- [ ] Can create a taste profile from scratch
- [ ] Can add signals from ≥3 different tool types
- [ ] Aggregation produces stable, deterministic results
- [ ] Scoring engine produces ranked output consistent with profile weights
- [ ] Profile can be exported to JSON and re-imported
- [ ] All unit tests pass
- [ ] CLI demo runs end-to-end without errors

---

## Phase 2 — Persistence, Domains & Adaptive Weights

**Goal:** Add domain-aware taste modeling, persistent storage, adaptive weight decay, and a plugin interface for tool integration.

### Description

Build on Phase 1 with production-quality features:
- **Domain-aware profiles:** Taste profiles organized by domain/category with cross-domain weight transfer
- **Persistent storage:** SQLite-backed TasteProfileStore with migration support
- **Adaptive weights:** Exponential decay on older signals; configurable half-life per domain
- **Signal pruning:** Configurable retention (max signals per domain, time-based expiry)
- **Plugin interface:** `RankerPlugin` base class for tools to register themselves and emit signals
- **REST API:** FastAPI-based HTTP endpoint for remote signal submission and profile queries
- **Dashboard:** Simple web dashboard (HTML/JS) showing taste profile visualization and signal history

### Deliverable

Extensions to `ranker_core/`:
- `ranker_core/domains.py` — Domain management, cross-domain weight transfer
- `ranker_core/storage.py` — SQLite storage backend with migrations
- `ranker_core/decay.py` — Exponential decay and half-life configuration
- `ranker_core/pruning.py` — Signal pruning strategies
- `ranker_core/plugins.py` — RankerPlugin base class and registration
- `ranker_core/api/` — FastAPI application (signal submission, profile queries, ranking)
- `ranker_core/dashboard/` — Static dashboard with profile visualization
- `tests/` — Integration tests, storage tests, API tests
- `examples/domain_ranking.py` — Example: multi-domain taste modeling
- `examples/plugin_integration.py` — Example: custom tool plugin

### Dependencies

- Phase 1 (ranker_core core)
- SQLite (bundled with Python)
- FastAPI + uvicorn (for API)
- Minimal JS/CSS for dashboard (no framework)

### Success Criteria

- [ ] Taste profiles persist across restarts (SQLite)
- [ ] Domain-aware profiles produce distinct rankings per domain
- [ ] Signal decay works correctly (verify with time-travel tests)
- [ ] Signal pruning respects configured limits
- [ ] At least 2 example tools can register as plugins and emit signals
- [ ] API accepts signals and returns profiles/rankings
- [ ] Dashboard displays profile weights and signal history
- [ ] Integration tests pass (≥80% coverage)

---

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
| **3 — ML Integration** | ML pipelines, hybrid scoring, collaborative filtering | ML-ready ranker with advanced features | High |

Each phase is independently shippable and builds on the previous one. Phase 1 delivers a usable ranker. Phase 2 makes it production-ready. Phase 3 unlocks ML capabilities.
