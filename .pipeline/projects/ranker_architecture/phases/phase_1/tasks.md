# Phase 1 Tasks

- [x] Task 1: Implement Signal data model and validation
  - What: Create `Signal` dataclass with fields (user_id, tool_id, item_id, timestamp, signal_type, value) and validation logic. Define `TasteProfile` dataclass with fields (user_id, taste_vector, metadata, created_at, updated_at).
  - Files: `ranker_core/signals.py`, `ranker_core/profile.py`
  - Done when: Signal and TasteProfile classes exist with validation that rejects invalid signal_type values, negative/zero weights outside range, and missing required fields. Unit tests cover valid and invalid inputs.

- [ ] Task 2: Implement SignalCollector
  - What: Build `SignalCollector` class that accepts preference signals from any tool, validates them, and stores them in memory. Supports adding explicit signals (ratings) and implicit signals (behavior-derived).
  - Files: `ranker_core/collector.py`
  - Done when: Collector can add signals from ≥3 different tool types, deduplicates identical signals, and exposes a method to retrieve all stored signals. Unit tests cover add, retrieve, and edge cases.

- [ ] Task 3: Implement WeightAggregator with aggregation strategies
  - What: Build `WeightAggregator` class with three strategies: `weighted_avg` (simple weighted average), `recency_weighted` (linear recency decay), and `exponential_decay` (exponential time-based decay).
  - Files: `ranker_core/aggregator.py`
  - Done when: All three strategies produce deterministic, stable results given identical inputs. Recency and exponential strategies weight newer signals more heavily. Unit tests verify each strategy against known expected outputs.

- [ ] Task 4: Implement TasteProfileStore (JSON-backed)
  - What: Build `TasteProfileStore` class that persists taste profiles to JSON files. Supports create, read, update, delete, and list operations. Profiles are keyed by user_id.
  - Files: `ranker_core/store.py`
  - Done when: Profiles can be exported to JSON and re-imported without data loss. Unit tests cover CRUD operations, file I/O errors, and profile serialization/deserialization.

- [ ] Task 5: Implement ScoringEngine and unified Ranker class
  - What: Build `ScoringEngine` with `compute_scores`, `rank_items`, and `re_rank` methods that score items based on taste profiles. Build `Ranker` orchestrator class that ties together SignalCollector, WeightAggregator, TasteProfileStore, and ScoringEngine.
  - Files: `ranker_core/scorer.py`, `ranker_core/ranker.py`
  - Done when: ScoringEngine produces ranked output consistent with profile weights. Ranker orchestrates the full pipeline: add signals → aggregate → update profile → score → rank. Unit tests cover scoring consistency and end-to-end ranking.

- [ ] Task 6: Implement CLI, example, and integration tests
  - What: Build CLI with commands (add_signal, get_profile, rank, export). Create `examples/basic_ranking.py` demonstrating ranking items across 3 tools with synthetic data. Write integration tests.
  - Files: `ranker_core/cli.py`, `examples/basic_ranking.py`, `tests/` (unit + integration tests)
  - Done when: CLI demo runs end-to-end without errors. Example script produces ranked output from synthetic multi-tool signals. All unit and integration tests pass.