"""Tests for PredictionEngine."""

import pytest
import numpy as np

from chronovision2.core.prediction_engine import PredictionEngine


class TestPredictionEngineInit:
    """Tests for PredictionEngine initialization."""

    def test_default_init(self):
        """Default initialization should set up correctly."""
        pe = PredictionEngine()
        assert len(pe.hypothesis_configs) == 0
        assert pe.composite_method == "weighted_average"
        assert pe.time_horizon == 10

    def test_custom_init(self):
        """Custom initialization should set values correctly."""
        configs = [
            {"hypothesis_id": "a", "weight": 0.5},
            {"hypothesis_id": "b", "weight": 0.5},
        ]
        pe = PredictionEngine(
            hypothesis_configs=configs,
            composite_method="median",
            time_horizon=20,
        )
        assert len(pe.hypothesis_configs) == 2
        assert pe.composite_method == "median"
        assert pe.time_horizon == 20


class TestPredictionEngineAddHypothesis:
    """Tests for adding hypotheses."""

    def test_add_hypothesis(self):
        """Adding a hypothesis should store it."""
        pe = PredictionEngine()
        pe.add_hypothesis({"hypothesis_id": "test", "weight": 1.0})
        assert len(pe.hypothesis_configs) == 1
        assert pe.hypothesis_configs[0]["hypothesis_id"] == "test"

    def test_add_missing_id(self):
        """Adding without hypothesis_id should raise ValueError."""
        pe = PredictionEngine()
        with pytest.raises(ValueError):
            pe.add_hypothesis({"weight": 1.0})

    def test_add_multiple(self):
        """Adding multiple hypotheses should store all."""
        pe = PredictionEngine()
        for i in range(5):
            pe.add_hypothesis({"hypothesis_id": f"hyp_{i}", "weight": 1.0})
        assert len(pe.hypothesis_configs) == 5


class TestPredictionEngineComposite:
    """Tests for composite prediction methods."""

    def test_weighted_average(self):
        """Weighted average should compute correctly."""
        pe = PredictionEngine(composite_method="weighted_average")
        # Create mock hypothesis results
        from chronovision2.core.prediction_engine import HypothesisResult
        results = [
            HypothesisResult(
                hypothesis_id="a",
                predicted_state={"x": 10},
                trajectory=[],
                weight=0.3,
                hypothesis_config={},
            ),
            HypothesisResult(
                hypothesis_id="b",
                predicted_state={"x": 20},
                trajectory=[],
                weight=0.7,
                hypothesis_config={},
            ),
        ]
        result = pe._compute_composite(results)
        assert result["x"] == pytest.approx(17.0)  # 10*0.3 + 20*0.7

    def test_median(self):
        """Median should compute correctly."""
        pe = PredictionEngine(composite_method="median")
        from chronovision2.core.prediction_engine import HypothesisResult
        results = [
            HypothesisResult(hypothesis_id="a", predicted_state={"x": 10}, trajectory=[], weight=1.0, hypothesis_config={}),
            HypothesisResult(hypothesis_id="b", predicted_state={"x": 20}, trajectory=[], weight=1.0, hypothesis_config={}),
            HypothesisResult(hypothesis_id="c", predicted_state={"x": 30}, trajectory=[], weight=1.0, hypothesis_config={}),
        ]
        result = pe._compute_composite(results)
        assert result["x"] == pytest.approx(20.0)

    def test_median_even_count(self):
        """Median with even count should average middle two."""
        pe = PredictionEngine(composite_method="median")
        from chronovision2.core.prediction_engine import HypothesisResult
        results = [
            HypothesisResult(hypothesis_id="a", predicted_state={"x": 10}, trajectory=[], weight=1.0, hypothesis_config={}),
            HypothesisResult(hypothesis_id="b", predicted_state={"x": 20}, trajectory=[], weight=1.0, hypothesis_config={}),
        ]
        result = pe._compute_composite(results)
        assert result["x"] == pytest.approx(15.0)

    def test_max_likelihood(self):
        """Max likelihood should return highest weight prediction."""
        pe = PredictionEngine(composite_method="max_likelihood")
        from chronovision2.core.prediction_engine import HypothesisResult
        results = [
            HypothesisResult(hypothesis_id="a", predicted_state={"x": 10}, trajectory=[], weight=0.3, hypothesis_config={}),
            HypothesisResult(hypothesis_id="b", predicted_state={"x": 20}, trajectory=[], weight=0.7, hypothesis_config={}),
        ]
        result = pe._compute_composite(results)
        assert result["x"] == 20

    def test_empty_results(self):
        """Empty results should return empty dict."""
        pe = PredictionEngine()
        result = pe._compute_composite([])
        assert result == {}

    def test_unknown_method(self):
        """Unknown method should raise ValueError."""
        pe = PredictionEngine(composite_method="unknown")
        from chronovision2.core.prediction_engine import HypothesisResult
        results = [
            HypothesisResult(hypothesis_id="a", predicted_state={"x": 10}, trajectory=[], weight=1.0, hypothesis_config={}),
        ]
        with pytest.raises(ValueError):
            pe._compute_composite(results)


class TestPredictionEnginePredict:
    """Tests for predict method."""

    def test_predict_basic(self):
        """Basic predict should return PredictionResult."""
        pe = PredictionEngine()
        pe.add_hypothesis({"hypothesis_id": "test", "weight": 1.0})
        result = pe.predict({"x": 0}, num_steps=5)
        assert isinstance(result, PredictionResult)
        # Check it's a PredictionResult
        assert hasattr(result, "prediction")
        assert hasattr(result, "hypothesis_results")
        assert hasattr(result, "total_time")
        assert hasattr(result, "timestamp")

    def test_predict_uses_time_horizon(self):
        """Predict should use time_horizon when num_steps is None."""
        pe = PredictionEngine(time_horizon=15)
        pe.add_hypothesis({"hypothesis_id": "test", "weight": 1.0})
        result = pe.predict({"x": 0})
        assert len(result.hypothesis_results[0].trajectory) == 16

    def test_predict_stores_result(self):
        """Predict should store result internally."""
        pe = PredictionEngine()
        pe.add_hypothesis({"hypothesis_id": "test", "weight": 1.0})
        pe.predict({"x": 0}, num_steps=5)
        assert len(pe._results) == 1

    def test_predict_multiple_hypotheses(self):
        """Predict with multiple hypotheses should run all."""
        pe = PredictionEngine()
        pe.add_hypothesis({"hypothesis_id": "a", "weight": 1.0})
        pe.add_hypothesis({"hypothesis_id": "b", "weight": 1.0})
        result = pe.predict({"x": 0}, num_steps=5)
        assert len(result.hypothesis_results) == 2


class TestPredictionEngineBatch:
    """Tests for predict_batch method."""

    def test_predict_batch(self):
        """Batch predict should return list of results."""
        pe = PredictionEngine()
        pe.add_hypothesis({"hypothesis_id": "test", "weight": 1.0})
        states = [{"x": 0}, {"x": 10}]
        results = pe.predict_batch(states, num_steps=5)
        assert len(results) == 2
        # With no rules, state doesn't change
        assert results[0].prediction["x"] == pytest.approx(0.0)
        assert results[1].prediction["x"] == pytest.approx(10.0)


class TestPredictionEngineGetResults:
    """Tests for getting results."""

    def test_get_last_result(self):
        """Should return last result."""
        pe = PredictionEngine()
        pe.add_hypothesis({"hypothesis_id": "test", "weight": 1.0})
        pe.predict({"x": 0}, num_steps=5)
        result = pe.get_last_result()
        assert result is not None
        assert result == pe._results[-1]

    def test_get_last_result_empty(self):
        """Should return None if no results."""
        pe = PredictionEngine()
        assert pe.get_last_result() is None

    def test_get_all_results(self):
        """Should return all results."""
        pe = PredictionEngine()
        pe.add_hypothesis({"hypothesis_id": "test", "weight": 1.0})
        pe.predict({"x": 0}, num_steps=5)
        pe.predict({"x": 10}, num_steps=5)
        results = pe.get_all_results()
        assert len(results) == 2


class TestPredictionResultMethods:
    """Tests for PredictionResult helper methods."""

    def test_get_per_hypothesis(self):
        """Should get field from all hypotheses."""
        from chronovision2.core.prediction_engine import PredictionResult, HypothesisResult
        results = [
            HypothesisResult(hypothesis_id="a", predicted_state={"x": 10}, trajectory=[], weight=1.0, hypothesis_config={}),
            HypothesisResult(hypothesis_id="b", predicted_state={"x": 20}, trajectory=[], weight=1.0, hypothesis_config={}),
        ]
        pr = PredictionResult(prediction={}, hypothesis_results=results, composite_method="test", total_time=1.0)
        values = pr.get_per_hypothesis("x")
        assert values == [10, 20]

    def test_get_aggregate(self):
        """Should compute aggregate value."""
        from chronovision2.core.prediction_engine import PredictionResult, HypothesisResult
        results = [
            HypothesisResult(hypothesis_id="a", predicted_state={"x": 10}, trajectory=[], weight=1.0, hypothesis_config={}),
            HypothesisResult(hypothesis_id="b", predicted_state={"x": 20}, trajectory=[], weight=1.0, hypothesis_config={}),
        ]
        pr = PredictionResult(prediction={}, hypothesis_results=results, composite_method="test", total_time=1.0)
        value = pr.get_aggregate("x")
        assert value == pytest.approx(15.0)

    def test_get_aggregate_none_values(self):
        """Should handle None values."""
        from chronovision2.core.prediction_engine import PredictionResult, HypothesisResult
        results = [
            HypothesisResult(hypothesis_id="a", predicted_state={"x": None}, trajectory=[], weight=1.0, hypothesis_config={}),
            HypothesisResult(hypothesis_id="b", predicted_state={"x": 20}, trajectory=[], weight=1.0, hypothesis_config={}),
        ]
        pr = PredictionResult(prediction={}, hypothesis_results=results, composite_method="test", total_time=1.0)
        value = pr.get_aggregate("x")
        assert value == pytest.approx(20.0)

    def test_get_aggregate_all_none(self):
        """Should return None if all values are None."""
        from chronovision2.core.prediction_engine import PredictionResult, HypothesisResult
        results = [
            HypothesisResult(hypothesis_id="a", predicted_state={"x": None}, trajectory=[], weight=1.0, hypothesis_config={}),
            HypothesisResult(hypothesis_id="b", predicted_state={"x": None}, trajectory=[], weight=1.0, hypothesis_config={}),
        ]
        pr = PredictionResult(prediction={}, hypothesis_results=results, composite_method="test", total_time=1.0)
        value = pr.get_aggregate("x")
        assert value is None
