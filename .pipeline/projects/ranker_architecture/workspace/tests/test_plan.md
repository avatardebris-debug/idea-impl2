# Test Plan for Ranker Architecture

## Overview
This test plan covers the `ranker_core` package, which includes:
- `signals.py` — Signal data model and validation
- `profile.py` — TasteProfile data model
- `collector.py` — SignalCollector for accepting/storing preference signals
- `aggregator.py` — Aggregation strategies and similarity computation

## Current Test Coverage
- **87 tests** currently pass across 3 test files:
  - `test_signals_and_profile.py` — Signal and TasteProfile model tests
  - `test_collector.py` — SignalCollector tests
  - `test_aggregator.py` — Aggregator tests

## Identified Issues and Gaps

### Issue 1: `SignalCollector.add_signals()` weight mismatch bug
**Location:** `collector.py`, `add_signals()` method
**Problem:** When `add_signals()` adds signals from a batch, it passes `s.weight` to `add_signal()`, but the dedup key only checks `(user_id, tool_id, item_id, signal_type, value)` — it does NOT include `weight`. This means two signals with the same dedup key but different weights will be deduplicated, but only the first one's weight is preserved. The second signal's weight is silently lost.
**Severity:** Medium — silently drops weight information.

### Issue 2: `SignalCollector.add_signals()` timestamp mismatch bug
**Location:** `collector.py`, `add_signals()` method
**Problem:** Same as Issue 1 — the dedup key does not include `timestamp`, so two signals with the same dedup key but different timestamps will be deduplicated, but only the first one's timestamp is preserved.
**Severity:** Medium — silently drops timestamp information.

### Issue 3: `SignalCollector.add_signals()` return value inconsistency
**Location:** `collector.py`, `add_signals()` method
**Problem:** The method returns `len(self._dedup_set)` (total signals after adding), but the docstring says "Returns: Number of signals added." This is misleading — it returns the total count, not the number newly added.
**Severity:** Low — misleading API contract.

### Issue 4: `SignalCollector.add_signals()` doesn't validate input
**Location:** `collector.py`, `add_signals()` method
**Problem:** The method accepts any list of objects without validating that they are `Signal` instances. If a non-Signal object is passed, it will fail later with an unhelpful AttributeError.
**Severity:** Medium — poor error handling.

### Issue 5: `TasteProfile.update_taste_vector()` doesn't validate key/value types
**Location:** `profile.py`, `update_taste_vector()` method
**Problem:** The constructor validates `taste_vector` keys and values, but `update_taste_vector()` does not. It allows adding invalid keys/values to an existing profile.
**Severity:** Medium — inconsistent validation.

### Issue 6: `TasteProfile.update_taste_vector()` doesn't validate negative values
**Location:** `profile.py`, `update_taste_vector()` method
**Problem:** The constructor validates that taste_vector values are non-negative, but `update_taste_vector()` does not. It allows setting negative values.
**Severity:** Medium — inconsistent validation.

### Issue 7: `Aggregator.aggregate_user_taste()` doesn't validate user_id
**Location:** `aggregator.py`, `aggregate_user_taste()` method
**Problem:** If `user_id` is empty or None, it will create a TasteProfile with an invalid user_id. The TasteProfile constructor validates this, so it will raise, but the error message is about user_id validation rather than being clear about the aggregation issue.
**Severity:** Low — will raise but with confusing error.

### Issue 8: `Aggregator.compute_preference_score()` doesn't handle empty signals gracefully
**Location:** `aggregator.py`, `compute_preference_score()` method
**Problem:** If `signals` is empty, `aggregate_item_scores` returns `{}`, and `scores.get(item_id, 0.0)` returns `0.0`. This is actually correct behavior, but there's no explicit test for this case.
**Severity:** Low — works correctly but untested.

### Issue 9: `Aggregator.normalize_scores()` doesn't handle all-zero scores
**Location:** `aggregator.py`, `normalize_scores()` method
**Problem:** If all scores are 0, `min_score == max_score == 0`, so it returns `0.5` for all items. This is reasonable but should be documented/tested.
**Severity:** Low — edge case worth testing.

### Issue 10: `Aggregator.compute_similarity()` doesn't handle zero-norm vectors
**Location:** `aggregator.py`, `compute_similarity()` method
**Problem:** If a profile has an empty taste_vector or all-zero values, the norm is 0, causing division by zero. The current code checks `if norm1 == 0 or norm2 == 0: return 0.0`, which handles this correctly. But this should be explicitly tested.
**Severity:** Low — works correctly but untested.

### Issue 11: `SignalCollector.get_signals_by_tool()` doesn't filter by tool_id
**Location:** `collector.py`, `get_signals_by_tool()` method
**Problem:** The method signature takes `tool_id` but the implementation filters by `user_id` instead. This is a clear bug.
**Severity:** High — returns wrong results.

### Issue 12: `SignalCollector.get_signals_by_item()` doesn't filter by item_id
**Location:** `collector.py`, `get_signals_by_item()` method
**Problem:** The method signature takes `item_id` but the implementation filters by `user_id` instead. This is a clear bug.
**Severity:** High — returns wrong results.

### Issue 13: `SignalCollector.get_signals_by_user()` doesn't filter by user_id
**Location:** `collector.py`, `get_signals_by_user()` method
**Problem:** The method signature takes `user_id` but the implementation filters by `tool_id` instead. This is a clear bug.
**Severity:** High — returns wrong results.

### Issue 14: `TasteProfile.from_dict()` doesn't validate `user_id`
**Location:** `profile.py`, `from_dict()` method
**Problem:** If `user_id` is missing or empty in the dict, it will pass through to the constructor which validates it. But the error message is about user_id validation rather than being clear about the deserialization issue.
**Severity:** Low — will raise but with confusing error.

### Issue 15: `TasteProfile.from_dict()` doesn't validate `taste_vector` types
**Location:** `profile.py`, `from_dict()` method
**Problem:** If `taste_vector` in the dict has invalid keys or values, it will pass through to the constructor which validates it. But the error message is about taste_vector validation rather than being clear about the deserialization issue.
**Severity:** Low — will raise but with confusing error.

### Issue 16: `TasteProfile.to_dict()` doesn't serialize `updated_at`
**Location:** `profile.py`, `to_dict()` method
**Problem:** The `to_dict()` method only serializes `user_id`, `taste_vector`, `metadata`, and `created_at`. It does NOT serialize `updated_at`. This means a round-trip through `to_dict()` and `from_dict()` will lose the `updated_at` value.
**Severity:** Medium — data loss in serialization.

### Issue 17: `SignalCollector.add_signal()` doesn't validate signal_type
**Location:** `collector.py`, `add_signal()` method
**Problem:** The method accepts any string for `signal_type` without validating against `VALID_SIGNAL_TYPE_VALUES`. Invalid signal types will be silently accepted.
**Severity:** Medium — allows invalid signal types.

### Issue 18: `SignalCollector.add_signal()` doesn't validate value range
**Location:** `collector.py`, `add_signal()` method
**Problem:** The method accepts any numeric value for `value` without validating that it's non-negative. Negative values will be silently accepted.
**Severity:** Medium — allows invalid values.

### Issue 19: `SignalCollector.add_signal()` doesn't validate weight range
**Location:** `collector.py`, `add_signal()` method
**Problem:** The method accepts any numeric value for `weight` without validating that it's non-negative. Negative weights will be silently accepted.
**Severity:** Medium — allows invalid weights.

### Issue 20: `SignalCollector.add_signal()` doesn't validate timestamp format
**Location:** `collector.py`, `add_signal()` method
**Problem:** The method accepts any string for `timestamp` without validating that it's a valid ISO format datetime. Invalid timestamps will cause errors later.
**Severity:** Medium — allows invalid timestamps.

## Test Plan

### Priority 1: Critical Bugs (Issues 11, 12, 13)
These are clear bugs where methods filter by the wrong field.

#### Test 1: `SignalCollector.get_signals_by_user()` filters by user_id
```python
def test_get_signals_by_user_filters_by_user_id(self):
    collector = SignalCollector()
    collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
    collector.add_signal("u2", "t2", "i2", "explicit_rating", 3.0)
    u1_signals = collector.get_signals_by_user("u1")
    assert len(u1_signals) == 1
    assert u1_signals[0].user_id == "u1"
    # Verify it doesn't return signals from other users
    for s in u1_signals:
        assert s.user_id == "u1"
```

#### Test 2: `SignalCollector.get_signals_by_item()` filters by item_id
```python
def test_get_signals_by_item_filters_by_item_id(self):
    collector = SignalCollector()
    collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
    collector.add_signal("u2", "t2", "i2", "explicit_rating", 3.0)
    i1_signals = collector.get_signals_by_item("i1")
    assert len(i1_signals) == 1
    assert i1_signals[0].item_id == "i1"
    # Verify it doesn't return signals for other items
    for s in i1_signals:
        assert s.item_id == "i1"
```

#### Test 3: `SignalCollector.get_signals_by_tool()` filters by tool_id
```python
def test_get_signals_by_tool_filters_by_tool_id(self):
    collector = SignalCollector()
    collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
    collector.add_signal("u2", "t2", "i2", "explicit_rating", 3.0)
    t1_signals = collector.get_signals_by_tool("t1")
    assert len(t1_signals) == 1
    assert t1_signals[0].tool_id == "t1"
    # Verify it doesn't return signals from other tools
    for s in t1_signals:
        assert s.tool_id == "t1"
```

### Priority 2: Data Integrity Bugs (Issues 1, 2, 16)
These bugs cause silent data loss.

#### Test 4: `SignalCollector.add_signals()` preserves weight for deduplicated signals
```python
def test_add_signals_preserves_weight_for_deduped_signals(self):
    collector = SignalCollector()
    signals = [
        Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=2.0),
        Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=5.0),
    ]
    collector.add_signals(signals)
    # After dedup, only one signal should exist with the first signal's weight
    all_signals = collector.get_signals()
    assert len(all_signals) == 1
    assert all_signals[0].weight == 2.0  # First signal's weight is preserved
```

#### Test 5: `SignalCollector.add_signals()` preserves timestamp for deduplicated signals
```python
def test_add_signals_preserves_timestamp_for_deduped_signals(self):
    collector = SignalCollector()
    signals = [
        Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, timestamp="2024-01-01T00:00:00+00:00"),
        Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, timestamp="2024-06-01T00:00:00+00:00"),
    ]
    collector.add_signals(signals)
    all_signals = collector.get_signals()
    assert len(all_signals) == 1
    assert all_signals[0].timestamp.year == 2024
    assert all_signals[0].timestamp.month == 1  # First signal's timestamp is preserved
```

#### Test 6: `TasteProfile.to_dict()` serializes `updated_at`
```python
def test_to_dict_serializes_updated_at(self):
    p = TasteProfile(user_id="u1", taste_vector={"a": 1.0})
    d = p.to_dict()
    assert "updated_at" in d
    # Verify it can be deserialized back
    p2 = TasteProfile.from_dict(d)
    assert p2.updated_at is not None
    assert p2.updated_at.year == p.updated_at.year
```

### Priority 3: Validation Gaps (Issues 5, 6, 17, 18, 19, 20)
These are missing validations that should be caught early.

#### Test 7: `TasteProfile.update_taste_vector()` validates key types
```python
def test_update_taste_vector_validates_key_type(self):
    p = TasteProfile(user_id="u1")
    with pytest.raises(TasteProfileValidationError, match="taste_vector key"):
        p.update_taste_vector(123, 0.5)  # Invalid key type
```

#### Test 8: `TasteProfile.update_taste_vector()` validates value types
```python
def test_update_taste_vector_validates_value_type(self):
    p = TasteProfile(user_id="u1")
    with pytest.raises(TasteProfileValidationError, match="taste_vector value"):
        p.update_taste_vector("item", "not_numeric")  # Invalid value type
```

#### Test 9: `TasteProfile.update_taste_vector()` validates non-negative values
```python
def test_update_taste_vector_validates_non_negative_value(self):
    p = TasteProfile(user_id="u1")
    with pytest.raises(TasteProfileValidationError, match="non-negative"):
        p.update_taste_vector("item", -0.5)  # Negative value
```

#### Test 10: `SignalCollector.add_signal()` validates signal_type
```python
def test_add_signal_validates_signal_type(self):
    collector = SignalCollector()
    with pytest.raises(ValueError, match="Invalid signal_type"):
        collector.add_signal("u1", "t1", "i1", "invalid_type", 4.0)
```

#### Test 11: `SignalCollector.add_signal()` validates non-negative value
```python
def test_add_signal_validates_non_negative_value(self):
    collector = SignalCollector()
    with pytest.raises(ValueError, match="non-negative"):
        collector.add_signal("u1", "t1", "i1", "explicit_rating", -1.0)
```

#### Test 12: `SignalCollector.add_signal()` validates non-negative weight
```python
def test_add_signal_validates_non_negative_weight(self):
    collector = SignalCollector()
    with pytest.raises(ValueError, match="non-negative"):
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0, weight=-1.0)
```

#### Test 13: `SignalCollector.add_signal()` validates timestamp format
```python
def test_add_signal_validates_timestamp_format(self):
    collector = SignalCollector()
    with pytest.raises(ValueError, match="Invalid timestamp"):
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0, timestamp="not_a_date")
```

### Priority 4: Edge Cases and Robustness (Issues 9, 10, 11, 12, 13, 14, 15)
These are edge cases that should be handled gracefully.

#### Test 14: `Aggregator.normalize_scores()` handles all-zero scores
```python
def test_normalize_scores_all_zero(self):
    agg = Aggregator()
    scores = {"i1": 0.0, "i2": 0.0}
    normalized = agg.normalize_scores(scores)
    assert normalized["i1"] == pytest.approx(0.5)
    assert normalized["i2"] == pytest.approx(0.5)
```

#### Test 15: `Aggregator.compute_similarity()` handles zero-norm vectors
```python
def test_compute_similarity_zero_norm_profiles(self):
    agg = Aggregator()
    p1 = TasteProfile(user_id="u1", taste_vector={})
    p2 = TasteProfile(user_id="u2", taste_vector={"i1": 0.0})
    sim = agg.compute_similarity(p1, p2, "cosine")
    assert sim == pytest.approx(0.0)
```

#### Test 16: `SignalCollector.add_signals()` validates input types
```python
def test_add_signals_validates_input_type(self):
    collector = SignalCollector()
    with pytest.raises(TypeError, match="Signal"):
        collector.add_signals(["not a signal"])
```

#### Test 17: `TasteProfile.from_dict()` handles missing user_id
```python
def test_from_dict_missing_user_id(self):
    data = {"taste_vector": {"a": 1.0}, "metadata": {}, "created_at": "2024-01-01T00:00:00+00:00"}
    with pytest.raises(TasteProfileValidationError, match="user_id"):
        TasteProfile.from_dict(data)
```

#### Test 18: `TasteProfile.from_dict()` handles invalid taste_vector
```python
def test_from_dict_invalid_taste_vector(self):
    data = {"user_id": "u1", "taste_vector": "not_a_dict", "metadata": {}, "created_at": "2024-01-01T00:00:00+00:00"}
    with pytest.raises(TasteProfileValidationError, match="taste_vector"):
        TasteProfile.from_dict(data)
```

#### Test 19: `Aggregator.aggregate_user_taste()` handles empty user_id
```python
def test_aggregate_user_taste_empty_user_id(self):
    agg = Aggregator()
    with pytest.raises(TasteProfileValidationError, match="user_id"):
        agg.aggregate_user_taste([], "")
```

#### Test 20: `Aggregator.compute_preference_score()` handles empty signals
```python
def test_compute_preference_score_empty_signals(self):
    agg = Aggregator()
    score = agg.compute_preference_score([], "i1")
    assert score == 0.0
```

## Summary
This test plan covers **20 tests** that address:
- **3 critical bugs** in SignalCollector filter methods (Issues 11, 12, 13)
- **3 data integrity bugs** causing silent data loss (Issues 1, 2, 16)
- **6 validation gaps** that should catch errors early (Issues 5, 6, 17, 18, 19, 20)
- **8 edge cases** for robustness (Issues 9, 10, 14, 15, 16, 17, 18, 19)

These tests will ensure the codebase is robust, consistent, and free of silent data loss bugs.
