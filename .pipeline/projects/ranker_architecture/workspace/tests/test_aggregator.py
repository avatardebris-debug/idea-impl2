"""Tests for Aggregator (Task 3)."""

import pytest
from ranker_core.signals import Signal
from ranker_core.profile import TasteProfile
from ranker_core.aggregator import Aggregator


class TestAggregatorItemScores:
    """Test item score aggregation."""

    def test_weighted_average_single_signal(self):
        agg = Aggregator()
        signals = [Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=1.0)]
        scores = agg.aggregate_item_scores(signals, "weighted_average")
        assert scores["i1"] == pytest.approx(4.0)

    def test_weighted_average_multiple_signals(self):
        agg = Aggregator()
        signals = [
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=1.0),
            Signal(user_id="u1", tool_id="t2", item_id="i1", signal_type="explicit_rating", value=5.0, weight=1.0),
        ]
        scores = agg.aggregate_item_scores(signals, "weighted_average")
        assert scores["i1"] == pytest.approx(4.5)

    def test_weighted_average_with_weights(self):
        agg = Aggregator()
        signals = [
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=2.0),
            Signal(user_id="u1", tool_id="t2", item_id="i1", signal_type="explicit_rating", value=5.0, weight=1.0),
        ]
        scores = agg.aggregate_item_scores(signals, "weighted_average")
        # (4*2 + 5*1) / (2+1) = 13/3
        assert scores["i1"] == pytest.approx(13.0 / 3.0)

    def test_count_strategy(self):
        agg = Aggregator()
        signals = [
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=1.0),
            Signal(user_id="u1", tool_id="t2", item_id="i1", signal_type="explicit_rating", value=5.0, weight=1.0),
            Signal(user_id="u1", tool_id="t3", item_id="i2", signal_type="explicit_rating", value=3.0, weight=1.0),
        ]
        scores = agg.aggregate_item_scores(signals, "count")
        assert scores["i1"] == 2
        assert scores["i2"] == 1

    def test_max_strategy(self):
        agg = Aggregator()
        signals = [
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=1.0),
            Signal(user_id="u1", tool_id="t2", item_id="i1", signal_type="explicit_rating", value=5.0, weight=1.0),
            Signal(user_id="u1", tool_id="t3", item_id="i1", signal_type="explicit_rating", value=3.0, weight=1.0),
        ]
        scores = agg.aggregate_item_scores(signals, "max")
        assert scores["i1"] == 5.0

    def test_sum_strategy(self):
        agg = Aggregator()
        signals = [
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=1.0),
            Signal(user_id="u1", tool_id="t2", item_id="i1", signal_type="explicit_rating", value=5.0, weight=1.0),
        ]
        scores = agg.aggregate_item_scores(signals, "sum")
        assert scores["i1"] == 9.0

    def test_multiple_items(self):
        agg = Aggregator()
        signals = [
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=1.0),
            Signal(user_id="u1", tool_id="t2", item_id="i2", signal_type="explicit_rating", value=5.0, weight=1.0),
            Signal(user_id="u1", tool_id="t3", item_id="i3", signal_type="explicit_rating", value=3.0, weight=1.0),
        ]
        scores = agg.aggregate_item_scores(signals, "weighted_average")
        assert len(scores) == 3
        assert scores["i1"] == 4.0
        assert scores["i2"] == 5.0
        assert scores["i3"] == 3.0

    def test_invalid_strategy_raises(self):
        agg = Aggregator()
        signals = [Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=1.0)]
        with pytest.raises(ValueError, match="Unknown aggregation strategy"):
            agg.aggregate_item_scores(signals, "invalid_strategy")


class TestAggregatorUserTaste:
    """Test user taste profile aggregation."""

    def test_aggregate_user_taste(self):
        agg = Aggregator()
        signals = [
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=1.0),
            Signal(user_id="u1", tool_id="t2", item_id="i2", signal_type="explicit_rating", value=5.0, weight=1.0),
            Signal(user_id="u2", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=3.0, weight=1.0),
        ]
        profile = agg.aggregate_user_taste(signals, "u1")
        assert profile.user_id == "u1"
        assert profile.taste_vector["i1"] == pytest.approx(4.0)
        assert profile.taste_vector["i2"] == pytest.approx(5.0)

    def test_aggregate_user_taste_empty(self):
        agg = Aggregator()
        profile = agg.aggregate_user_taste([], "u1")
        assert profile.user_id == "u1"
        assert profile.taste_vector == {}


class TestAggregatorPreferenceScore:
    """Test single item preference score computation."""

    def test_compute_preference_score(self):
        agg = Aggregator()
        signals = [
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=1.0),
            Signal(user_id="u1", tool_id="t2", item_id="i1", signal_type="explicit_rating", value=5.0, weight=1.0),
        ]
        score = agg.compute_preference_score(signals, "i1")
        assert score == pytest.approx(4.5)

    def test_compute_preference_score_missing_item(self):
        agg = Aggregator()
        signals = [
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=1.0),
        ]
        score = agg.compute_preference_score(signals, "i999")
        assert score == 0.0


class TestAggregatorTopItems:
    """Test top N items retrieval."""

    def test_get_top_items(self):
        agg = Aggregator()
        signals = [
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=1.0),
            Signal(user_id="u1", tool_id="t2", item_id="i2", signal_type="explicit_rating", value=5.0, weight=1.0),
            Signal(user_id="u1", tool_id="t3", item_id="i3", signal_type="explicit_rating", value=3.0, weight=1.0),
        ]
        top = agg.get_top_items(signals, n=2)
        assert len(top) == 2
        assert top[0] == ("i2", 5.0)
        assert top[1] == ("i1", 4.0)

    def test_get_top_items_more_than_available(self):
        agg = Aggregator()
        signals = [
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=4.0, weight=1.0),
        ]
        top = agg.get_top_items(signals, n=10)
        assert len(top) == 1

    def test_get_top_items_empty(self):
        agg = Aggregator()
        top = agg.get_top_items([], n=10)
        assert top == []


class TestAggregatorSimilarity:
    """Test taste profile similarity computation."""

    def test_cosine_similarity_identical_profiles(self):
        agg = Aggregator()
        p1 = TasteProfile(user_id="u1", taste_vector={"i1": 4.0, "i2": 6.0})
        p2 = TasteProfile(user_id="u2", taste_vector={"i1": 4.0, "i2": 6.0})
        sim = agg.compute_similarity(p1, p2, "cosine")
        assert sim == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal_profiles(self):
        agg = Aggregator()
        p1 = TasteProfile(user_id="u1", taste_vector={"i1": 4.0})
        p2 = TasteProfile(user_id="u2", taste_vector={"i2": 6.0})
        sim = agg.compute_similarity(p1, p2, "cosine")
        assert sim == pytest.approx(0.0)

    def test_cosine_similarity_no_common_items(self):
        agg = Aggregator()
        p1 = TasteProfile(user_id="u1", taste_vector={"i1": 4.0})
        p2 = TasteProfile(user_id="u2", taste_vector={"i2": 6.0})
        sim = agg.compute_similarity(p1, p2, "cosine")
        assert sim == pytest.approx(0.0)

    def test_jaccard_similarity(self):
        agg = Aggregator()
        p1 = TasteProfile(user_id="u1", taste_vector={"i1": 4.0, "i2": 6.0, "i3": 8.0})
        p2 = TasteProfile(user_id="u2", taste_vector={"i2": 5.0, "i3": 7.0, "i4": 9.0})
        sim = agg.compute_similarity(p1, p2, "jaccard")
        # Intersection: {i2, i3} = 2, Union: {i1, i2, i3, i4} = 4
        assert sim == pytest.approx(0.5)

    def test_invalid_similarity_method_raises(self):
        agg = Aggregator()
        p1 = TasteProfile(user_id="u1", taste_vector={"i1": 4.0})
        p2 = TasteProfile(user_id="u2", taste_vector={"i1": 4.0})
        with pytest.raises(ValueError, match="Unknown similarity method"):
            agg.compute_similarity(p1, p2, "invalid")


class TestAggregatorNormalizeScores:
    """Test score normalization."""

    def test_normalize_scores(self):
        agg = Aggregator()
        scores = {"i1": 4.0, "i2": 6.0, "i3": 8.0}
        normalized = agg.normalize_scores(scores)
        assert normalized["i1"] == pytest.approx(0.0)
        assert normalized["i2"] == pytest.approx(0.5)
        assert normalized["i3"] == pytest.approx(1.0)

    def test_normalize_scores_all_same(self):
        agg = Aggregator()
        scores = {"i1": 5.0, "i2": 5.0}
        normalized = agg.normalize_scores(scores)
        assert normalized["i1"] == pytest.approx(0.5)
        assert normalized["i2"] == pytest.approx(0.5)

    def test_normalize_scores_empty(self):
        agg = Aggregator()
        normalized = agg.normalize_scores({})
        assert normalized == {}
