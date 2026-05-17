"""Comprehensive test suite for the RL dropshipping system."""

import json
import math
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rl_dropshipping.src.shadow import ShadowPredictor, ShadowComparator, ShadowStore
from rl_dropshipping.src.shadow.predictor import Prediction
from rl_dropshipping.src.rollout import RolloutPipeline, RolloutStatus
from rl_dropshipping.src.calibration import CalibrationLayer
from rl_dropshipping.src.monitoring import (
    MonitoringDashboard,
    KillSwitch,
    MetricTracker,
    Alert,
    AlertLevel,
)
from rl_dropshipping.src.feedback import FeedbackCollector, FeedbackProcessor, FeedbackSample


class TestShadowPredictor(unittest.TestCase):
    """Test shadow predictor functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.predictor = ShadowPredictor(enabled=True)

    def test_initialization(self):
        """Test predictor initialization."""
        self.assertTrue(self.predictor.enabled)
        self.assertEqual(self.predictor.prediction_count, 0)

    def test_predict(self):
        """Test making a prediction."""
        pred = self.predictor.predict(
            action_type="product_selection",
            prediction={"product_id": 123},
            confidence=0.8,
        )
        self.assertIsInstance(pred, Prediction)
        self.assertEqual(self.predictor.prediction_count, 1)

    def test_predict_disabled(self):
        """Test prediction when disabled."""
        predictor = ShadowPredictor(enabled=False)
        pred = predictor.predict(
            action_type="product_selection",
            prediction={"product_id": 123},
            confidence=0.8,
        )
        self.assertIsInstance(pred, Prediction)
        self.assertEqual(predictor.prediction_count, 0)

    def test_get_predictions(self):
        """Test getting predictions."""
        self.predictor.predict(action_type="a", prediction={}, confidence=0.5)
        self.predictor.predict(action_type="b", prediction={}, confidence=0.6)

        predictions = self.predictor.get_predictions(action_type="a")
        self.assertEqual(len(predictions), 1)

    def test_clear(self):
        """Test clearing predictions."""
        self.predictor.predict(action_type="a", prediction={}, confidence=0.5)
        self.predictor.clear()
        self.assertEqual(self.predictor.prediction_count, 0)

    def test_confidence_clamping(self):
        """Test confidence score clamping."""
        pred = self.predictor.predict(
            action_type="a",
            prediction={},
            confidence=1.5,  # Should be clamped to 1.0
        )
        self.assertEqual(pred.confidence, 1.0)

        pred = self.predictor.predict(
            action_type="a",
            prediction={},
            confidence=-0.5,  # Should be clamped to 0.0
        )
        self.assertEqual(pred.confidence, 0.0)


class TestShadowComparator(unittest.TestCase):
    """Test shadow comparator functionality."""

    def test_initialization(self):
        """Test comparator initialization."""
        comparator = ShadowComparator()
        self.assertEqual(comparator.sample_count, 0)

    def test_record_comparison(self):
        """Test recording a comparison."""
        comparator = ShadowComparator()
        comparator.record_comparison(
            action_type="product_selection",
            rl_reward=5.0,
            baseline_reward=4.0,
        )
        self.assertEqual(comparator.sample_count, 1)

    def test_get_improvement_rate(self):
        """Test getting improvement rate."""
        comparator = ShadowComparator()
        comparator.record_comparison("a", rl_reward=5.0, baseline_reward=4.0)
        comparator.record_comparison("b", rl_reward=3.0, baseline_reward=4.0)

        rate = comparator.get_improvement_rate()
        self.assertIsInstance(rate, float)
        self.assertGreaterEqual(rate, 0.0)
        self.assertLessEqual(rate, 1.0)

    def test_get_metrics(self):
        """Test getting comparison metrics."""
        comparator = ShadowComparator()
        comparator.record_comparison("a", rl_reward=5.0, baseline_reward=4.0)

        metrics = comparator.get_metrics()
        self.assertIn("sample_count", metrics)
        self.assertIn("improvement_rate", metrics)


class TestShadowStore(unittest.TestCase):
    """Test shadow store functionality."""

    def test_initialization(self):
        """Test store initialization."""
        store = ShadowStore()
        self.assertEqual(store.sample_count, 0)

    def test_save_and_load(self):
        """Test saving and loading data."""
        store = ShadowStore()
        store.save({"key": "value"})
        loaded = store.load()
        self.assertEqual(loaded["key"], "value")

    def test_get_sample_count(self):
        """Test getting sample count."""
        store = ShadowStore()
        store.save({"key": "value"})
        self.assertEqual(store.sample_count, 1)


class TestRolloutPipeline(unittest.TestCase):
    """Test rollout pipeline functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.pipeline = RolloutPipeline(name="test_rollout")

    def test_initialization(self):
        """Test pipeline initialization."""
        self.assertEqual(self.pipeline.name, "test_rollout")
        self.assertEqual(len(self.pipeline.phases), 0)
        self.assertEqual(self.pipeline.current_phase, None)

    def test_add_phase(self):
        """Test adding phases."""
        self.pipeline.add_phase("phase_1", "Canary", traffic_fraction=0.01)
        self.assertEqual(len(self.pipeline.phases), 1)
        self.assertIn("phase_1", self.pipeline.phases)

    def test_activate_phase(self):
        """Test activating a phase."""
        self.pipeline.add_phase("phase_1", "Canary", traffic_fraction=0.01)
        self.pipeline.activate_phase("phase_1", traffic_fraction=0.01)

        phase = self.pipeline.phases["phase_1"]
        self.assertEqual(phase.status, RolloutStatus.ACTIVE)
        self.assertEqual(phase.traffic_fraction, 0.01)

    def test_complete_phase(self):
        """Test completing a phase."""
        self.pipeline.add_phase("phase_1", "Canary", traffic_fraction=0.01)
        self.pipeline.activate_phase("phase_1", traffic_fraction=0.01)
        self.pipeline.complete_phase("phase_1")

        phase = self.pipeline.phases["phase_1"]
        self.assertEqual(phase.status, RolloutStatus.COMPLETED)

    def test_rollback_phase(self):
        """Test rolling back a phase."""
        self.pipeline.add_phase("phase_1", "Canary", traffic_fraction=0.01)
        self.pipeline.activate_phase("phase_1", traffic_fraction=0.01)
        self.pipeline.rollback_phase("phase_1")

        phase = self.pipeline.phases["phase_1"]
        self.assertEqual(phase.status, RolloutStatus.ROLLED_BACK)

    def test_get_current_traffic(self):
        """Test getting current traffic fraction."""
        self.pipeline.add_phase("phase_1", "Canary", traffic_fraction=0.01)
        self.pipeline.add_phase("phase_2", "Beta", traffic_fraction=0.1)
        self.pipeline.activate_phase("phase_1", traffic_fraction=0.01)
        self.pipeline.activate_phase("phase_2", traffic_fraction=0.1)

        self.assertAlmostEqual(self.pipeline.get_current_traffic_fraction(), 0.11)

    def test_get_status(self):
        """Test getting pipeline status."""
        self.pipeline.add_phase("phase_1", "Canary", traffic_fraction=0.01)
        self.pipeline.activate_phase("phase_1", traffic_fraction=0.01)

        status = self.pipeline.get_status()
        self.assertIn("name", status)
        self.assertIn("phases", status)
        self.assertIn("current_phase", status)


class TestCalibrationLayer(unittest.TestCase):
    """Test calibration layer functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.calibrator = CalibrationLayer(calibration_window=100)

    def test_initialization(self):
        """Test calibration layer initialization."""
        self.assertEqual(self.calibrator.calibration_window, 100)
        self.assertEqual(self.calibrator.sample_count, 0)

    def test_add_sample(self):
        """Test adding samples."""
        self.calibrator.add_sample(score=0.8, label=1)
        self.assertEqual(self.calibrator.sample_count, 1)

    def test_calibrate(self):
        """Test calibration."""
        # Add samples
        for i in range(100):
            self.calibrator.add_sample(
                score=0.5 + i * 0.005,
                label=1 if i > 50 else 0,
            )

        # Calibrate
        calibrated = self.calibrator.calibrate(0.75)
        self.assertIsInstance(calibrated, float)
        self.assertGreaterEqual(calibrated, 0.0)
        self.assertLessEqual(calibrated, 1.0)

    def test_apply_temperature(self):
        """Test temperature scaling."""
        raw_score = 0.8
        scaled = self.calibrator.apply_temperature(raw_score, temperature=1.5)
        self.assertIsInstance(scaled, float)
        self.assertGreaterEqual(scaled, 0.0)
        self.assertLessEqual(scaled, 1.0)

    def test_get_calibration_stats(self):
        """Test getting calibration statistics."""
        self.calibrator.add_sample(score=0.5, label=1)
        self.calibrator.add_sample(score=0.3, label=0)

        stats = self.calibrator.get_calibration_stats()
        self.assertIn("mean_score", stats)
        self.assertIn("mean_label", stats)
        self.assertIn("sample_count", stats)
        self.assertEqual(stats["sample_count"], 2)

    def test_reset(self):
        """Test resetting calibration."""
        self.calibrator.add_sample(score=0.5, label=1)
        self.calibrator.reset()
        self.assertEqual(self.calibrator.sample_count, 0)


class TestMonitoringDashboard(unittest.TestCase):
    """Test monitoring dashboard functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.dashboard = MonitoringDashboard()

    def test_initialization(self):
        """Test dashboard initialization."""
        self.assertEqual(len(self.dashboard._trackers), 0)
        self.assertFalse(self.dashboard.kill_switch.is_active)

    def test_register_metric(self):
        """Test registering a metric."""
        tracker = self.dashboard.register_metric("test_metric")
        self.assertIn("test_metric", self.dashboard._trackers)

    def test_record_metric(self):
        """Test recording a metric."""
        self.dashboard.record_metric("test_metric", 5.0)
        tracker = self.dashboard._trackers["test_metric"]
        self.assertEqual(tracker.get_count(), 1)

    def test_set_threshold(self):
        """Test setting thresholds."""
        self.dashboard.set_threshold("test_metric", upper=10.0, lower=1.0)
        self.assertIn("test_metric", self.dashboard._thresholds)

    def test_alert_generation(self):
        """Test alert generation on threshold violation."""
        self.dashboard.set_threshold("test_metric", upper=5.0)
        self.dashboard.record_metric("test_metric", 10.0)

        alerts = self.dashboard.get_alerts(AlertLevel.CRITICAL)
        self.assertGreater(len(alerts), 0)

    def test_kill_switch_trigger(self):
        """Test kill switch triggering."""
        self.dashboard.trigger_kill_switch("Test reason")
        self.assertTrue(self.dashboard.kill_switch.is_active)

    def test_kill_switch_reset(self):
        """Test kill switch reset."""
        self.dashboard.trigger_kill_switch("Test reason")
        self.dashboard.reset_kill_switch()
        self.assertFalse(self.dashboard.kill_switch.is_active)

    def test_get_dashboard_summary(self):
        """Test getting dashboard summary."""
        self.dashboard.record_metric("test_metric", 5.0)
        summary = self.dashboard.get_dashboard_summary()
        self.assertIn("kill_switch_active", summary)
        self.assertIn("total_alerts", summary)
        self.assertIn("metrics", summary)


class TestKillSwitch(unittest.TestCase):
    """Test kill switch functionality."""

    def test_initialization(self):
        """Test kill switch initialization."""
        ks = KillSwitch()
        self.assertFalse(ks.is_active)

    def test_trigger(self):
        """Test triggering kill switch."""
        ks = KillSwitch()
        ks.trigger("Test reason")
        self.assertTrue(ks.is_active)

    def test_reset(self):
        """Test resetting kill switch."""
        ks = KillSwitch()
        ks.trigger("Test reason")
        ks.reset()
        self.assertFalse(ks.is_active)

    def test_get_status(self):
        """Test getting kill switch status."""
        ks = KillSwitch()
        ks.trigger("Test reason")
        status = ks.get_status()
        self.assertTrue(status["active"])
        self.assertEqual(status["trigger_reason"], "Test reason")


class TestMetricTracker(unittest.TestCase):
    """Test metric tracker functionality."""

    def test_record(self):
        """Test recording values."""
        tracker = MetricTracker("test", window_seconds=3600)
        tracker.record(5.0)
        self.assertEqual(tracker.get_count(), 1)

    def test_get_average(self):
        """Test getting average."""
        tracker = MetricTracker("test", window_seconds=3600)
        tracker.record(4.0)
        tracker.record(6.0)
        self.assertAlmostEqual(tracker.get_average(), 5.0)

    def test_get_max_min(self):
        """Test getting max and min."""
        tracker = MetricTracker("test", window_seconds=3600)
        tracker.record(4.0)
        tracker.record(6.0)
        tracker.record(5.0)
        self.assertEqual(tracker.get_max(), 6.0)
        self.assertEqual(tracker.get_min(), 4.0)


class TestFeedbackCollector(unittest.TestCase):
    """Test feedback collector functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.collector = FeedbackCollector(max_samples=100)

    def test_add_sample(self):
        """Test adding samples."""
        sample = self.collector.add_sample(
            state={"a": 1.0},
            action=1,
            reward=5.0,
            next_state={"a": 2.0},
            done=False,
        )
        self.assertEqual(self.collector.sample_count, 1)
        self.assertIsInstance(sample, FeedbackSample)

    def test_get_samples(self):
        """Test getting samples."""
        self.collector.add_sample(
            state={"a": 1.0},
            action=1,
            reward=5.0,
            next_state={"a": 2.0},
            done=False,
        )
        samples = self.collector.get_samples()
        self.assertEqual(len(samples), 1)

    def test_get_recent_samples(self):
        """Test getting recent samples."""
        for i in range(10):
            self.collector.add_sample(
                state={"a": float(i)},
                action=1,
                reward=float(i),
                next_state={"a": float(i + 1)},
                done=False,
            )
        recent = self.collector.get_recent_samples(5)
        self.assertEqual(len(recent), 5)

    def test_clear(self):
        """Test clearing samples."""
        self.collector.add_sample(
            state={"a": 1.0},
            action=1,
            reward=5.0,
            next_state={"a": 2.0},
            done=False,
        )
        self.collector.clear()
        self.assertEqual(self.collector.sample_count, 0)


class TestFeedbackProcessor(unittest.TestCase):
    """Test feedback processor functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = FeedbackProcessor()

    def test_compute_statistics(self):
        """Test computing statistics."""
        samples = [
            FeedbackSample(state={}, action=0, reward=5.0, next_state={}, done=False),
            FeedbackSample(state={}, action=0, reward=10.0, next_state={}, done=False),
        ]
        stats = self.processor.compute_statistics(samples)
        self.assertAlmostEqual(stats["mean_reward"], 7.5)
        self.assertEqual(stats["sample_count"], 2)

    def test_filter_outliers(self):
        """Test filtering outliers."""
        samples = [
            FeedbackSample(state={}, action=0, reward=5.0, next_state={}, done=False),
            FeedbackSample(state={}, action=0, reward=5.1, next_state={}, done=False),
            FeedbackSample(state={}, action=0, reward=100.0, next_state={}, done=False),
        ]
        filtered = self.processor.filter_outliers(samples)
        self.assertLess(len(filtered), len(samples))

    def test_prepare_training_data(self):
        """Test preparing training data."""
        samples = [
            FeedbackSample(state={"a": 1.0, "b": 2.0}, action=1, reward=5.0, next_state={}, done=False),
            FeedbackSample(state={"a": 3.0, "b": 4.0}, action=0, reward=10.0, next_state={}, done=False),
        ]
        states, actions, rewards = self.processor.prepare_training_data(samples, 2, 2)
        self.assertEqual(len(states), 2)
        self.assertEqual(len(actions), 2)
        self.assertEqual(len(rewards), 2)


class TestFeedbackSample(unittest.TestCase):
    """Test feedback sample dataclass."""

    def test_to_dict(self):
        """Test converting to dict."""
        sample = FeedbackSample(
            state={"a": 1.0},
            action=1,
            reward=5.0,
            next_state={"a": 2.0},
            done=False,
        )
        data = sample.to_dict()
        self.assertIn("state", data)
        self.assertIn("action", data)
        self.assertIn("reward", data)

    def test_from_dict(self):
        """Test creating from dict."""
        data = {
            "state": {"a": 1.0},
            "action": 1,
            "reward": 5.0,
            "next_state": {"a": 2.0},
            "done": False,
        }
        sample = FeedbackSample.from_dict(data)
        self.assertEqual(sample.action, 1)
        self.assertEqual(sample.reward, 5.0)


if __name__ == "__main__":
    unittest.main()
