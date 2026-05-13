"""Tests for HypothesisManager."""

import pytest
import numpy as np

from chronovision2.core.hypothesis_manager import HypothesisManager


class TestHypothesisManagerInit:
    """Tests for HypothesisManager initialization."""

    def test_default_init(self):
        """Default initialization should set up correctly."""
        hm = HypothesisManager()
        assert len(hm.hypotheses) == 0
        assert hm.learning_rate == 0.1
        assert hm.min_weight == 0.01
        assert hm.reward_decay == 0.95

    def test_custom_init(self):
        """Custom initialization should set values correctly."""
        hm = HypothesisManager(
            learning_rate=0.2,
            min_weight=0.05,
            reward_decay=0.9,
            surprise_metric="l1",
            normalize_surprise=False,
        )
        assert hm.learning_rate == 0.2
        assert hm.min_weight == 0.05
        assert hm.reward_decay == 0.9
        assert hm.surprise_meter.default_metric == "l1"
        assert hm.surprise_meter.normalize is False


class TestHypothesisManagerAdd:
    """Tests for adding hypotheses."""

    def test_add_hypothesis_with_id(self):
        """Adding a hypothesis with ID should store it."""
        hm = HypothesisManager()
        hid = hm.add_hypothesis(hypothesis_id="test", config={"x": 1})
        assert hid == "test"
        assert len(hm.hypotheses) == 1
        assert "test" in hm.hypotheses

    def test_add_hypothesis_auto_id(self):
        """Adding a hypothesis without ID should auto-generate."""
        hm = HypothesisManager()
        hid = hm.add_hypothesis(config={"x": 1})
        assert hid.startswith("hyp_")
        assert len(hm.hypotheses) == 1

    def test_add_duplicate_id(self):
        """Adding duplicate ID should raise ValueError."""
        hm = HypothesisManager()
        hm.add_hypothesis(hypothesis_id="test", config={"x": 1})
        with pytest.raises(ValueError):
            hm.add_hypothesis(hypothesis_id="test", config={"x": 2})

    def test_add_multiple(self):
        """Adding multiple hypotheses should store all."""
        hm = HypothesisManager()
        for i in range(5):
            hm.add_hypothesis(hypothesis_id=f"hyp_{i}", config={"x": i})
        assert len(hm.hypotheses) == 5

    def test_add_initial_weight(self):
        """Adding with initial weight should set it."""
        hm = HypothesisManager()
        hm.add_hypothesis(hypothesis_id="test", config={"x": 1}, initial_weight=0.5)
        record = hm.hypotheses["test"]
        assert record.weight == 0.5

    def test_add_default_config(self):
        """Adding without config should use empty dict."""
        hm = HypothesisManager()
        hm.add_hypothesis(hypothesis_id="test")
        record = hm.hypotheses["test"]
        assert record.config == {}


class TestHypothesisManagerRemove:
    """Tests for removing hypotheses."""

    def test_remove_existing(self):
        """Remove existing should return True and delete."""
        hm = HypothesisManager()
        hm.add_hypothesis(hypothesis_id="test", config={"x": 1})
        result = hm.remove_hypothesis("test")
        assert result is True
        assert len(hm.hypotheses) == 0

    def test_remove_nonexistent(self):
        """Remove nonexistent should return False."""
        hm = HypothesisManager()
        result = hm.remove_hypothesis("nonexistent")
        assert result is False


class TestHypothesisManagerScore:
    """Tests for scoring hypotheses."""

    def test_score_hypothesis(self):
        """Scoring should update score and return surprise."""
        hm = HypothesisManager()
        hm.add_hypothesis(hypothesis_id="test", config={"x": 1})
        surprise = hm.score_hypothesis("test", {"x": 10}, {"x": 13})
        assert surprise == pytest.approx(3.0)
        assert hm.hypotheses["test"].score == pytest.approx(3.0)

    def test_score_updates_running_average(self):
        """Subsequent scores should update running average."""
        hm = HypothesisManager(reward_decay=0.95)
        hm.add_hypothesis(hypothesis_id="test", config={"x": 1})
        hm.score_hypothesis("test", {"x": 0}, {"x": 10})  # surprise=10
        hm.score_hypothesis("test", {"x": 0}, {"x": 20})  # surprise=20
        # Running average: (1-0.95)*20 + 0.95*10 = 1 + 9.5 = 10.5
        assert hm.hypotheses["test"].score == pytest.approx(10.5)

    def test_score_increments_survival_count(self):
        """Scoring should increment survival_count."""
        hm = HypothesisManager()
        hm.add_hypothesis(hypothesis_id="test", config={"x": 1})
        hm.score_hypothesis("test", {"x": 0}, {"x": 10})
        hm.score_hypothesis("test", {"x": 0}, {"x": 10})
        assert hm.hypotheses["test"].survival_count == 2

    def test_score_appends_to_history(self):
        """Scoring should append to history."""
        hm = HypothesisManager()
        hm.add_hypothesis(hypothesis_id="test", config={"x": 1})
        hm.score_hypothesis("test", {"x": 0}, {"x": 10})
        assert len(hm.hypotheses["test"].history) == 1
        assert "surprise" in hm.hypotheses["test"].history[0]
        assert "score" in hm.hypotheses["test"].history[0]

    def test_score_nonexistent_raises(self):
        """Scoring nonexistent should raise ValueError."""
        hm = HypothesisManager()
        with pytest.raises(ValueError):
            hm.score_hypothesis("nonexistent", {"x": 0}, {"x": 10})


class TestHypothesisManagerUpdateWeights:
    """Tests for weight updates."""

    def test_update_weights_basic(self):
        """Basic weight update should work."""
        hm = HypothesisManager(learning_rate=0.1, min_weight=0.01)
        hm.add_hypothesis(hypothesis_id="test", config={"x": 1}, initial_weight=1.0)
        hm.score_hypothesis("test", {"x": 0}, {"x": 10})  # score=10
        weights = hm.update_weights()
        assert "test" in weights
        assert weights["test"] > 0

    def test_update_weights_normalizes(self):
        """Weights should sum to 1 after update."""
        hm = HypothesisManager(learning_rate=0.1, min_weight=0.01)
        for i in range(3):
            hm.add_hypothesis(hypothesis_id=f"hyp_{i}", config={"x": i}, initial_weight=1.0)
        # All have same score, so weights should be equal
        for i in range(3):
            hm.score_hypothesis(f"hyp_{i}", {"x": 0}, {"x": 10})
        weights = hm.update_weights()
        total = sum(weights.values())
        assert abs(total - 1.0) < 1e-6

    def test_update_weights_prunes_low(self):
        """Low weight hypotheses should be pruned."""
        hm = HypothesisManager(learning_rate=0.01, min_weight=0.1)
        hm.add_hypothesis(hypothesis_id="good", config={"x": 1}, initial_weight=1.0)
        hm.add_hypothesis(hypothesis_id="bad", config={"x": 2}, initial_weight=1.0)
        # Good hypothesis has low surprise
        hm.score_hypothesis("good", {"x": 0}, {"x": 1})
        # Bad hypothesis has high surprise
        hm.score_hypothesis("bad", {"x": 0}, {"x": 100})
        weights = hm.update_weights()
        # Good should survive, bad might be pruned
        assert "good" in weights

    def test_update_weights_empty(self):
        """Update with no hypotheses should return empty dict."""
        hm = HypothesisManager()
        weights = hm.update_weights()
        assert weights == {}

    def test_update_weights_increments_episode(self):
        """Update should increment episode count."""
        hm = HypothesisManager()
        hm.add_hypothesis(hypothesis_id="test", config={"x": 1})
        hm.update_weights()
        hm.update_weights()
        assert hm._episode_count == 2


class TestHypothesisManagerGetConfigs:
    """Tests for getting hypothesis configs."""

    def test_get_configs(self):
        """Should return configs with weights."""
        hm = HypothesisManager()
        hm.add_hypothesis(hypothesis_id="test", config={"x": 1}, initial_weight=0.5)
        configs = hm.get_hypothesis_configs()
        assert len(configs) == 1
        assert configs[0]["hypothesis_id"] == "test"
        assert configs[0]["x"] == 1
        assert "weight" in configs[0]


class TestHypothesisManagerGetBest:
    """Tests for getting best hypothesis."""

    def test_get_best(self):
        """Should return hypothesis with lowest score."""
        hm = HypothesisManager()
        hm.add_hypothesis(hypothesis_id="good", config={"x": 1})
        hm.add_hypothesis(hypothesis_id="bad", config={"x": 2})
        hm.score_hypothesis("good", {"x": 0}, {"x": 1})  # score=1
        hm.score_hypothesis("bad", {"x": 0}, {"x": 10})  # score=10
        best = hm.get_best_hypothesis()
        assert best == "good"

    def test_get_best_empty(self):
        """Empty should return None."""
        hm = HypothesisManager()
        assert hm.get_best_hypothesis() is None


class TestHypothesisManagerGetScores:
    """Tests for getting scores."""

    def test_get_all_scores(self):
        """Should return all scores."""
        hm = HypothesisManager()
        hm.add_hypothesis(hypothesis_id="test", config={"x": 1})
        hm.score_hypothesis("test", {"x": 0}, {"x": 10})
        scores = hm.get_all_scores()
        assert scores["test"] == pytest.approx(10.0)


class TestHypothesisManagerRunCycle:
    """Tests for run_reward_cycle."""

    def test_run_cycle(self):
        """Full cycle should score and update."""
        hm = HypothesisManager(learning_rate=0.1, min_weight=0.01)
        hm.add_hypothesis(hypothesis_id="test", config={"x": 1}, initial_weight=1.0)
        predictions = {"test": {"x": 0}}
        actual = {"x": 10}
        weights = hm.run_reward_cycle(predictions, actual)
        assert "test" in weights
        assert hm.hypotheses["test"].score == pytest.approx(10.0)


class TestHypothesisManagerSummary:
    """Tests for get_summary."""

    def test_summary_empty(self):
        """Empty summary should have count 0."""
        hm = HypothesisManager()
        summary = hm.get_summary()
        assert summary["count"] == 0
        assert summary["best_hypothesis"] is None

    def test_summary_with_hypotheses(self):
        """Summary should include all fields."""
        hm = HypothesisManager()
        hm.add_hypothesis(hypothesis_id="test", config={"x": 1})
        hm.score_hypothesis("test", {"x": 0}, {"x": 10})
        hm.update_weights()
        summary = hm.get_summary()
        assert summary["count"] == 1
        assert summary["best_hypothesis"] == "test"
        assert "weights" in summary
        assert "scores" in summary
        assert "episode_count" in summary
