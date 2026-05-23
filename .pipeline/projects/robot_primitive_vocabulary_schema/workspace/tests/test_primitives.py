"""Comprehensive tests for robot motion primitives (Phase 2 Task 1)."""

import json
import math
import pathlib
import sys

import pytest

# Ensure workspace is on sys.path
_ws = pathlib.Path(__file__).resolve().parent.parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from pipeline.code.primitives import (
    Acceleration,
    Duration,
    ForceLimit,
    GraspPrimitive,
    LiftPrimitive,
    MotionPrimitive,
    PlacePrimitive,
    PrimitiveValidationError,
    PrimitiveTypeError,
    PushPrimitive,
    Quaternion,
    RotatePrimitive,
    SlidePrimitive,
    Velocity,
    Vector3,
    clamp_value,
    create_primitive,
    load_schema,
    normalize_quaternion,
    validate_against_schema,
    validate_primitive,
    validate_vector3,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_BASE_KWARGS = {
    "primitive_type": "grasp",
    "position": [0.0, 0.0, 0.0],
    "orientation": [0.0, 0.0, 0.0, 1.0],
    "velocity": 1.0,
    "acceleration": 1.0,
    "force_limit": 10.0,
    "duration": 1.0,
}


def _valid_grasp_kwargs() -> dict:
    k = dict(_BASE_KWARGS)
    k["primitive_type"] = "grasp"
    k["grip_mode"] = "parallel"
    k["grasp_force"] = 5.0
    return k


def _valid_place_kwargs() -> dict:
    k = dict(_BASE_KWARGS)
    k["primitive_type"] = "place"
    k["release_force"] = 2.0
    return k


def _valid_slide_kwargs() -> dict:
    k = dict(_BASE_KWARGS)
    k["primitive_type"] = "slide"
    k["slide_direction"] = [1.0, 0.0, 0.0]
    k["friction_coefficient"] = 0.3
    return k


def _valid_push_kwargs() -> dict:
    k = dict(_BASE_KWARGS)
    k["primitive_type"] = "push"
    k["push_force"] = 5.0
    k["contact_point"] = [0.0, 0.0, 0.0]
    return k


def _valid_lift_kwargs() -> dict:
    k = dict(_BASE_KWARGS)
    k["primitive_type"] = "lift"
    k["lift_height"] = 0.1
    return k


def _valid_rotate_kwargs() -> dict:
    k = dict(_BASE_KWARGS)
    k["primitive_type"] = "rotate"
    k["rotation_axis"] = [0.0, 0.0, 1.0]
    k["rotation_angle"] = math.pi / 2
    return k


# ---------------------------------------------------------------------------
# Task 1a — each of 6 primitive types instantiates correctly with valid params
# ---------------------------------------------------------------------------


class TestValidInstantiation:
    """Test that each primitive type can be created with valid parameters."""

    def test_grasp_valid(self):
        p = GraspPrimitive(**_valid_grasp_kwargs())
        assert p.primitive_type == "grasp"
        assert p.grip_mode == "parallel"
        assert p.grasp_force == 5.0
        assert p.position == [0.0, 0.0, 0.0]
        assert p.duration == 1.0

    def test_place_valid(self):
        p = PlacePrimitive(**_valid_place_kwargs())
        assert p.primitive_type == "place"
        assert p.release_force == 2.0

    def test_slide_valid(self):
        p = SlidePrimitive(**_valid_slide_kwargs())
        assert p.primitive_type == "slide"
        assert p.slide_direction == [1.0, 0.0, 0.0]
        assert p.friction_coefficient == 0.3

    def test_push_valid(self):
        p = PushPrimitive(**_valid_push_kwargs())
        assert p.primitive_type == "push"
        assert p.push_force == 5.0
        assert p.contact_point == [0.0, 0.0, 0.0]

    def test_lift_valid(self):
        p = LiftPrimitive(**_valid_lift_kwargs())
        assert p.primitive_type == "lift"
        assert p.lift_height == 0.1

    def test_rotate_valid(self):
        p = RotatePrimitive(**_valid_rotate_kwargs())
        assert p.primitive_type == "rotate"
        assert p.rotation_angle == pytest.approx(math.pi / 2)

    def test_motion_primitive_base_valid(self):
        p = MotionPrimitive(**_BASE_KWARGS)
        assert p.primitive_type == "grasp"
        assert p.velocity == 1.0
        assert p.acceleration == 1.0


# ---------------------------------------------------------------------------
# Task 1b — each raises ValueError on invalid params
# ---------------------------------------------------------------------------


class TestInvalidParams:
    """Test that invalid parameters raise PrimitiveValidationError."""

    def test_negative_position(self):
        """Negative position values are allowed (they are coordinates),
        but non-numeric values should fail."""
        with pytest.raises((PrimitiveTypeError, PrimitiveValidationError)):
            MotionPrimitive(
                primitive_type="grasp",
                position=["a", 0.0, 0.0],
                orientation=[0.0, 0.0, 0.0, 1.0],
                velocity=1.0,
                acceleration=1.0,
                force_limit=10.0,
                duration=1.0,
            )

    def test_wrong_vector3_length(self):
        with pytest.raises(PrimitiveValidationError):
            MotionPrimitive(
                primitive_type="grasp",
                position=[0.0, 0.0],
                orientation=[0.0, 0.0, 0.0, 1.0],
                velocity=1.0,
                acceleration=1.0,
                force_limit=10.0,
                duration=1.0,
            )

    def test_zero_duration(self):
        with pytest.raises(PrimitiveValidationError):
            MotionPrimitive(
                primitive_type="grasp",
                position=[0.0, 0.0, 0.0],
                orientation=[0.0, 0.0, 0.0, 1.0],
                velocity=1.0,
                acceleration=1.0,
                force_limit=10.0,
                duration=0.0,
            )

    def test_negative_duration(self):
        with pytest.raises(PrimitiveValidationError):
            MotionPrimitive(
                primitive_type="grasp",
                position=[0.0, 0.0, 0.0],
                orientation=[0.0, 0.0, 0.0, 1.0],
                velocity=1.0,
                acceleration=1.0,
                force_limit=10.0,
                duration=-1.0,
            )

    def test_invalid_quaternion_length(self):
        with pytest.raises(PrimitiveValidationError):
            MotionPrimitive(
                primitive_type="grasp",
                position=[0.0, 0.0, 0.0],
                orientation=[0.0, 0.0, 1.0],
                velocity=1.0,
                acceleration=1.0,
                force_limit=10.0,
                duration=1.0,
            )

    def test_zero_norm_quaternion(self):
        with pytest.raises(PrimitiveValidationError):
            MotionPrimitive(
                primitive_type="grasp",
                position=[0.0, 0.0, 0.0],
                orientation=[0.0, 0.0, 0.0, 0.0],
                velocity=1.0,
                acceleration=1.0,
                force_limit=10.0,
                duration=1.0,
            )

    def test_negative_velocity(self):
        with pytest.raises(PrimitiveValidationError):
            MotionPrimitive(
                primitive_type="grasp",
                position=[0.0, 0.0, 0.0],
                orientation=[0.0, 0.0, 0.0, 1.0],
                velocity=-1.0,
                acceleration=1.0,
                force_limit=10.0,
                duration=1.0,
            )

    def test_negative_acceleration(self):
        with pytest.raises(PrimitiveValidationError):
            MotionPrimitive(
                primitive_type="grasp",
                position=[0.0, 0.0, 0.0],
                orientation=[0.0, 0.0, 0.0, 1.0],
                velocity=1.0,
                acceleration=-1.0,
                force_limit=10.0,
                duration=1.0,
            )

    def test_negative_force_limit(self):
        with pytest.raises(PrimitiveValidationError):
            MotionPrimitive(
                primitive_type="grasp",
                position=[0.0, 0.0, 0.0],
                orientation=[0.0, 0.0, 0.0, 1.0],
                velocity=1.0,
                acceleration=1.0,
                force_limit=-1.0,
                duration=1.0,
            )

    def test_grasp_invalid_grip_mode(self):
        k = _valid_grasp_kwargs()
        k["grip_mode"] = "invalid"
        with pytest.raises(PrimitiveValidationError):
            GraspPrimitive(**k)

    def test_grasp_negative_grasp_force(self):
        k = _valid_grasp_kwargs()
        k["grasp_force"] = -1.0
        with pytest.raises(PrimitiveValidationError):
            GraspPrimitive(**k)

    def test_place_negative_release_force(self):
        k = _valid_place_kwargs()
        k["release_force"] = -1.0
        with pytest.raises(PrimitiveValidationError):
            PlacePrimitive(**k)

    def test_slide_invalid_friction(self):
        k = _valid_slide_kwargs()
        k["friction_coefficient"] = 1.5
        with pytest.raises(PrimitiveValidationError):
            SlidePrimitive(**k)

    def test_slide_negative_friction(self):
        k = _valid_slide_kwargs()
        k["friction_coefficient"] = -0.1
        with pytest.raises(PrimitiveValidationError):
            SlidePrimitive(**k)

    def test_push_negative_push_force(self):
        k = _valid_push_kwargs()
        k["push_force"] = -1.0
        with pytest.raises(PrimitiveValidationError):
            PushPrimitive(**k)

    def test_lift_negative_lift_height(self):
        k = _valid_lift_kwargs()
        k["lift_height"] = -0.1
        with pytest.raises(PrimitiveValidationError):
            LiftPrimitive(**k)

    def test_wrong_vector3_type(self):
        with pytest.raises(PrimitiveTypeError):
            MotionPrimitive(
                primitive_type="grasp",
                position="not_a_vector",
                orientation=[0.0, 0.0, 0.0, 1.0],
                velocity=1.0,
                acceleration=1.0,
                force_limit=10.0,
                duration=1.0,
            )

    def test_non_numeric_velocity(self):
        with pytest.raises(PrimitiveTypeError):
            MotionPrimitive(
                primitive_type="grasp",
                position=[0.0, 0.0, 0.0],
                orientation=[0.0, 0.0, 0.0, 1.0],
                velocity="fast",
                acceleration=1.0,
                force_limit=10.0,
                duration=1.0,
            )


# ---------------------------------------------------------------------------
# Task 1c — create_primitive factory dispatches to correct class
# ---------------------------------------------------------------------------


class TestFactoryDispatch:
    """Test that create_primitive dispatches to the correct class."""

    def test_factory_grasp(self):
        p = create_primitive("grasp", **_valid_grasp_kwargs())
        assert isinstance(p, GraspPrimitive)

    def test_factory_place(self):
        p = create_primitive("place", **_valid_place_kwargs())
        assert isinstance(p, PlacePrimitive)

    def test_factory_slide(self):
        p = create_primitive("slide", **_valid_slide_kwargs())
        assert isinstance(p, SlidePrimitive)

    def test_factory_push(self):
        p = create_primitive("push", **_valid_push_kwargs())
        assert isinstance(p, PushPrimitive)

    def test_factory_lift(self):
        p = create_primitive("lift", **_valid_lift_kwargs())
        assert isinstance(p, LiftPrimitive)

    def test_factory_rotate(self):
        p = create_primitive("rotate", **_valid_rotate_kwargs())
        assert isinstance(p, RotatePrimitive)

    def test_factory_unknown_type(self):
        with pytest.raises(ValueError, match="Unknown primitive type"):
            create_primitive("fly", **_BASE_KWARGS)


# ---------------------------------------------------------------------------
# Task 1d — validate_primitive rejects malformed dicts
# ---------------------------------------------------------------------------


class TestValidatePrimitive:
    """Test validate_primitive helper."""

    def test_valid_primitive_passes(self):
        p = GraspPrimitive(**_valid_grasp_kwargs())
        assert validate_primitive(p) is True

    def test_invalid_type_raises(self):
        with pytest.raises(PrimitiveTypeError):
            validate_primitive({"primitive_type": "grasp"})  # type: ignore


# ---------------------------------------------------------------------------
# Task 1e — validate_schema loads and validates against the JSON schema
# ---------------------------------------------------------------------------


class TestValidateSchema:
    """Test JSON schema validation."""

    def test_load_schema(self):
        schema = load_schema()
        assert "$defs" in schema
        assert "GraspPrimitive" in schema["$defs"]

    def test_valid_grasp_dict_passes(self):
        p = GraspPrimitive(**_valid_grasp_kwargs())
        d = p.to_dict()
        assert validate_against_schema(d) is True

    def test_valid_place_dict_passes(self):
        p = PlacePrimitive(**_valid_place_kwargs())
        d = p.to_dict()
        assert validate_against_schema(d) is True

    def test_valid_slide_dict_passes(self):
        p = SlidePrimitive(**_valid_slide_kwargs())
        d = p.to_dict()
        assert validate_against_schema(d) is True

    def test_valid_push_dict_passes(self):
        p = PushPrimitive(**_valid_push_kwargs())
        d = p.to_dict()
        assert validate_against_schema(d) is True

    def test_valid_lift_dict_passes(self):
        p = LiftPrimitive(**_valid_lift_kwargs())
        d = p.to_dict()
        assert validate_against_schema(d) is True

    def test_valid_rotate_dict_passes(self):
        p = RotatePrimitive(**_valid_rotate_kwargs())
        d = p.to_dict()
        assert validate_against_schema(d) is True

    def test_invalid_dict_raises(self):
        with pytest.raises(Exception):  # jsonschema.ValidationError
            validate_against_schema({"primitive_type": "invalid_type"})

    def test_missing_required_field_raises(self):
        with pytest.raises(Exception):
            validate_against_schema({"primitive_type": "grasp"})


# ---------------------------------------------------------------------------
# Helper function tests (Task 2 preview — helpers used by tests)
# ---------------------------------------------------------------------------


class TestHelperFunctions:
    """Test normalize_quaternion, validate_vector3, clamp_value."""

    def test_normalize_quaternion_identity(self):
        q = normalize_quaternion([0.0, 0.0, 0.0, 1.0])
        assert q == [0.0, 0.0, 0.0, 1.0]

    def test_normalize_quaternion_arbitrary(self):
        q = normalize_quaternion([3.0, 0.0, 0.0, 0.0])
        assert q == [1.0, 0.0, 0.0, 0.0]

    def test_normalize_quaternion_zero_norm_raises(self):
        with pytest.raises(PrimitiveValidationError):
            normalize_quaternion([0.0, 0.0, 0.0, 0.0])

    def test_normalize_quaternion_wrong_length_raises(self):
        with pytest.raises(PrimitiveValidationError):
            normalize_quaternion([1.0, 0.0, 0.0])

    def test_validate_vector3_valid(self):
        v = validate_vector3([1.0, 2.0, 3.0])
        assert v == [1.0, 2.0, 3.0]

    def test_validate_vector3_wrong_length_raises(self):
        with pytest.raises(PrimitiveValidationError):
            validate_vector3([1.0, 2.0])

    def test_validate_vector3_non_iterable_raises(self):
        with pytest.raises(PrimitiveTypeError):
            validate_vector3(42)

    def test_clamp_value_within_range(self):
        assert clamp_value(5.0, 0.0, 10.0) == 5.0

    def test_clamp_value_below_min(self):
        assert clamp_value(-1.0, 0.0, 10.0) == 0.0

    def test_clamp_value_above_max(self):
        assert clamp_value(15.0, 0.0, 10.0) == 10.0

    def test_clamp_value_invalid_range_raises(self):
        with pytest.raises(PrimitiveValidationError):
            clamp_value(5.0, 10.0, 0.0)


# ---------------------------------------------------------------------------
# to_dict round-trip tests
# ---------------------------------------------------------------------------


class TestToDict:
    """Test serialization round-trip."""

    def test_grasp_to_dict(self):
        p = GraspPrimitive(**_valid_grasp_kwargs())
        d = p.to_dict()
        assert d["primitive_type"] == "grasp"
        assert d["grip_mode"] == "parallel"
        assert d["grasp_force"] == 5.0

    def test_place_to_dict(self):
        p = PlacePrimitive(**_valid_place_kwargs())
        d = p.to_dict()
        assert d["release_force"] == 2.0

    def test_slide_to_dict(self):
        p = SlidePrimitive(**_valid_slide_kwargs())
        d = p.to_dict()
        assert d["slide_direction"] == [1.0, 0.0, 0.0]

    def test_push_to_dict(self):
        p = PushPrimitive(**_valid_push_kwargs())
        d = p.to_dict()
        assert d["push_force"] == 5.0

    def test_lift_to_dict(self):
        p = LiftPrimitive(**_valid_lift_kwargs())
        d = p.to_dict()
        assert d["lift_height"] == 0.1

    def test_rotate_to_dict(self):
        p = RotatePrimitive(**_valid_rotate_kwargs())
        d = p.to_dict()
        assert d["rotation_angle"] == pytest.approx(math.pi / 2)
