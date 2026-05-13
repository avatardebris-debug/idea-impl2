"""Tests for SurpriseMeter."""

import pytest
import numpy as np

from chronovision2.core.surprise_meter import SurpriseMeter


class TestSurpriseMeterInit:
    """Tests for SurpriseMeter initialization."""

    def test_default_init(self):
        """Default initialization should use l2 and normalize."""
        meter = SurpriseMeter()
        assert meter.default_metric == "l2"
        assert meter.normalize is True

    def test_custom_init(self):
        """Custom initialization should set values correctly."""
        meter = SurpriseMeter(default_metric="l1", normalize=False)
        assert meter.default_metric == "l1"
        assert meter.normalize is False


class TestSurpriseMeterCompute:
    """Tests for SurpriseMeter.compute."""

    def test_identical_states(self):
        """Identical states should produce zero surprise."""
        meter = SurpriseMeter()
        state = {"x": 10, "y": 20, "z": 30}
        score = meter.compute(state, state)
        assert score == 0.0

    def test_l2_distance(self):
        """L2 distance should be Euclidean distance."""
        meter = SurpriseMeter(default_metric="l2", normalize=False)
        pred = {"x": 0, "y": 0}
        actual = {"x": 3, "y": 4}
        score = meter.compute(pred, actual)
        assert score == pytest.approx(5.0)  # sqrt(9 + 16)

    def test_l1_distance(self):
        """L1 distance should be Manhattan distance."""
        meter = SurpriseMeter(default_metric="l1", normalize=False)
        pred = {"x": 0, "y": 0}
        actual = {"x": 3, "y": 4}
        score = meter.compute(pred, actual)
        assert score == pytest.approx(7.0)  # 3 + 4

    def test_normalize(self):
        """Normalized score should divide by number of fields."""
        meter = SurpriseMeter(default_metric="l2", normalize=True)
        pred = {"x": 0, "y": 0}
        actual = {"x": 3, "y": 4}
        score = meter.compute(pred, actual)
        assert score == pytest.approx(2.5)  # 5.0 / 2

    def test_empty_states(self):
        """Empty states should produce zero surprise."""
        meter = SurpriseMeter()
        score = meter.compute({}, {})
        assert score == 0.0

    def test_non_numeric_fields_ignored(self):
        """Non-numeric fields should be ignored."""
        meter = SurpriseMeter(default_metric="l2", normalize=False)
        pred = {"x": 10, "name": "test"}
        actual = {"x": 13, "name": "test"}
        score = meter.compute(pred, actual)
        assert score == pytest.approx(3.0)

    def test_mismatched_keys(self):
        """Mismatched keys should be handled gracefully."""
        meter = SurpriseMeter(default_metric="l2", normalize=False)
        pred = {"x": 10, "y": 20}
        actual = {"x": 13, "z": 30}
        score = meter.compute(pred, actual)
        # Only 'x' is common, so distance is 3
        assert score == pytest.approx(3.0)

    def test_metric_override(self):
        """Metric parameter should override default."""
        meter = SurpriseMeter(default_metric="l2", normalize=False)
        pred = {"x": 0, "y": 0}
        actual = {"x": 3, "y": 4}
        score_l2 = meter.compute(pred, actual, metric="l2")
        score_l1 = meter.compute(pred, actual, metric="l1")
        assert score_l2 == pytest.approx(5.0)
        assert score_l1 == pytest.approx(7.0)

    def test_negative_values(self):
        """Negative values should be handled correctly."""
        meter = SurpriseMeter(default_metric="l2", normalize=False)
        pred = {"x": -10}
        actual = {"x": 10}
        score = meter.compute(pred, actual)
        assert score == pytest.approx(20.0)

    def test_float_values(self):
        """Float values should be handled correctly."""
        meter = SurpriseMeter(default_metric="l2", normalize=False)
        pred = {"x": 1.5}
        actual = {"x": 2.5}
        score = meter.compute(pred, actual)
        assert score == pytest.approx(1.0)


class TestSurpriseMeterComputeBatch:
    """Tests for SurpriseMeter.compute_batch."""

    def test_batch_compute(self):
        """Batch compute should return list of scores."""
        meter = SurpriseMeter(default_metric="l2", normalize=False)
        predicted = [{"x": 0}, {"x": 10}]
        actual = [{"x": 3}, {"x": 13}]
        scores = meter.compute_batch(predicted, actual)
        assert len(scores) == 2
        assert scores[0] == pytest.approx(3.0)
        assert scores[1] == pytest.approx(3.0)

    def test_batch_mismatched_lengths(self):
        """Mismatched lengths should raise ValueError."""
        meter = SurpriseMeter()
        predicted = [{"x": 0}]
        actual = [{"x": 3}, {"x": 13}]
        with pytest.raises(ValueError):
            meter.compute_batch(predicted, actual)


class TestSurpriseMeterComputeDetailed:
    """Tests for SurpriseMeter.compute_detailed."""

    def test_detailed_output(self):
        """Detailed output should contain all required fields."""
        meter = SurpriseMeter(default_metric="l2", normalize=False)
        pred = {"x": 0, "y": 0}
        actual = {"x": 3, "y": 4}
        result = meter.compute_detailed(pred, actual)
        assert "score" in result
        assert "metric" in result
        assert "per_field_errors" in result
        assert "num_fields" in result
        assert result["score"] == pytest.approx(5.0)
        assert result["metric"] == "l2"
        assert result["per_field_errors"]["x"] == 3.0
        assert result["per_field_errors"]["y"] == 4.0
        assert result["num_fields"] == 2

    def test_detailed_with_normalize(self):
        """Detailed output with normalize should divide score."""
        meter = SurpriseMeter(default_metric="l2", normalize=True)
        pred = {"x": 0, "y": 0}
        actual = {"x": 3, "y": 4}
        result = meter.compute_detailed(pred, actual)
        assert result["score"] == pytest.approx(2.5)  # 5.0 / 2

    def test_detailed_empty(self):
        """Empty states should produce zero score."""
        meter = SurpriseMeter()
        result = meter.compute_detailed({}, {})
        assert result["score"] == 0.0
        assert result["num_fields"] == 0
