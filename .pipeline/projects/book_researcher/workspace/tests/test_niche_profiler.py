"""Tests for the niche_profiler module."""

import pytest
from book_researcher.niche_profiler import profile_niches, _cluster_gaps_by_topic
from book_researcher.models import Gap, NicheProfile


class TestClusterGapsByTopic:
    """Tests for _cluster_gaps_by_topic."""

    def test_cluster_gaps_by_topic_groups_same_topic(self):
        """Gaps with the same topic should be clustered together."""
        gaps = [
            Gap(text="I wish it covered transfer learning", source_review="r1", topic="transfer learning"),
            Gap(text="I want more on transfer learning", source_review="r2", topic="transfer learning"),
            Gap(text="I wish it covered model deployment", source_review="r3", topic="model deployment"),
        ]
        clusters = _cluster_gaps_by_topic(gaps)
        assert len(clusters) == 2
        # Each cluster should have gaps with the same topic
        for cluster in clusters:
            topics = {g.topic for g in cluster}
            assert len(topics) == 1

    def test_cluster_gaps_by_topic_empty_input(self):
        """Empty input should return empty list."""
        clusters = _cluster_gaps_by_topic([])
        assert clusters == []

    def test_cluster_gaps_by_topic_single_gap(self):
        """Single gap should return a single cluster."""
        gaps = [Gap(text="I wish it covered X", source_review="r1", topic="X")]
        clusters = _cluster_gaps_by_topic(gaps)
        assert len(clusters) == 1
        assert len(clusters[0]) == 1


class TestProfileNiches:
    """Tests for profile_niches."""

    def test_profile_niches_returns_list(self):
        """profile_niches should return a list of NicheProfile."""
        gaps = [
            Gap(text="I wish it covered transfer learning", source_review="r1", topic="transfer learning"),
            Gap(text="I want more on transfer learning", source_review="r2", topic="transfer learning"),
            Gap(text="I wish it covered model deployment", source_review="r3", topic="model deployment"),
        ]
        result = profile_niches(gaps)
        assert isinstance(result, list)
        assert all(isinstance(n, NicheProfile) for n in result)

    def test_profile_niches_empty_input(self):
        """Empty gaps should return empty list."""
        result = profile_niches([])
        assert result == []

    def test_profile_niches_sorts_by_score(self):
        """Niches should be sorted by score descending."""
        gaps = [
            Gap(text="I wish it covered A", source_review="r1", topic="A"),
            Gap(text="I wish it covered A", source_review="r2", topic="A"),
            Gap(text="I wish it covered B", source_review="r3", topic="B"),
        ]
        result = profile_niches(gaps)
        if len(result) >= 2:
            assert result[0].score >= result[1].score

    def test_profile_niches_has_required_fields(self):
        """Each NicheProfile should have required fields."""
        gaps = [
            Gap(text="I wish it covered X", source_review="r1", topic="X"),
        ]
        result = profile_niches(gaps)
        assert len(result) > 0
        niche = result[0]
        assert hasattr(niche, "topic")
        assert hasattr(niche, "score")
        assert hasattr(niche, "gap_count")
        assert hasattr(niche, "representative_gaps")
