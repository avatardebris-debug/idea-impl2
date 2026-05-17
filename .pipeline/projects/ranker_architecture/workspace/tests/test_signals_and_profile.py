"""Tests for Signal and TasteProfile data models (Task 1)."""

import pytest
from datetime import datetime, timezone

from ranker_core.signals import Signal, SignalValidationError, VALID_SIGNAL_TYPE_VALUES
from ranker_core.profile import TasteProfile, TasteProfileValidationError


# ── Signal Tests ──────────────────────────────────────────────


class TestSignalValidInputs:
    """Valid Signal creation."""

    def test_create_minimal_signal(self):
        s = Signal(user_id="u1", tool_id="t1", item_id="i1")
        assert s.user_id == "u1"
        assert s.tool_id == "t1"
        assert s.item_id == "i1"
        assert s.signal_type == "explicit_rating"
        assert s.value == 1.0
        assert s.weight == 1.0
        assert s.id is not None
        assert isinstance(s.timestamp, datetime)

    def test_create_full_signal(self):
        ts = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        s = Signal(
            user_id="u1",
            tool_id="t1",
            item_id="i1",
            timestamp=ts,
            signal_type="explicit_rating",
            value=4.5,
            weight=2.0,
        )
        assert s.timestamp == ts
        assert s.signal_type == "explicit_rating"
        assert s.value == 4.5
        assert s.weight == 2.0

    def test_all_valid_signal_types(self):
        for stype in VALID_SIGNAL_TYPE_VALUES:
            if stype == "explicit_rating":
                s = Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type=stype, value=3.0)
            elif stype == "explicit_dislike":
                s = Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type=stype, value=-3.0)
            elif stype == "explicit_rank":
                s = Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type=stype, value=5.0)
            else:
                s = Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type=stype, value=0.5)
            assert s.signal_type == stype

    def test_signal_to_dict(self):
        s = Signal(user_id="u1", tool_id="t1", item_id="i1", value=3.0)
        d = s.to_dict()
        assert d["user_id"] == "u1"
        assert d["tool_id"] == "t1"
        assert d["item_id"] == "i1"
        assert d["value"] == 3.0
        assert "timestamp" in d
        assert "id" in d

    def test_signal_from_dict(self):
        data = {
            "user_id": "u1",
            "tool_id": "t1",
            "item_id": "i1",
            "signal_type": "explicit_rating",
            "value": 4.0,
            "weight": 1.5,
            "timestamp": "2024-06-01T12:00:00+00:00",
        }
        s = Signal.from_dict(data)
        assert s.user_id == "u1"
        assert s.value == 4.0
        assert s.weight == 1.5
        assert isinstance(s.timestamp, datetime)

    def test_signal_equality(self):
        s1 = Signal(user_id="u1", tool_id="t1", item_id="i1", value=3.0)
        s2 = Signal(user_id="u1", tool_id="t1", item_id="i1", value=3.0)
        assert s1 == s2

    def test_signal_inequality(self):
        s1 = Signal(user_id="u1", tool_id="t1", item_id="i1", value=3.0)
        s2 = Signal(user_id="u1", tool_id="t1", item_id="i2", value=3.0)
        assert s1 != s2

    def test_signal_hash(self):
        s1 = Signal(user_id="u1", tool_id="t1", item_id="i1", value=3.0)
        s2 = Signal(user_id="u1", tool_id="t1", item_id="i1", value=3.0)
        assert hash(s1) == hash(s2)


class TestSignalInvalidInputs:
    """Invalid Signal creation should raise SignalValidationError."""

    def test_empty_user_id(self):
        with pytest.raises(SignalValidationError, match="user_id"):
            Signal(user_id="", tool_id="t1", item_id="i1")

    def test_empty_tool_id(self):
        with pytest.raises(SignalValidationError, match="tool_id"):
            Signal(user_id="u1", tool_id="", item_id="i1")

    def test_empty_item_id(self):
        with pytest.raises(SignalValidationError, match="item_id"):
            Signal(user_id="u1", tool_id="t1", item_id="")

    def test_invalid_signal_type(self):
        with pytest.raises(SignalValidationError, match="signal_type"):
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="invalid_type")

    def test_rating_out_of_range(self):
        with pytest.raises(SignalValidationError, match="explicit_rating"):
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=6.0)
        with pytest.raises(SignalValidationError, match="explicit_rating"):
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rating", value=0.0)

    def test_dislike_out_of_range(self):
        with pytest.raises(SignalValidationError, match="explicit_dislike"):
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_dislike", value=0.0)
        with pytest.raises(SignalValidationError, match="explicit_dislike"):
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_dislike", value=-6.0)

    def test_rank_out_of_range(self):
        with pytest.raises(SignalValidationError, match="explicit_rank"):
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rank", value=0.0)
        with pytest.raises(SignalValidationError, match="explicit_rank"):
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="explicit_rank", value=101.0)

    def test_implicit_value_out_of_range(self):
        with pytest.raises(SignalValidationError, match="implicit"):
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="implicit_click", value=1.5)
        with pytest.raises(SignalValidationError, match="implicit"):
            Signal(user_id="u1", tool_id="t1", item_id="i1", signal_type="implicit_view", value=-0.1)

    def test_zero_weight(self):
        with pytest.raises(SignalValidationError, match="weight"):
            Signal(user_id="u1", tool_id="t1", item_id="i1", weight=0.0)

    def test_negative_weight(self):
        with pytest.raises(SignalValidationError, match="weight"):
            Signal(user_id="u1", tool_id="t1", item_id="i1", weight=-1.0)

    def test_weight_exceeds_max(self):
        with pytest.raises(SignalValidationError, match="weight"):
            Signal(user_id="u1", tool_id="t1", item_id="i1", weight=11.0)


# ── TasteProfile Tests ────────────────────────────────────────


class TestTasteProfileValidInputs:
    """Valid TasteProfile creation."""

    def test_create_minimal_profile(self):
        p = TasteProfile(user_id="u1")
        assert p.user_id == "u1"
        assert p.taste_vector == {}
        assert p.metadata == {}
        assert p.id is not None
        assert isinstance(p.created_at, datetime)
        assert isinstance(p.updated_at, datetime)

    def test_create_full_profile(self):
        tv = {"item_a": 0.8, "item_b": 0.3}
        meta = {"category": "music", "source": "manual"}
        p = TasteProfile(user_id="u1", taste_vector=tv, metadata=meta)
        assert p.taste_vector == tv
        assert p.metadata == meta

    def test_update_taste_vector(self):
        p = TasteProfile(user_id="u1")
        p.update_taste_vector("item_a", 0.9)
        assert p.taste_vector["item_a"] == 0.9
        assert p.updated_at > p.created_at

    def test_merge_profile(self):
        p1 = TasteProfile(user_id="u1", taste_vector={"a": 0.5})
        p2 = TasteProfile(user_id="u1", taste_vector={"b": 0.7, "a": 0.9})
        p1.merge(p2)
        assert p1.taste_vector["a"] == 0.9
        assert p1.taste_vector["b"] == 0.7

    def test_profile_to_dict(self):
        p = TasteProfile(user_id="u1", taste_vector={"x": 1.0})
        d = p.to_dict()
        assert d["user_id"] == "u1"
        assert d["taste_vector"] == {"x": 1.0}
        assert "created_at" in d
        assert "updated_at" in d

    def test_profile_from_dict(self):
        data = {
            "user_id": "u1",
            "taste_vector": {"x": 1.0, "y": 2.0},
            "metadata": {"tag": "test"},
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-06-01T00:00:00+00:00",
        }
        p = TasteProfile.from_dict(data)
        assert p.user_id == "u1"
        assert p.taste_vector == {"x": 1.0, "y": 2.0}
        assert p.metadata == {"tag": "test"}
        assert isinstance(p.created_at, datetime)

    def test_profile_equality(self):
        p1 = TasteProfile(user_id="u1", taste_vector={"a": 1.0})
        p2 = TasteProfile(user_id="u1", taste_vector={"a": 1.0})
        assert p1 == p2

    def test_profile_inequality(self):
        p1 = TasteProfile(user_id="u1", taste_vector={"a": 1.0})
        p2 = TasteProfile(user_id="u2", taste_vector={"a": 1.0})
        assert p1 != p2

    def test_profile_inequality_different_taste_vector(self):
        p1 = TasteProfile(user_id="u1", taste_vector={"a": 1.0})
        p2 = TasteProfile(user_id="u1", taste_vector={"a": 2.0})
        assert p1 != p2

    def test_profile_inequality_different_metadata(self):
        p1 = TasteProfile(user_id="u1", taste_vector={"a": 1.0}, metadata={"tag": "x"})
        p2 = TasteProfile(user_id="u1", taste_vector={"a": 1.0}, metadata={"tag": "y"})
        assert p1 != p2

    def test_profile_hash_consistency(self):
        p1 = TasteProfile(user_id="u1", taste_vector={"a": 1.0})
        p2 = TasteProfile(user_id="u1", taste_vector={"a": 1.0})
        assert hash(p1) == hash(p2)

    def test_profile_hash_inequality(self):
        p1 = TasteProfile(user_id="u1", taste_vector={"a": 1.0})
        p2 = TasteProfile(user_id="u1", taste_vector={"a": 2.0})
        assert hash(p1) != hash(p2)

    def test_profile_hash_in_set(self):
        p1 = TasteProfile(user_id="u1", taste_vector={"a": 1.0})
        p2 = TasteProfile(user_id="u1", taste_vector={"a": 1.0})
        profile_set = {p1}
        assert p2 in profile_set

    def test_profile_hash_in_dict(self):
        p1 = TasteProfile(user_id="u1", taste_vector={"a": 1.0})
        p2 = TasteProfile(user_id="u1", taste_vector={"a": 1.0})
        profile_dict = {p1: "value"}
        assert profile_dict[p2] == "value"

    def test_profile_equality_not_instance(self):
        p = TasteProfile(user_id="u1", taste_vector={"a": 1.0})
        assert p != "not a profile"
        assert p != 123
        assert p != None


class TestTasteProfileFromDict:
    """Test TasteProfile.from_dict deserialization."""

    def test_from_dict_with_all_fields(self):
        data = {
            "user_id": "u1",
            "taste_vector": {"x": 1.0, "y": 2.0},
            "metadata": {"tag": "test"},
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-06-01T00:00:00+00:00",
        }
        p = TasteProfile.from_dict(data)
        assert p.user_id == "u1"
        assert p.taste_vector == {"x": 1.0, "y": 2.0}
        assert p.metadata == {"tag": "test"}
        assert isinstance(p.created_at, datetime)
        assert isinstance(p.updated_at, datetime)
        assert p.created_at.year == 2024
        assert p.updated_at.year == 2024

    def test_from_dict_missing_updated_at(self):
        data = {
            "user_id": "u1",
            "taste_vector": {"x": 1.0},
            "metadata": {},
            "created_at": "2024-01-01T00:00:00+00:00",
        }
        p = TasteProfile.from_dict(data)
        assert p.user_id == "u1"
        assert isinstance(p.updated_at, datetime)
        # updated_at should be current time (or close to it)
        assert p.updated_at.year == datetime.now(timezone.utc).year

    def test_from_dict_empty_taste_vector(self):
        data = {
            "user_id": "u1",
            "taste_vector": {},
            "metadata": {},
            "created_at": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-06-01T00:00:00+00:00",
        }
        p = TasteProfile.from_dict(data)
        assert p.taste_vector == {}

    def test_from_dict_round_trip(self):
        original = TasteProfile(user_id="u1", taste_vector={"a": 1.0, "b": 2.0}, metadata={"tag": "test"})
        d = original.to_dict()
        restored = TasteProfile.from_dict(d)
        assert restored.user_id == original.user_id
        assert restored.taste_vector == original.taste_vector
        assert restored.metadata == original.metadata
        assert isinstance(restored.created_at, datetime)
        assert isinstance(restored.updated_at, datetime)


class TestTasteProfileInvalidInputs:
    """Invalid TasteProfile creation should raise TasteProfileValidationError."""

    def test_empty_user_id(self):
        with pytest.raises(TasteProfileValidationError, match="user_id"):
            TasteProfile(user_id="")

    def test_invalid_taste_vector_type(self):
        with pytest.raises(TasteProfileValidationError, match="taste_vector"):
            TasteProfile(user_id="u1", taste_vector="not_a_dict")

    def test_invalid_taste_vector_key(self):
        with pytest.raises(TasteProfileValidationError, match="taste_vector key"):
            TasteProfile(user_id="u1", taste_vector={123: 0.5})

    def test_invalid_taste_vector_value(self):
        with pytest.raises(TasteProfileValidationError, match="taste_vector value"):
            TasteProfile(user_id="u1", taste_vector={"item": "not_numeric"})

    def test_invalid_metadata_type(self):
        with pytest.raises(TasteProfileValidationError, match="metadata"):
            TasteProfile(user_id="u1", metadata="not_a_dict")

    def test_negative_weight_update(self):
        p = TasteProfile(user_id="u1")
        with pytest.raises(TasteProfileValidationError, match="non-negative"):
            p.update_taste_vector("item", -0.5)
