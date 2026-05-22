"""Tests for the PlayerAttribute data model."""

import pytest
from player_attribute_library.models import (
    PlayerAttribute,
    DEFAULT_ATTRIBUTES,
    MIN_VALUE,
    MAX_VALUE,
)


# ---------------------------------------------------------------------------
# PlayerAttribute creation
# ---------------------------------------------------------------------------

class TestPlayerAttributeCreation:
    """Tests for PlayerAttribute instantiation."""

    def test_default_values(self):
        """PlayerAttribute with no attrs has all zeros."""
        player = PlayerAttribute(name="Default")
        for attr in DEFAULT_ATTRIBUTES:
            assert getattr(player, attr) == 0.0

    def test_partial_override(self):
        """PlayerAttribute accepts partial attribute overrides."""
        player = PlayerAttribute(name="Partial", speed=80, shooting=90)
        assert player.speed == 80.0
        assert player.shooting == 90.0
        for attr in ["passing", "defending", "physical", "mental"]:
            assert getattr(player, attr) == 0.0

    def test_full_override(self):
        """PlayerAttribute accepts all attribute overrides."""
        player = PlayerAttribute(
            name="Full",
            speed=80, shooting=90, passing=70,
            defending=60, physical=75, mental=85,
        )
        assert player.speed == 80.0
        assert player.shooting == 90.0
        assert player.passing == 70.0
        assert player.defending == 60.0
        assert player.physical == 75.0
        assert player.mental == 85.0

    def test_name_is_stripped(self):
        """PlayerAttribute strips whitespace from name."""
        player = PlayerAttribute(name="  Test  ")
        assert player.name == "Test"


# ---------------------------------------------------------------------------
# Clamping behavior
# ---------------------------------------------------------------------------

class TestClamping:
    """Tests for attribute value clamping to [0, 100]."""

    def test_negative_clamped_to_zero(self):
        """Negative values are clamped to 0.0."""
        player = PlayerAttribute(name="Neg", speed=-50, shooting=-100)
        assert player.speed == 0.0
        assert player.shooting == 0.0

    def test_above_max_clamped_to_100(self):
        """Values above 100 are clamped to 100.0."""
        player = PlayerAttribute(name="Max", speed=150, shooting=200)
        assert player.speed == 100.0
        assert player.shooting == 100.0

    def test_boundary_zero(self):
        """Zero is not clamped."""
        player = PlayerAttribute(name="Zero", speed=0)
        assert player.speed == 0.0

    def test_boundary_100(self):
        """100 is not clamped."""
        player = PlayerAttribute(name="Hundred", speed=100)
        assert player.speed == 100.0

    def test_set_negative_clamped(self):
        """set() clamps negative values."""
        player = PlayerAttribute(name="Test")
        player.set("speed", -50)
        assert player.speed == 0.0

    def test_set_above_max_clamped(self):
        """set() clamps values above 100."""
        player = PlayerAttribute(name="Test")
        player.set("speed", 200)
        assert player.speed == 100.0

    def test_set_boundary_values(self):
        """set() preserves boundary values."""
        player = PlayerAttribute(name="Test")
        player.set("speed", 0)
        assert player.speed == 0.0
        player.set("speed", 100)
        assert player.speed == 100.0

    def test_set_float_value(self):
        """set() accepts float values."""
        player = PlayerAttribute(name="Test")
        player.set("speed", 80.5)
        assert player.speed == 80.5

    def test_from_dict_negative_clamped(self):
        """from_dict clamps negative values."""
        player = PlayerAttribute.from_dict("Neg", {"speed": -100, "shooting": -50})
        assert player.speed == 0.0
        assert player.shooting == 0.0

    def test_from_dict_above_max_clamped(self):
        """from_dict clamps values above 100."""
        player = PlayerAttribute.from_dict("Max", {"speed": 150, "shooting": 200})
        assert player.speed == 100.0
        assert player.shooting == 100.0


# ---------------------------------------------------------------------------
# Name validation
# ---------------------------------------------------------------------------

class TestNameValidation:
    """Tests for player name validation."""

    def test_empty_name_raises_valueerror(self):
        with pytest.raises(ValueError, match="non-empty string"):
            PlayerAttribute(name="")

    def test_whitespace_only_name_raises_valueerror(self):
        with pytest.raises(ValueError, match="non-empty string"):
            PlayerAttribute(name="   ")

    def test_none_name_raises_valueerror(self):
        with pytest.raises(ValueError, match="non-empty string"):
            PlayerAttribute(name=None)

    def test_name_is_stripped(self):
        """Whitespace is stripped from name."""
        player = PlayerAttribute(name="  Test  ")
        assert player.name == "Test"


# ---------------------------------------------------------------------------
# get() and set() accessors
# ---------------------------------------------------------------------------

class TestGetSetAccessors:
    """Tests for get() and set() methods."""

    def test_get_all_attributes(self):
        """get() returns correct value for all attributes."""
        player = PlayerAttribute(name="Test", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        assert player.get("speed") == 80.0
        assert player.get("shooting") == 90.0
        assert player.get("passing") == 70.0
        assert player.get("defending") == 60.0
        assert player.get("physical") == 75.0
        assert player.get("mental") == 85.0

    def test_get_unknown_attribute_raises_keyerror(self):
        """get() raises KeyError for unknown attribute."""
        player = PlayerAttribute(name="Test")
        with pytest.raises(KeyError):
            player.get("invalid_attr")

    def test_set_all_attributes(self):
        """set() works for all attributes."""
        player = PlayerAttribute(name="Test")
        player.set("speed", 80)
        player.set("shooting", 90)
        player.set("passing", 70)
        player.set("defending", 60)
        player.set("physical", 75)
        player.set("mental", 85)
        assert player.speed == 80.0
        assert player.shooting == 90.0
        assert player.passing == 70.0
        assert player.defending == 60.0
        assert player.physical == 75.0
        assert player.mental == 85.0

    def test_set_unknown_attribute_raises_keyerror(self):
        """set() raises KeyError for unknown attribute."""
        player = PlayerAttribute(name="Test")
        with pytest.raises(KeyError):
            player.set("invalid_attr", 50)

    def test_set_non_numeric_raises_typeerror(self):
        """set() raises TypeError for non-numeric value."""
        player = PlayerAttribute(name="Test")
        with pytest.raises(TypeError, match="must be a number"):
            player.set("speed", "fast")


# ---------------------------------------------------------------------------
# to_dict
# ---------------------------------------------------------------------------

class TestToDict:
    """Tests for to_dict() method."""

    def test_returns_all_6_attributes(self):
        """to_dict returns all 6 attributes."""
        player = PlayerAttribute(name="Test")
        d = player.to_dict()
        assert len(d) == 6
        for attr in DEFAULT_ATTRIBUTES:
            assert attr in d

    def test_returns_correct_values(self):
        """to_dict returns correct values."""
        player = PlayerAttribute(name="Test", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        d = player.to_dict()
        assert d["speed"] == 80.0
        assert d["shooting"] == 90.0
        assert d["passing"] == 70.0
        assert d["defending"] == 60.0
        assert d["physical"] == 75.0
        assert d["mental"] == 85.0

    def test_default_values(self):
        """to_dict returns zeros for default player."""
        player = PlayerAttribute(name="Default")
        d = player.to_dict()
        for attr in DEFAULT_ATTRIBUTES:
            assert d[attr] == 0.0


# ---------------------------------------------------------------------------
# from_dict
# ---------------------------------------------------------------------------

class TestFromDict:
    """Tests for from_dict() class method."""

    def test_round_trip_preservation(self):
        """from_dict and to_dict preserve values."""
        original = PlayerAttribute(name="Test", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        d = original.to_dict()
        restored = PlayerAttribute.from_dict("Test", d)
        for attr in DEFAULT_ATTRIBUTES:
            assert getattr(restored, attr) == getattr(original, attr)

    def test_partial_data(self):
        """from_dict works with partial data."""
        player = PlayerAttribute.from_dict("Partial", {"speed": 80})
        assert player.speed == 80.0
        for attr in ["shooting", "passing", "defending", "physical", "mental"]:
            assert getattr(player, attr) == 0.0

    def test_invalid_name_raises_valueerror(self):
        """from_dict raises ValueError for invalid name."""
        with pytest.raises(ValueError, match="non-empty string"):
            PlayerAttribute.from_dict("", {})

    def test_invalid_data_raises_typeerror(self):
        """from_dict raises TypeError for non-dict data."""
        with pytest.raises(TypeError, match="must be a dict"):
            PlayerAttribute.from_dict("Test", "not a dict")

    def test_non_numeric_attribute_raises_typeerror(self):
        """from_dict raises TypeError for non-numeric attribute."""
        with pytest.raises(TypeError, match="must be a number"):
            PlayerAttribute.from_dict("Test", {"speed": "fast"})


# ---------------------------------------------------------------------------
# __repr__
# ---------------------------------------------------------------------------

class TestRepr:
    """Tests for __repr__ method."""

    def test_repr_format(self):
        """__repr__ has correct format."""
        player = PlayerAttribute(name="Test", speed=80, shooting=90, passing=70, defending=60, physical=75, mental=85)
        r = repr(player)
        assert "PlayerAttribute(name='Test'" in r
        assert "speed=80.0" in r
        assert "shooting=90.0" in r
        assert "passing=70.0" in r
        assert "defending=60.0" in r
        assert "physical=75.0" in r
        assert "mental=85.0" in r

    def test_repr_default_values(self):
        """__repr__ shows zeros for default values."""
        player = PlayerAttribute(name="Default")
        r = repr(player)
        assert "speed=0.0" in r
        assert "shooting=0.0" in r
        assert "passing=0.0" in r
        assert "defending=0.0" in r
        assert "physical=0.0" in r
        assert "mental=0.0" in r
