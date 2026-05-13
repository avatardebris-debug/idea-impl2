# Test Plan: Player Attribute Library

## 1. Overview

This test plan covers the **Player Attribute Library** — a Python library for creating, managing, and matching football (soccer) player attribute profiles. The library provides:

- **Data model** (`models.py`): `PlayerAttribute` dataclass with 6 attributes (speed, shooting, passing, defending, physical, mental), each clamped to 0–100.
- **Core functions** (`core.py`): `create_player`, `get_attribute`, `get_all_attributes`, `euclidean_distance`, `cosine_similarity`, `match_players`, `save_players`, `load_players`.
- **Demo** (`demo.py`): Interactive demonstration with sample players (Messi, Ronaldo, Neymar, Kante).

### Testing Framework
- **pytest** (with `pytest-cov` for coverage)
- **Python 3.10+**

---

## 2. Test Categories

### 2.1 Model Tests (`test_models.py`)
Tests for the `PlayerAttribute` dataclass and its methods.

| Test Class | Description |
|---|---|
| `TestPlayerAttributeCreation` | Default values, overrides, partial overrides |
| `TestClamping` | Negative clamping, above-max clamping, boundary values, `set()` clamping |
| `TestNameValidation` | Empty, whitespace, None names; name stripping |
| `TestGetSetAccessors` | `get()`/`set()` for all valid attributes; `KeyError` for invalid |
| `TestToDict` | Returns all 6 attributes; default values |
| `TestFromDict` | Round-trip preservation, partial data, clamping |
| `TestRepr` | Format correctness, default values |

### 2.2 Core Tests (`test_core.py`)
Tests for all core library functions.

| Test Class | Description |
|---|---|
| `TestCreatePlayer` | Name-only, overrides, return type |
| `TestGetAttribute` | Known attribute, unknown attribute raises `KeyError` |
| `TestGetAllAttributes` | Returns all 6 attrs; correct values |
| `TestEuclideanDistance` | Identical (0), fully different (max), partial difference |
| `TestCosineSimilarity` | Identical (1.0), range check, orthogonal (0.0) |
| `TestMatchPlayers` | Sorted results, `top_n` truncation, unknown metric, euclidean metric, dict format |

### 2.3 Edge Case Tests (`test_edge_cases.py`)
Tests for boundary conditions and integration scenarios.

| Test Class | Description |
|---|---|
| `TestZeroVectorPlayers` | Cosine similarity with zero vectors; euclidean with zeros |
| `TestAllZeroPlayers` | Create all-zero player; match all-zero players |
| `TestBoundaryValues` | All max (100), all min (0), mixed boundaries |
| `TestIntegration` | Full workflow; euclidean matching; empty candidates; single candidate |
| `TestLargeScale` | Match 100 players; `top_n` > candidates |
| `TestFromDictEdgeCases` | Empty dict, extra keys, negative clamping, float values |
| `TestSetEdgeCases` | Zero, max, float, negative clamped, above-max clamped |

### 2.4 Error Handling Tests (`test_error_handling.py`)
Tests for input validation and error raising.

| Test Class | Description |
|---|---|
| `TestCreatePlayerValidation` | Empty/whitespace/None name; invalid attribute; non-numeric attribute |
| `TestPlayerAttributeValidation` | Same as above + `from_dict` validation |
| `TestGetAttributeValidation` | Non-player input raises `TypeError` |
| `TestGetAllAttributesValidation` | Non-player input raises `TypeError` |
| `TestEuclideanDistanceValidation` | Non-player inputs (both args) |
| `TestCosineSimilarityValidation` | Non-player inputs (both args) |
| `TestMatchPlayersValidation` | Non-player target; invalid metric; invalid `top_n`; non-player candidates |

---

## 3. Test Coverage Goals

| Module | Target Coverage |
|---|---|
| `models.py` | 100% |
| `core.py` | 100% |
| `demo.py` | N/A (demo code, not tested) |

---

## 4. Test Execution

### Run all tests:
```bash
cd workspace/player_attribute_library
python -m pytest tests/ -v
```

### Run with coverage:
```bash
python -m pytest tests/ -v --cov=player_attribute_library --cov-report=term-missing
```

### Run specific test classes:
```bash
python -m pytest tests/test_models.py -v
python -m pytest tests/test_core.py -v
python -m pytest tests/test_edge_cases.py -v
python -m pytest tests/test_error_handling.py -v
```

---

## 5. Test Files Summary

| File | Purpose |
|---|---|
| `tests/test_models.py` | Model layer tests (dataclass, get/set, to_dict/from_dict, repr) |
| `tests/test_core.py` | Core function tests (create, get, distance, similarity, match) |
| `tests/test_edge_cases.py` | Boundary conditions, integration, large-scale, edge cases |
| `tests/test_error_handling.py` | Input validation and error raising for all functions |

---

## 6. Key Test Scenarios

### 6.1 Clamping Behavior
- Values < 0 → clamped to 0.0
- Values > 100 → clamped to 100.0
- Values in [0, 100] → unchanged
- Applies to `__post_init__`, `set()`, `from_dict()`

### 6.2 Cosine Similarity
- Identical vectors → 1.0
- Zero vectors → 0.0
- Range: [0.0, 1.0] for non-negative attributes

### 6.3 Euclidean Distance
- Identical vectors → 0.0
- Fully different (0 vs 100 on all attrs) → ~244.95
- Inverted in `match_players`: `score = 1.0 - (dist / 245.0)`

### 6.4 match_players Output
- Returns `List[dict]` with keys `"player"` and `"score"`
- Sorted by score descending
- `top_n` truncates to top N results
- Scores rounded to 4 decimal places

### 6.5 Validation Errors
- `ValueError` for invalid names, unknown attributes, invalid metrics
- `TypeError` for non-numeric attributes, non-player inputs
- `KeyError` for unknown attribute names in `get()`/`set()`
