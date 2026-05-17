"""Tests for SignalCollector (Task 2)."""

import pytest
from ranker_core.signals import Signal
from ranker_core.collector import SignalCollector


class TestSignalCollectorBasic:
    """Basic SignalCollector operations."""

    def test_add_single_signal(self):
        collector = SignalCollector()
        s = collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        assert s.user_id == "u1"
        assert s.value == 4.0
        assert collector.get_signal_count() == 1

    def test_add_multiple_signals(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.add_signal("u1", "t2", "i2", "implicit_click", 0.8)
        collector.add_signal("u2", "t1", "i1", "explicit_rating", 3.0)
        assert collector.get_signal_count() == 3

    def test_add_signals_from_multiple_tools(self):
        """Collector accepts signals from >= 3 different tool types."""
        collector = SignalCollector()
        collector.add_signal("u1", "tool_click", "i1", "implicit_click", 0.9)
        collector.add_signal("u1", "tool_rating", "i2", "explicit_rating", 4.5)
        collector.add_signal("u1", "tool_purchase", "i3", "implicit_purchase", 1.0)
        collector.add_signal("u1", "tool_like", "i4", "implicit_like", 0.7)
        assert collector.get_signal_count() == 4

    def test_retrieve_all_signals(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.add_signal("u1", "t2", "i2", "implicit_click", 0.5)
        all_signals = collector.get_signals()
        assert len(all_signals) == 2

    def test_retrieve_signals_by_user(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.add_signal("u2", "t1", "i1", "explicit_rating", 3.0)
        u1_signals = collector.get_signals_by_user("u1")
        assert len(u1_signals) == 1
        assert u1_signals[0].user_id == "u1"

    def test_retrieve_signals_by_item(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.add_signal("u2", "t2", "i1", "explicit_rating", 3.0)
        i1_signals = collector.get_signals_by_item("i1")
        assert len(i1_signals) == 2

    def test_retrieve_signals_by_tool(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.add_signal("u1", "t2", "i2", "explicit_rating", 3.0)
        t1_signals = collector.get_signals_by_tool("t1")
        assert len(t1_signals) == 1
        assert t1_signals[0].tool_id == "t1"

    def test_retrieve_with_combined_filters(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.add_signal("u1", "t1", "i2", "explicit_rating", 3.0)
        collector.add_signal("u2", "t1", "i1", "explicit_rating", 2.0)
        filtered = collector.get_signals(user_id="u1", item_id="i1")
        assert len(filtered) == 1
        assert filtered[0].user_id == "u1"
        assert filtered[0].item_id == "i1"


class TestSignalCollectorDeduplication:
    """SignalCollector deduplicates identical signals."""

    def test_deduplicate_identical_signals(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        assert collector.get_signal_count() == 1

    def test_different_value_not_deduped(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 3.0)
        assert collector.get_signal_count() == 2

    def test_different_tool_not_deduped(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.add_signal("u1", "t2", "i1", "explicit_rating", 4.0)
        assert collector.get_signal_count() == 2

    def test_different_user_not_deduped(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.add_signal("u2", "t1", "i1", "explicit_rating", 4.0)
        assert collector.get_signal_count() == 2

    def test_different_type_not_deduped(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.add_signal("u1", "t1", "i1", "implicit_click", 0.5)
        assert collector.get_signal_count() == 2

    def test_add_signals_batch_deduplicates(self):
        collector = SignalCollector()
        signals = [
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0),
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0),
        ]
        count = collector.add_signals(signals)
        assert count == 1
        assert collector.get_signal_count() == 1


class TestSignalCollectorClear:
    """SignalCollector clear functionality."""

    def test_clear_removes_all_signals(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.add_signal("u2", "t2", "i2", "implicit_click", 0.5)
        collector.clear()
        assert collector.get_signal_count() == 0
        assert collector.get_signals() == []

    def test_clear_removes_dedup_set(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.clear()
        # After clear, same signal should be added again
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        assert collector.get_signal_count() == 1


class TestSignalCollectorEdgeCases:
    """Edge cases for SignalCollector."""

    def test_add_signal_with_timestamp(self):
        collector = SignalCollector()
        s = collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0, timestamp="2024-06-01T12:00:00+00:00")
        assert s.timestamp is not None
        assert s.timestamp.year == 2024
        assert s.timestamp.month == 6
        assert s.timestamp.day == 1

    def test_add_signal_with_default_timestamp(self):
        collector = SignalCollector()
        s = collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        assert s.timestamp is not None

    def test_empty_filters_return_all(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        collector.add_signal("u2", "t2", "i2", "implicit_click", 0.5)
        assert len(collector.get_signals()) == 2

    def test_no_matching_filters_returns_empty(self):
        collector = SignalCollector()
        collector.add_signal("u1", "t1", "i1", "explicit_rating", 4.0)
        result = collector.get_signals(user_id="u999")
        assert result == []
