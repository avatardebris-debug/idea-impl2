"""Tests for core library functions."""

import pytest
from player_attribute_library.core import (
    create_player,
    get_attribute,
    get_all_attributes,
    euclidean_distance,
    cosine_similarity,
    match_players,
)
from player_attribute_library.models import PlayerAttribute


# ---------------------------------------------------------------------------
# create_player
# ---------------------------------------------------------------------------

class TestCreatePlayer:
    """Tests for create_player function."""

    def test_name_only(self):
        """create_player with name only creates zero-vector player."""
        player = create_player("Test")
        assert player.name == "Test"
        for attr in ["speed", "shooting", "passing", "defending", "physical", "mental"]:
            assert getattr(player, attr) == 0.0

    def test_with_overrides(self):
        """create_player with attribute overrides."""
        player = create_player("Test", speed=80, shooting=90)
        assert player.speed == 80.0
        assert player.shooting == 90.0

    def test_returns_player_attribute(self):
        """create_player returns a PlayerAttribute instance."""
        player = create_player("Test")
        assert isinstance(player, PlayerAttribute)


# ---------------------------------------------------------------------------
# get_attribute
# ---------------------------------------------------------------------------

class TestGetAttribute:
    """Tests for get_attribute function."""

    def test_known_attribute(self):
        """get_attribute returns correct value for known attribute."""
        player = create_player("Test", speed=80, shooting=90)
        assert get_attribute(player, "speed") == 80.0
        assert get_attribute(player, "shooting") == 90.0

    def test_unknown_attribute_raises_keyerror(self):
        """get_attribute raises KeyError for unknown attribute."""
        player = create_player("Test")
        with pytest.raises(KeyError):
            get_attribute(player, "invalid_attr")


# ---------------------------------------------------------------------------
# get_all_attributes
# ---------------------------------------------------------------------------

class TestGetAllAttributes:
    """Tests for get_all_attributes function."""

    def test_returns_all_6_attributes(self):
        """get_all_attributes returns all 6 attributes."""
        player = create_player("Test")
        attrs = get_all_attributes(player)
        assert len(attrs) == 6
        for attr in ["speed", "shooting", "passing", "defending", "physical", "mental"]:
            assert attr in attrs

    def test_returns_correct_values(self):
        """get_all_attributes returns correct values."""
        player = create_player("Test", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        attrs = get_all_attributes(player)
        assert attrs["speed"] == 80.0
        assert attrs["shooting"] == 90.0
        assert attrs["passing"] == 70.0
        assert attrs["defending"] == 60.0
        assert attrs["physical"] == 75.0
        assert attrs["mental"] == 85.0


# ---------------------------------------------------------------------------
# euclidean_distance
# ---------------------------------------------------------------------------

class TestEuclideanDistance:
    """Tests for euclidean_distance function."""

    def test_identical_players(self):
        """Euclidean distance between identical players is 0."""
        p1 = create_player("A", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        p2 = create_player("B", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        assert euclidean_distance(p1, p2) == 0.0

    def test_fully_different_players(self):
        """Euclidean distance between fully different players is max."""
        p1 = create_player("Min", speed=0, shooting=0, passing=0, defending=0, physical=0, mental=0)
        p2 = create_player("Max", speed=100, shooting=100, passing=100, defending=100, physical=100, mental=100)
        # sqrt(6 * 100^2) = 100 * sqrt(6) ≈ 244.95
        import math
        expected = math.sqrt(6) * 100
        assert abs(euclidean_distance(p1, p2) - expected) < 0.01

    def test_partial_difference(self):
        """Euclidean distance for partial difference."""
        p1 = create_player("A", speed=50, shooting=50, passing=50, defending=50, physical=50, mental=50)
        p2 = create_player("B", speed=100, shooting=50, passing=50, defending=50, physical=50, mental=50)
        assert euclidean_distance(p1, p2) == 50.0

    def test_symmetric(self):
        """Euclidean distance is symmetric."""
        p1 = create_player("A", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        p2 = create_player("B", speed=50, shooting=60, passing=40, defending=30, physical=45, mental=55)
        assert euclidean_distance(p1, p2) == euclidean_distance(p2, p1)


# ---------------------------------------------------------------------------
# cosine_similarity
# ---------------------------------------------------------------------------

class TestCosineSimilarity:
    """Tests for cosine_similarity function."""

    def test_identical_players(self):
        """Cosine similarity between identical players is 1.0."""
        p1 = create_player("A", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        p2 = create_player("B", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        assert cosine_similarity(p1, p2) == 1.0

    def test_range(self):
        """Cosine similarity is in [0, 1] for non-negative attributes."""
        p1 = create_player("A", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        p2 = create_player("B", speed=50, shooting=60, passing=40, defending=30, physical=45, mental=55)
        sim = cosine_similarity(p1, p2)
        assert 0.0 <= sim <= 1.0

    def test_zero_vector(self):
        """Cosine similarity with zero vector is 0.0."""
        p1 = create_player("Zero", speed=0, shooting=0, passing=0, defending=0, physical=0, mental=0)
        p2 = create_player("NonZero", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        assert cosine_similarity(p1, p2) == 0.0

    def test_symmetric(self):
        """Cosine similarity is symmetric."""
        p1 = create_player("A", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        p2 = create_player("B", speed=50, shooting=60, passing=40, defending=30, physical=45, mental=55)
        assert cosine_similarity(p1, p2) == pytest.approx(cosine_similarity(p2, p1))


# ---------------------------------------------------------------------------
# match_players
# ---------------------------------------------------------------------------

class TestMatchPlayers:
    """Tests for match_players function."""

    def test_sorted_by_score(self):
        """match_players returns results sorted by score descending."""
        target = create_player("Target", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        p1 = create_player("Close", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        p2 = create_player("Far", speed=50, shooting=60, passing=40, defending=30, physical=45, mental=55)
        results = match_players(target, [p1, p2], metric="cosine")
        assert results[0]["player"].name == "Close"
        assert results[1]["player"].name == "Far"

    def test_top_n_truncation(self):
        """match_players truncates to top_n results."""
        target = create_player("Target", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        p1 = create_player("A", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        p2 = create_player("B", speed=50, shooting=60, passing=40, defending=30, physical=45, mental=55)
        p3 = create_player("C", speed=30, shooting=40, passing=30, defending=20, physical=25, mental=35)
        results = match_players(target, [p1, p2, p3], metric="cosine", top_n=2)
        assert len(results) == 2

    def test_unknown_metric_raises_valueerror(self):
        """match_players raises ValueError for unknown metric."""
        target = create_player("Target")
        with pytest.raises(ValueError, match="Unknown metric"):
            match_players(target, [], metric="unknown")

    def test_euclidean_metric(self):
        """match_players works with euclidean metric."""
        target = create_player("Target", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        p1 = create_player("Close", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        p2 = create_player("Far", speed=50, shooting=60, passing=40, defending=30, physical=45, mental=55)
        results = match_players(target, [p1, p2], metric="euclidean")
        assert results[0]["player"].name == "Close"
        assert results[1]["player"].name == "Far"

    def test_dict_format(self):
        """match_players returns dict with 'player' and 'score' keys."""
        target = create_player("Target")
        p1 = create_player("A")
        results = match_players(target, [p1], metric="cosine")
        assert "player" in results[0]
        assert "score" in results[0]
        assert isinstance(results[0]["player"], PlayerAttribute)
        assert isinstance(results[0]["score"], float)

    def test_invalid_top_n_raises_valueerror(self):
        """match_players raises ValueError for invalid top_n."""
        target = create_player("Target")
        with pytest.raises(ValueError, match="top_n must be a positive integer"):
            match_players(target, [], metric="cosine", top_n=0)
        with pytest.raises(ValueError, match="top_n must be a positive integer"):
            match_players(target, [], metric="cosine", top_n=-1)
        with pytest.raises(ValueError, match="top_n must be a positive integer"):
            match_players(target, [], metric="cosine", top_n="abc")

    def test_non_player_target_raises_typeerror(self):
        """match_players raises TypeError for non-player target."""
        with pytest.raises(TypeError, match="target must be a PlayerAttribute instance"):
            match_players("not a player", [], metric="cosine")

    def test_non_player_candidate_raises_typeerror(self):
        """match_players raises TypeError for non-player candidate."""
        target = create_player("Target")
        with pytest.raises(TypeError, match="Each candidate must be a PlayerAttribute instance"):
            match_players(target, ["not a player"], metric="cosine")

    def test_empty_candidates(self):
        """match_players returns empty list for empty candidates."""
        target = create_player("Target")
        results = match_players(target, [], metric="cosine")
        assert results == []

    def test_single_candidate(self):
        """match_players works with single candidate."""
        target = create_player("Target")
        p1 = create_player("A")
        results = match_players(target, [p1], metric="cosine")
        assert len(results) == 1
        assert results[0]["player"].name == "A"
