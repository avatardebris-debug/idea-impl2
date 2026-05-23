"""End-to-end verification for Phase 1 deliverables."""

import json
import pathlib
import sys

# Ensure workspace is on sys.path (same as conftest.py)
_ws = pathlib.Path(__file__).resolve().parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from pipeline.code.primitives import (
    GraspPrimitive,
    LiftPrimitive,
    MotionPrimitive,
    PlacePrimitive,
    PushPrimitive,
    Quaternion,
    RotatePrimitive,
    SlidePrimitive,
    Vector3,
    Velocity,
    Acceleration,
    ForceLimits,
    VALID_PRIMITIVE_TYPES,
    create_primitive,
    validate_primitive,
    validate_schema,
)


def test_imports() -> None:
    """All required symbols are importable."""
    print("[OK] All imports successful")


def test_schema_exists() -> None:
    """JSON schema file exists and is valid JSON."""
    schema_path = _ws / ".pipeline" / "schemas" / "primitive_schema.json"
    assert schema_path.exists(), f"Schema file missing: {schema_path}"
    with open(schema_path) as f:
        schema = json.load(f)
    assert "$schema" in schema
    assert "primitive_type" in schema["properties"]
    print("[OK] Schema file exists and is valid")


def test_directories_exist() -> None:
    """Required directories are present."""
    assert (_ws / ".pipeline" / "schemas").is_dir()
    assert (_ws / ".pipeline" / "code").is_dir()
    assert (_ws / ".pipeline" / "code" / "__init__.py").exists()
    print("[OK] Directory structure correct")


def test_base_primitive() -> None:
    """MotionPrimitive can be instantiated and validated."""
    p = MotionPrimitive(
        primitive_type="grasp",
        position=Vector3(0.1, 0.2, 0.3),
        orientation=Quaternion(0, 0, 0, 1),
        velocity=Velocity(linear=Vector3(0.1, 0.1, 0.1), angular=Vector3(0, 0, 0)),
        acceleration=Acceleration(linear=Vector3(0.5, 0.5, 0.5), angular=Vector3(0, 0, 0)),
        force_limits=ForceLimits(max_force=50.0, max_torque=10.0),
        duration=1.0,
    )
    errs = validate_primitive(p)
    assert errs == [], f"Unexpected validation errors: {errs}"
    d = p.to_dict()
    assert d["primitive_type"] == "grasp"
    assert d["position"]["x"] == 0.1
    print("[OK] MotionPrimitive works")


def test_concrete_primitives() -> None:
    """All 6 concrete primitives can be created via factory."""
    base_kwargs = {
        "position": Vector3(0.1, 0.2, 0.3),
        "orientation": Quaternion(0, 0, 0, 1),
        "velocity": Velocity(linear=Vector3(0.1, 0.1, 0.1), angular=Vector3(0, 0, 0)),
        "acceleration": Acceleration(linear=Vector3(0.5, 0.5, 0.5), angular=Vector3(0, 0, 0)),
        "force_limits": ForceLimits(max_force=50.0, max_torque=10.0),
        "duration": 1.0,
    }
    for ptype in VALID_PRIMITIVE_TYPES:
        p = create_primitive(primitive_type=ptype, **base_kwargs)
        assert p.primitive_type == ptype
        errs = validate_primitive(p)
        assert errs == [], f"Validation errors for {ptype}: {errs}"
    print("[OK] All 6 concrete primitives created and validated")


def test_factory_invalid_type() -> None:
    """Factory raises ValueError for unknown type."""
    try:
        create_primitive(primitive_type="fly", **{
            "position": Vector3(0, 0, 0),
            "orientation": Quaternion(0, 0, 0, 1),
            "velocity": Velocity(linear=Vector3(0, 0, 0), angular=Vector3(0, 0, 0)),
            "acceleration": Acceleration(linear=Vector3(0, 0, 0), angular=Vector3(0, 0, 0)),
            "force_limits": ForceLimits(max_force=0, max_torque=0),
            "duration": 1.0,
        })
        assert False, "Should have raised ValueError"
    except ValueError:
        print("[OK] Factory rejects invalid type")


def test_validate_schema() -> None:
    """validate_schema returns True."""
    assert validate_schema() is True
    print("[OK] validate_schema passed")


def test_validation_errors() -> None:
    """validate_primitive catches bad data."""
    p = MotionPrimitive(
        primitive_type="grasp",
        position=Vector3(float("nan"), 0.2, 0.3),
        orientation=Quaternion(0, 0, 0, 1),
        velocity=Velocity(linear=Vector3(0.1, 0.1, 0.1), angular=Vector3(0, 0, 0)),
        acceleration=Acceleration(linear=Vector3(0.5, 0.5, 0.5), angular=Vector3(0, 0, 0)),
        force_limits=ForceLimits(max_force=50.0, max_torque=10.0),
        duration=1.0,
    )
    errs = validate_primitive(p)
    assert len(errs) > 0, "Should have caught NaN position"
    print("[OK] Validation catches errors")


if __name__ == "__main__":
    tests = [
        test_imports,
        test_schema_exists,
        test_directories_exist,
        test_base_primitive,
        test_concrete_primitives,
        test_factory_invalid_type,
        test_validate_schema,
        test_validation_errors,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as exc:
            print(f"[FAIL] {t.__name__}: {exc}")
            failed += 1
    if failed:
        print(f"\n{failed}/{len(tests)} tests FAILED")
        sys.exit(1)
    else:
        print(f"\nAll {len(tests)} tests PASSED")
