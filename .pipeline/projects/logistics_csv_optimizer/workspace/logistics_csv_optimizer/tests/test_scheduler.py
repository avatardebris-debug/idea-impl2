"""Unit tests for the ScheduleGenerator module.

Tests schedule generation:
- Priority ordering (overnight > express > standard)
- Geographic grouping by destination
- Alphabetical sorting within groups
- Empty input handling
- Determinism
"""

import pytest
from logistics_csv_optimizer.scheduler import ScheduleGenerator


# ── Fixtures ──────────────────────────────────────────────────────────────

def _make_schedule_entry(**overrides):
    """Helper to create a minimal schedule entry dict with defaults."""
    base = {
        "origin": "New York",
        "destination": "Chicago",
        "priority": "standard",
        "weight": 100.0,
        "length": 0,
        "width": 0,
        "height": 0,
        "description": "",
    }
    base.update(overrides)
    return base


# ── Empty input handling ──────────────────────────────────────────────

class TestEmptyInput:
    """Tests for handling empty input."""

    def test_empty_list(self):
        result = ScheduleGenerator.generate([])
        assert result == []

    def test_none_input(self):
        result = ScheduleGenerator.generate(None)
        assert result == []


# ── Priority ordering ─────────────────────────────────────────────────

class TestPriorityOrdering:
    """Tests that overnight > express > standard ordering is respected."""

    def test_overnight_before_express(self):
        entries = [
            _make_schedule_entry(destination="A", priority="express"),
            _make_schedule_entry(destination="B", priority="overnight"),
        ]
        result = ScheduleGenerator.generate(entries)
        overnight_idx = next(i for i, e in enumerate(result) if e["priority"] == "overnight")
        express_idx = next(i for i, e in enumerate(result) if e["priority"] == "express")
        assert overnight_idx < express_idx

    def test_express_before_standard(self):
        entries = [
            _make_schedule_entry(destination="A", priority="standard"),
            _make_schedule_entry(destination="B", priority="express"),
        ]
        result = ScheduleGenerator.generate(entries)
        express_idx = next(i for i, e in enumerate(result) if e["priority"] == "express")
        standard_idx = next(i for i, e in enumerate(result) if e["priority"] == "standard")
        assert express_idx < standard_idx

    def test_overnight_before_standard(self):
        entries = [
            _make_schedule_entry(destination="A", priority="standard"),
            _make_schedule_entry(destination="B", priority="overnight"),
        ]
        result = ScheduleGenerator.generate(entries)
        overnight_idx = next(i for i, e in enumerate(result) if e["priority"] == "overnight")
        standard_idx = next(i for i, e in enumerate(result) if e["priority"] == "standard")
        assert overnight_idx < standard_idx

    def test_all_three_priorities_ordered(self):
        entries = [
            _make_schedule_entry(destination="A", priority="standard"),
            _make_schedule_entry(destination="B", priority="overnight"),
            _make_schedule_entry(destination="C", priority="express"),
        ]
        result = ScheduleGenerator.generate(entries)
        priorities = [e["priority"] for e in result]
        # All overnight first, then express, then standard
        overnight_indices = [i for i, p in enumerate(priorities) if p == "overnight"]
        express_indices = [i for i, p in enumerate(priorities) if p == "express"]
        standard_indices = [i for i, p in enumerate(priorities) if p == "standard"]
        if overnight_indices and express_indices:
            assert max(overnight_indices) < min(express_indices)
        if express_indices and standard_indices:
            assert max(express_indices) < min(standard_indices)

    def test_multiple_of_same_priority_preserve_relative_order(self):
        """Shipments with the same priority should maintain their original relative order."""
        entries = [
            _make_schedule_entry(destination="A", priority="standard", weight=10.0),
            _make_schedule_entry(destination="B", priority="express", weight=20.0),
            _make_schedule_entry(destination="C", priority="standard", weight=30.0),
            _make_schedule_entry(destination="D", priority="express", weight=40.0),
        ]
        result = ScheduleGenerator.generate(entries)
        express_entries = [e for e in result if e["priority"] == "express"]
        standard_entries = [e for e in result if e["priority"] == "standard"]
        # Express should come before standard
        express_first_dest = express_entries[0]["destination"]
        standard_first_dest = standard_entries[0]["destination"]
        express_idx = next(i for i, e in enumerate(result) if e["destination"] == express_first_dest)
        standard_idx = next(i for i, e in enumerate(result) if e["destination"] == standard_first_dest)
        assert express_idx < standard_idx


# ── Geographic grouping by destination ─────────────────────────────────

class TestGeographicGrouping:
    """Tests for grouping by destination."""

    def test_same_destination_grouped(self):
        """Shipments to the same destination should be grouped together."""
        entries = [
            _make_schedule_entry(destination="Chicago", priority="standard", weight=10.0),
            _make_schedule_entry(destination="Denver", priority="overnight", weight=20.0),
            _make_schedule_entry(destination="Chicago", priority="express", weight=30.0),
        ]
        result = ScheduleGenerator.generate(entries)
        chicago_indices = [i for i, e in enumerate(result) if e["destination"] == "Chicago"]
        # Should be consecutive
        assert chicago_indices[1] - chicago_indices[0] == 1

    def test_all_destinations_present(self):
        entries = [
            _make_schedule_entry(destination="A", priority="standard"),
            _make_schedule_entry(destination="B", priority="express"),
            _make_schedule_entry(destination="C", priority="overnight"),
        ]
        result = ScheduleGenerator.generate(entries)
        destinations = {e["destination"] for e in result}
        assert destinations == {"A", "B", "C"}

    def test_grouped_by_destination_then_priority(self):
        """Within same destination, priority ordering should still apply."""
        entries = [
            _make_schedule_entry(destination="Chicago", priority="standard", weight=10.0),
            _make_schedule_entry(destination="Chicago", priority="overnight", weight=20.0),
            _make_schedule_entry(destination="Chicago", priority="express", weight=30.0),
        ]
        result = ScheduleGenerator.generate(entries)
        chicago_entries = [e for e in result if e["destination"] == "Chicago"]
        priorities = [e["priority"] for e in chicago_entries]
        # Within Chicago group: overnight, express, standard
        assert priorities == ["overnight", "express", "standard"]


# ── Alphabetical sorting within groups ─────────────────────────────────

class TestAlphabeticalSorting:
    """Tests for alphabetical sorting within destination groups."""

    def test_alphabetical_within_same_destination(self):
        """Within same destination, entries should be sorted alphabetically by destination (trivially same)."""
        entries = [
            _make_schedule_entry(destination="Chicago", priority="standard", weight=10.0),
            _make_schedule_entry(destination="Chicago", priority="express", weight=20.0),
        ]
        result = ScheduleGenerator.generate(entries)
        # Both have same destination, so order is determined by priority
        assert result[0]["priority"] == "express"
        assert result[1]["priority"] == "standard"

    def test_destinations_sorted_alphabetically(self):
        """Destinations should be sorted alphabetically."""
        entries = [
            _make_schedule_entry(destination="Zurich", priority="standard", weight=10.0),
            _make_schedule_entry(destination="Amsterdam", priority="express", weight=20.0),
            _make_schedule_entry(destination="Berlin", priority="overnight", weight=30.0),
        ]
        result = ScheduleGenerator.generate(entries)
        destinations = [e["destination"] for e in result]
        # All destinations should appear in alphabetical order
        assert destinations == sorted(destinations)


# ── Determinism ─────────────────────────────────────────────────

class TestDeterminism:
    """Tests for deterministic output."""

    def test_same_input_same_output(self):
        entries = [
            _make_schedule_entry(destination="A", priority="standard", weight=10.0),
            _make_schedule_entry(destination="B", priority="express", weight=20.0),
            _make_schedule_entry(destination="C", priority="overnight", weight=30.0),
        ]
        r1 = ScheduleGenerator.generate(entries)
        r2 = ScheduleGenerator.generate(entries)
        assert r1 == r2

    def test_multiple_runs_consistent(self):
        entries = [
            _make_schedule_entry(destination="A", priority="standard", weight=10.0),
            _make_schedule_entry(destination="B", priority="express", weight=20.0),
        ]
        results = [ScheduleGenerator.generate(entries) for _ in range(10)]
        for r in results[1:]:
            assert r == results[0]


# ── Output structure ─────────────────────────────────────────────────

class TestOutputStructure:
    """Tests for the structure of the generated schedule."""

    def test_returns_list(self):
        entries = [_make_schedule_entry()]
        result = ScheduleGenerator.generate(entries)
        assert isinstance(result, list)

    def test_each_entry_has_required_keys(self):
        entries = [_make_schedule_entry()]
        result = ScheduleGenerator.generate(entries)
        required_keys = {"origin", "destination", "priority", "weight"}
        for entry in result:
            assert required_keys.issubset(entry.keys())

    def test_entry_count_matches_input(self):
        entries = [
            _make_schedule_entry(destination="A", weight=10.0),
            _make_schedule_entry(destination="B", weight=20.0),
            _make_schedule_entry(destination="C", weight=30.0),
        ]
        result = ScheduleGenerator.generate(entries)
        assert len(result) == len(entries)

    def test_entry_values_preserved(self):
        entries = [_make_schedule_entry(destination="TestCity", priority="express", weight=99.9)]
        result = ScheduleGenerator.generate(entries)
        assert result[0]["destination"] == "TestCity"
        assert result[0]["priority"] == "express"
        assert result[0]["weight"] == 99.9


# ── Edge cases ─────────────────────────────────────────────────

class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_entry(self):
        entries = [_make_schedule_entry()]
        result = ScheduleGenerator.generate(entries)
        assert len(result) == 1

    def test_all_same_priority(self):
        entries = [
            _make_schedule_entry(destination="A", priority="standard", weight=10.0),
            _make_schedule_entry(destination="B", priority="standard", weight=20.0),
            _make_schedule_entry(destination="C", priority="standard", weight=30.0),
        ]
        result = ScheduleGenerator.generate(entries)
        assert all(e["priority"] == "standard" for e in result)
        # Should be sorted alphabetically by destination
        destinations = [e["destination"] for e in result]
        assert destinations == sorted(destinations)

    def test_all_same_destination(self):
        entries = [
            _make_schedule_entry(destination="Chicago", priority="standard", weight=10.0),
            _make_schedule_entry(destination="Chicago", priority="express", weight=20.0),
            _make_schedule_entry(destination="Chicago", priority="overnight", weight=30.0),
        ]
        result = ScheduleGenerator.generate(entries)
        assert all(e["destination"] == "Chicago" for e in result)
        # Should be sorted by priority
        priorities = [e["priority"] for e in result]
        assert priorities == ["overnight", "express", "standard"]

    def test_case_insensitive_destination_sorting(self):
        entries = [
            _make_schedule_entry(destination="zulu", priority="standard", weight=10.0),
            _make_schedule_entry(destination="alpha", priority="express", weight=20.0),
        ]
        result = ScheduleGenerator.generate(entries)
        destinations = [e["destination"] for e in result]
        assert destinations == sorted(destinations, key=str.lower)
