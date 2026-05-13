"""
test_hypothesis_manager.py
Tests the HypothesisManager class and its RL reward loop.

Tests:
  1. add_hypothesis creates a record with correct defaults
  2. add_hypothesis with custom ID works
  3. add_hypothesis raises on duplicate ID
  4. remove_hypothesis removes and returns True; returns False if missing
  5. score_hypothesis computes surprise and updates score
  6. score_hypothesis raises on unknown hypothesis
  7. update_weights adjusts weights based on rewards
  8. update_weights normalizes weights to sum to 1
  9. update_weights prunes low-weight hypotheses
 10. get_best_hypothesis returns lowest-score hypothesis
 11. get_all_scores / get_all_weights return correct dicts
 12. run_reward_cycle scores all and updates weights in one call
 13. get_hypothesis_configs returns configs with weights
 14. get_summary returns correct state summary
 15. Weight update is monotonic for consistently good hypothesis
 16. Multiple hypotheses: relative weights reflect relative scores
"""

import sys
import pathlib

# Add the chronovision2 source directory to the path
sys.path.insert(0, str(pathlib.Path(__file__).parent / ".pipeline" / "projects" / "chronovision2" / "workspace"))

import pytest
import numpy as np

from chronovision2.core.hypothesis_manager import HypothesisManager


class TestAddHypothesis:
    def test_add_creates_record_with_defaults(self):
        mgr = HypothesisManager()
        hid = mgr.add_hypothesis(config={"lr": 0.01})
        assert hid in mgr.hypotheses
        record = mgr.hypotheses[hid]
        assert record.weight == 1.0
        assert record.score == 0.0
        assert record.survival_count == 0
        assert record.config == {"lr": 0.01}
        assert len(record.history) == 0

    def test_add_with_custom_id(self):
        mgr = HypothesisManager()
        hid = mgr.add_hypothesis(hypothesis_id="my_hyp", config={"x": 42})
        assert hid == "my_hyp"
        assert mgr.hypotheses["my_hyp"].config == {"x": 42}

    def test_add_raises_on_duplicate(self):
        mgr = HypothesisManager()
        mgr.add_hypothesis(hypothesis_id="dup", config={})
        with pytest.raises(ValueError, match="already exists"):
            mgr.add_hypothesis(hypothesis_id="dup", config={})


class TestRemoveHypothesis:
    def test_remove_returns_true_and_deletes(self):
        mgr = HypothesisManager()
        hid = mgr.add_hypothesis(config={})
        assert mgr.remove_hypothesis(hid) is True
        assert hid not in mgr.hypotheses

    def test_remove_returns_false_if_missing(self):
        mgr = HypothesisManager()
        assert mgr.remove_hypothesis("nonexistent") is False


class TestScoreHypothesis:
    def test_score_updates_score_and_history(self):
        mgr = HypothesisManager()
        hid = mgr.add_hypothesis(config={})
        surprise = mgr.score_hypothesis(hid, {"a": 10}, {"a": 12})
        assert surprise > 0
        assert mgr.hypotheses[hid].score > 0
        assert len(mgr.hypotheses[hid].history) == 1

    def test_score_raises_on_unknown(self):
        mgr = HypothesisManager()
        with pytest.raises(ValueError, match="not found"):
            mgr.score_hypothesis("nope", {}, {})

    def test_score_with_l1_metric(self):
        mgr = HypothesisManager(surprise_metric="l1")
        hid = mgr.add_hypothesis(config={})
        surprise = mgr.score_hypothesis(hid, {"a": 0}, {"a": 5})
        # l1 distance for single field = 5, normalized = 5/1 = 5
        assert abs(surprise - 5.0) < 1e-9

    def test_score_with_l2_metric(self):
        mgr = HypothesisManager(surprise_metric="l2")
        hid = mgr.add_hypothesis(config={})
        # Only 'a' is in both dicts, so only 1 field compared
        # l2 distance = sqrt(9) = 3.0, normalized by 1 = 3.0
        surprise = mgr.score_hypothesis(hid, {"a": 0}, {"a": 3, "b": 4})
        assert abs(surprise - 3.0) < 1e-9


class TestUpdateWeights:
    def test_weights_adjusted_by_rewards(self):
        mgr = HypothesisManager(learning_rate=0.5)
        h1 = mgr.add_hypothesis(config={"name": "good"})
        h2 = mgr.add_hypothesis(config={"name": "bad"})

        # h1: low surprise -> high reward
        mgr.score_hypothesis(h1, {"a": 10}, {"a": 10})  # surprise ~ 0
        # h2: high surprise -> low reward
        mgr.score_hypothesis(h2, {"a": 0}, {"a": 100})

        weights = mgr.update_weights()
        assert weights[h1] > weights[h2]

    def test_weights_sum_to_one(self):
        mgr = HypothesisManager()
        h1 = mgr.add_hypothesis(config={})
        h2 = mgr.add_hypothesis(config={})
        mgr.score_hypothesis(h1, {"a": 10}, {"a": 10})
        mgr.score_hypothesis(h2, {"a": 0}, {"a": 100})
        weights = mgr.update_weights()
        assert abs(sum(weights.values()) - 1.0) < 1e-9

    def test_prunes_low_weight(self):
        mgr = HypothesisManager(min_weight=0.001, learning_rate=0.9)
        h1 = mgr.add_hypothesis(config={})
        h2 = mgr.add_hypothesis(config={})

        # h1 gets terrible scores repeatedly
        for _ in range(10):
            mgr.score_hypothesis(h1, {"a": 0}, {"a": 1000})
        # h2 gets good scores
        for _ in range(10):
            mgr.score_hypothesis(h2, {"a": 10}, {"a": 10})

        mgr.update_weights()
        mgr.prune()
        weights = mgr.get_all_weights()
        # h1 should be pruned
        assert h1 not in weights
        assert h2 in weights

    def test_empty_returns_empty(self):
        mgr = HypothesisManager()
        assert mgr.update_weights() == {}


class TestGetBestHypothesis:
    def test_returns_lowest_score(self):
        mgr = HypothesisManager()
        h1 = mgr.add_hypothesis(config={})
        h2 = mgr.add_hypothesis(config={})
        mgr.score_hypothesis(h1, {"a": 0}, {"a": 100})
        mgr.score_hypothesis(h2, {"a": 10}, {"a": 10})
        best = mgr.get_best_hypothesis()
        assert best == h2

    def test_returns_none_when_empty(self):
        mgr = HypothesisManager()
        assert mgr.get_best_hypothesis() is None


class TestGetAllScoresAndWeights:
    def test_get_all_scores(self):
        mgr = HypothesisManager()
        h1 = mgr.add_hypothesis(config={})
        mgr.score_hypothesis(h1, {"a": 0}, {"a": 10})
        scores = mgr.get_all_scores()
        assert h1 in scores
        assert scores[h1] > 0

    def test_get_all_weights(self):
        mgr = HypothesisManager()
        h1 = mgr.add_hypothesis(config={})
        weights = mgr.get_all_weights()
        assert h1 in weights
        assert weights[h1] > 0


class TestRunRewardCycle:
    def test_scores_all_and_updates_weights(self):
        mgr = HypothesisManager(learning_rate=0.5)
        h1 = mgr.add_hypothesis(config={})
        h2 = mgr.add_hypothesis(config={})

        predictions = {
            h1: {"a": 10},
            h2: {"a": 0},
        }
        actual = {"a": 10}

        weights = mgr.run_reward_cycle(predictions, actual)
        assert weights[h1] > weights[h2]
        assert abs(sum(weights.values()) - 1.0) < 1e-9


class TestGetHypothesisConfigs:
    def test_returns_configs_with_weights(self):
        mgr = HypothesisManager()
        h1 = mgr.add_hypothesis(config={"lr": 0.01})
        mgr.score_hypothesis(h1, {"a": 10}, {"a": 10})
        mgr.update_weights()
        configs = mgr.get_hypothesis_configs()
        assert len(configs) == 1
        assert configs[0]["hypothesis_id"] == h1
        assert "weight" in configs[0]
        assert configs[0]["lr"] == 0.01


class TestGetSummary:
    def test_summary_empty(self):
        mgr = HypothesisManager()
        s = mgr.get_summary()
        assert s["count"] == 0
        assert s["best_hypothesis"] is None

    def test_summary_with_hypotheses(self):
        mgr = HypothesisManager()
        h1 = mgr.add_hypothesis(config={})
        h2 = mgr.add_hypothesis(config={})
        mgr.score_hypothesis(h1, {"a": 10}, {"a": 10})
        mgr.score_hypothesis(h2, {"a": 0}, {"a": 100})
        s = mgr.get_summary()
        assert s["count"] == 2
        assert s["best_hypothesis"] == h1
        assert h1 in s["weights"]
        assert h2 in s["weights"]
        assert h1 in s["scores"]
        assert h2 in s["scores"]
        assert "episode_count" in s


class TestMonotonicWeight:
    def test_consistently_good_hypothesis_gains_weight(self):
        mgr = HypothesisManager(learning_rate=0.3)
        h_good = mgr.add_hypothesis(config={})
        h_bad = mgr.add_hypothesis(config={})

        # Score perfectly for good, poorly for bad, then update
        for _ in range(5):
            mgr.score_hypothesis(h_good, {"a": 10}, {"a": 10})
            mgr.score_hypothesis(h_bad, {"a": 0}, {"a": 100})
            mgr.update_weights()

        weights_after = mgr.get_all_weights()

        # Good hypothesis should have higher weight than bad
        assert weights_after[h_good] > weights_after[h_bad]
        # Good hypothesis should have gained relative to equal split
        assert weights_after[h_good] > 0.5


class TestRelativeWeights:
    def test_relative_weights_reflect_scores(self):
        mgr = HypothesisManager(learning_rate=0.5)
        h_good = mgr.add_hypothesis(config={"name": "good"})
        h_bad = mgr.add_hypothesis(config={"name": "bad"})

        # Good hypothesis: zero surprise
        mgr.score_hypothesis(h_good, {"a": 10, "b": 20}, {"a": 10, "b": 20})
        # Bad hypothesis: large surprise
        mgr.score_hypothesis(h_bad, {"a": 0, "b": 0}, {"a": 10, "b": 20})

        weights = mgr.update_weights()
        assert weights[h_good] > weights[h_bad]
        # Good should be significantly better
        assert weights[h_good] > 0.5
        assert weights[h_bad] < 0.5
