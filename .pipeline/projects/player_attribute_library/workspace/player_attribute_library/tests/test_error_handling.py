"""Tests for error handling in the player attribute library."""

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


# ------------------------------------------------------------------
# create_player validation
# ------------------------------------------------------------------

class TestCreatePlayerValidation:
    """Test that create_player validates inputs correctly."""

    def test_empty_name_raises_valueerror(self):
        with pytest.raises(ValueError, match="non-empty string"):
            create_player("")

    def test_whitespace_only_name_raises_valueerror(self):
        with pytest.raises(ValueError, match="non-empty string"):
            create_player("   ")

    def test_none_name_raises_typeerror(self):
        with pytest.raises((TypeError, ValueError)):
            create_player(None)

    def test_invalid_attribute_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown attribute"):
            create_player("Test", invalid_attr=50)

    def test_non_numeric_attribute_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a number"):
            create_player("Test", speed="fast")

    def test_non_numeric_attribute_raises_typeerror_for_shooting(self):
        with pytest.raises(TypeError, match="must be a number"):
            create_player("Test", shooting=None)


# ------------------------------------------------------------------
# PlayerAttribute validation
# ------------------------------------------------------------------

class TestPlayerAttributeValidation:
    """Test that PlayerAttribute validates inputs correctly."""

    def test_empty_name_raises_valueerror(self):
        with pytest.raises(ValueError, match="non-empty string"):
            PlayerAttribute(name="")

    def test_whitespace_only_name_raises_valueerror(self):
        with pytest.raises(ValueError, match="non-empty string"):
            PlayerAttribute(name="   ")

    def test_none_name_raises_valueerror(self):
        with pytest.raises(ValueError, match="non-empty string"):
            PlayerAttribute(name=None)

    def test_non_numeric_attribute_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a number"):
            PlayerAttribute(name="Test", speed="fast")

    def test_from_dict_with_invalid_name_raises_valueerror(self):
        with pytest.raises(ValueError, match="non-empty string"):
            PlayerAttribute.from_dict("", {"speed": 50})

    def test_from_dict_with_non_dict_data_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a dict"):
            PlayerAttribute.from_dict("Test", "invalid")

    def test_from_dict_with_non_numeric_value_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a number"):
            PlayerAttribute.from_dict("Test", {"speed": "fast"})


# ------------------------------------------------------------------
# get_attribute validation
# ------------------------------------------------------------------

class TestGetAttributeValidation:
    """Test that get_attribute validates inputs correctly."""

    def test_non_player_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            get_attribute("not a player", "speed")

    def test_non_player_raises_typeerror_for_none(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            get_attribute(None, "speed")


# ------------------------------------------------------------------
# get_all_attributes validation
# ------------------------------------------------------------------

class TestGetAllAttributesValidation:
    """Test that get_all_attributes validates inputs correctly."""

    def test_non_player_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            get_all_attributes("not a player")

    def test_non_player_raises_typeerror_for_none(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            get_all_attributes(None)


# ------------------------------------------------------------------
# euclidean_distance validation
# ------------------------------------------------------------------

class TestEuclideanDistanceValidation:
    """Test that euclidean_distance validates inputs correctly."""

    def test_non_player_a_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            euclidean_distance("not a player", PlayerAttribute(name="B"))

    def test_non_player_b_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            euclidean_distance(PlayerAttribute(name="A"), "not a player")

    def test_none_a_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            euclidean_distance(None, PlayerAttribute(name="B"))

    def test_none_b_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            euclidean_distance(PlayerAttribute(name="A"), None)


# ------------------------------------------------------------------
# cosine_similarity validation
# ------------------------------------------------------------------

class TestCosineSimilarityValidation:
    """Test that cosine_similarity validates inputs correctly."""

    def test_non_player_a_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            cosine_similarity("not a player", PlayerAttribute(name="B"))

    def test_non_player_b_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            cosine_similarity(PlayerAttribute(name="A"), "not a player")

    def test_none_a_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            cosine_similarity(None, PlayerAttribute(name="B"))

    def test_none_b_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            cosine_similarity(PlayerAttribute(name="A"), None)


# ------------------------------------------------------------------
# match_players validation
# ------------------------------------------------------------------

class TestMatchPlayersValidation:
    """Test that match_players validates inputs correctly."""

    def test_non_target_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            match_players("not a player", [PlayerAttribute(name="B")])

    def test_none_target_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            match_players(None, [PlayerAttribute(name="B")])

    def test_invalid_metric_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown metric"):
            match_players(
                PlayerAttribute(name="A"),
                [PlayerAttribute(name="B")],
                metric="invalid",
            )

    def test_invalid_top_n_raises_valueerror(self):
        with pytest.raises(ValueError, match="positive integer"):
            match_players(
                PlayerAttribute(name="A"),
                [PlayerAttribute(name="B")],
                top_n=0,
            )

    def test_negative_top_n_raises_valueerror(self):
        with pytest.raises(ValueError, match="positive integer"):
            match_players(
                PlayerAttribute(name="A"),
                [PlayerAttribute(name="B")],
                top_n=-1,
            )

    def test_non_integer_top_n_raises_valueerror(self):
        with pytest.raises(ValueError, match="positive integer"):
            match_players(
                PlayerAttribute(name="A"),
                [PlayerAttribute(name="B")],
                top_n=1.5,
            )

    def test_non_player_candidate_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            match_players(
                PlayerAttribute(name="A"),
                ["not a player"],
            )

    def test_none_candidate_raises_typeerror(self):
        with pytest.raises(TypeError, match="must be a PlayerAttribute"):
            match_players(
                PlayerAttribute(name="A"),
                [None],
            )
