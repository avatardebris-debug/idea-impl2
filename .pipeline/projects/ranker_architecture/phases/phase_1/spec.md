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