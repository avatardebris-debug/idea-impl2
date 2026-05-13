"""Edge-case and integration tests for the player attribute library."""

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
# Zero-vector players
# ---------------------------------------------------------------------------

class TestZeroVectorPlayers:
    """Tests involving zero-vector players."""

    def test_cosine_similarity_with_zero_vectors(self):
        """cosine_similarity with zero vectors returns 0.0."""
        zero = create_player("Zero", speed=0, shooting=0, passing=0, defending=0, physical=0, mental=0)
        non_zero = create_player("NonZero", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        assert cosine_similarity(zero, non_zero) == 0.0
        assert cosine_similarity(non_zero, zero) == 0.0

    def test_cosine_similarity_both_zero(self):
        """cosine_similarity of two zero vectors returns 0.0."""
        zero1 = create_player("Zero1", speed=0, shooting=0, passing=0, defending=0, physical=0, mental=0)
        zero2 = create_player("Zero2", speed=0, shooting=0, passing=0, defending=0, physical=0, mental=0)
        assert cosine_similarity(zero1, zero2) == 0.0

    def test_euclidean_distance_with_zero_vectors(self):
        """euclidean_distance with zero vectors works correctly."""
        zero = create_player("Zero", speed=0, shooting=0, passing=0, defending=0, physical=0, mental=0)
        non_zero = create_player("NonZero", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        dist = euclidean_distance(zero, non_zero)
        assert dist > 0


# ---------------------------------------------------------------------------
# Players with all-zero attributes
# ---------------------------------------------------------------------------

class TestAllZeroPlayers:
    """Tests for players with all-zero attributes."""

    def test_create_all_zero_player(self):
        """Can create a player with all-zero attributes."""
        player = create_player("AllZero")
        for attr in ["speed", "shooting", "passing", "defending", "physical", "mental"]:
            assert get_attribute(player, attr) == 0.0

    def test_match_all_zero_players(self):
        """match_players works with all-zero players."""
        target = create_player("Target", speed=0, shooting=0, passing=0, defending=0, physical=0, mental=0)
        zero1 = create_player("Zero1", speed=0, shooting=0, passing=0, defending=0, physical=0, mental=0)
        zero2 = create_player("Zero2", speed=0, shooting=0, passing=0, defending=0, physical=0, mental=0)
        results = match_players(target, [zero1, zero2], metric="cosine")
        assert len(results) == 2
        # Both should have similarity 0
        assert results[0]["score"] == 0.0
        assert results[1]["score"] == 0.0


# ---------------------------------------------------------------------------
# Boundary values
# ---------------------------------------------------------------------------

class TestBoundaryValues:
    """Tests for boundary values."""

    def test_all_max_values(self):
        """Player with all attributes at max (100)."""
        player = create_player(
            "MaxPlayer",
            speed=100, shooting=100, passing=100,
            defending=100, physical=100, mental=100,
        )
        for attr in ["speed", "shooting", "passing", "defending", "physical", "mental"]:
            assert get_attribute(player, attr) == 100.0

    def test_all_min_values(self):
        """Player with all attributes at min (0)."""
        player = create_player(
            "MinPlayer",
            speed=0, shooting=0, passing=0,
            defending=0, physical=0, mental=0,
        )
        for attr in ["speed", "shooting", "passing", "defending", "physical", "mental"]:
            assert get_attribute(player, attr) == 0.0

    def test_mixed_boundary_values(self):
        """Player with mixed boundary values."""
        player = create_player(
            "Mixed",
            speed=0, shooting=100, passing=50,
            defending=0, physical=100, mental=50,
        )
        assert get_attribute(player, "speed") == 0.0
        assert get_attribute(player, "shooting") == 100.0
        assert get_attribute(player, "passing") == 50.0
        assert get_attribute(player, "defending") == 0.0
        assert get_attribute(player, "physical") == 100.0
        assert get_attribute(player, "mental") == 50.0


# ---------------------------------------------------------------------------
# Integration: full workflow
# ---------------------------------------------------------------------------

class TestIntegration:
    """Integration tests for the full workflow."""

    def test_full_workflow(self):
        """Test the full workflow: create → get → match."""
        # Create players
        target = create_player(
            "Target",
            speed=80, shooting=90, passing=70,
            defending=60, physical=75, mental=85,
        )
        candidates = [
            create_player("Candidate1", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85),
            create_player("Candidate2", speed=50, shooting=60, passing=40, defending=30, physical=45, mental=55),
            create_player("Candidate3", speed=95, shooting=98, passing=85, defending=50, physical=90, mental=92),
        ]

        # Get attributes
        attrs = get_all_attributes(target)
        assert len(attrs) == 6
        assert attrs["speed"] == 80.0

        # Match
        results = match_players(target, candidates, metric="cosine", top_n=2)
        assert len(results) == 2
        # Candidate1 should be first (identical to target)
        assert results[0]["player"].name == "Candidate1"
        assert results[0]["score"] == 1.0

    def test_match_with_euclidean_metric(self):
        """Test matching with euclidean metric."""
        target = create_player(
            "Target",
            speed=80, shooting=90, passing=70,
            defending=60, physical=75, mental=85,
        )
        candidates = [
            create_player("Close", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85),
            create_player("Far", speed=0, shooting=0, passing=0, defending=0, physical=0, mental=0),
        ]
        results = match_players(target, candidates, metric="euclidean")
        assert len(results) == 2
        assert results[0]["player"].name == "Close"
        assert results[0]["score"] == 1.0  # Score is 1.0 for identical players
        assert results[1]["player"].name == "Far"

    def test_match_empty_candidates(self):
        """match_players with empty candidate list."""
        target = create_player("Target", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        results = match_players(target, [], metric="cosine")
        assert results == []

    def test_match_single_candidate(self):
        """match_players with single candidate."""
        target = create_player("Target", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        candidate = create_player("Candidate", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        results = match_players(target, [candidate], metric="cosine")
        assert len(results) == 1
        assert results[0]["player"].name == "Candidate"
        assert results[0]["score"] == 1.0


# ---------------------------------------------------------------------------
# Large-scale matching
# ---------------------------------------------------------------------------

class TestLargeScale:
    """Tests for large-scale operations."""

    def test_match_many_players(self):
        """match_players works with many players."""
        target = create_player("Target", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        players = [
            create_player(f"P{i}", speed=i * 10, shooting=i * 10, passing=i * 10,
                          defending=i * 10, physical=i * 10, mental=i * 10)
            for i in range(100)
        ]
        results = match_players(target, players, metric="cosine", top_n=10)
        assert len(results) == 10
        # Results should be sorted by score descending
        for i in range(len(results) - 1):
            assert results[i]["score"] >= results[i + 1]["score"]

    def test_match_with_top_n_larger_than_candidates(self):
        """match_players with top_n larger than number of candidates."""
        target = create_player("Target", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        players = [
            create_player(f"P{i}", speed=50, shooting=50, passing=50, defending=50, physical=50, mental=50)
            for i in range(5)
        ]
        results = match_players(target, players, metric="cosine", top_n=100)
        assert len(results) == 5


# ---------------------------------------------------------------------------
# from_dict edge cases
# ---------------------------------------------------------------------------

class TestFromDictEdgeCases:
    """Edge cases for from_dict."""

    def test_from_dict_empty_dict(self):
        """from_dict with empty dict creates player with all zeros."""
        player = PlayerAttribute.from_dict("Empty", {})
        for attr in ["speed", "shooting", "passing", "defending", "physical", "mental"]:
            assert getattr(player, attr) == 0.0

    def test_from_dict_with_extra_keys(self):
        """from_dict ignores extra keys in dict."""
        d = {"speed": 80, "shooting": 90, "extra_key": "ignored"}
        player = PlayerAttribute.from_dict("Extra", d)
        assert player.speed == 80.0
        assert player.shooting == 90.0
        assert player.passing == 0.0

    def test_from_dict_with_negative_clamped(self):
        """from_dict clamps negative values."""
        d = {"speed": -100, "shooting": -50}
        player = PlayerAttribute.from_dict("Negative", d)
        assert player.speed == 0.0
        assert player.shooting == 0.0

    def test_from_dict_with_float_values(self):
        """from_dict accepts float values."""
        d = {"speed": 80.5, "shooting": 90.7}
        player = PlayerAttribute.from_dict("Float", d)
        assert player.speed == 80.5
        assert player.shooting == 90.7


# ---------------------------------------------------------------------------
# set() edge cases
# ---------------------------------------------------------------------------

class TestSetEdgeCases:
    """Edge cases for set()."""

    def test_set_zero_value(self):
        """set() with zero value works."""
        player = create_player("Test")
        player.set("speed", 0)
        assert player.speed == 0.0

    def test_set_max_value(self):
        """set() with max value works."""
        player = create_player("Test")
        player.set("speed", 100)
        assert player.speed == 100.0

    def test_set_float_value(self):
        """set() with float value works."""
        player = create_player("Test")
        player.set("speed", 80.5)
        assert player.speed == 80.5

    def test_set_negative_clamped(self):
        """set() clamps negative values."""
        player = create_player("Test")
        player.set("speed", -50)
        assert player.speed == 0.0

    def test_set_above_max_clamped(self):
        """set() clamps values above 100."""
        player = create_player("Test")
        player.set("speed", 200)
        assert player.speed == 100.0
