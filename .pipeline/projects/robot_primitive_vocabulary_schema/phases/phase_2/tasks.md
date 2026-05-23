# Phase 2 Tasks

- [ ] Task 1: Create Phase 1 deliverables — directory structure and JSON schema
  - What: Create `.pipeline/schemas/` and `.pipeline/code/` directories in the workspace. Create an empty `__init__.py` in `.pipeline/code/`. Create `primitive_schema.json` with draft-07 schema defining all 6 primitive types (grasp, place, slide, push, lift, rotate) with common fields (position, orientation, velocity, acceleration, force_limits, duration) and type-specific fields (grasp_force, grip_mode, surface_type, release_velocity, friction_coefficient, slide_direction, push_force, contact_point, lift_height, orientation_delta, rotation_axis, rotation_angle, pivot_point).
  - Files: `.pipeline/schemas/` (dir), `.pipeline/code/` (dir), `.pipeline/code/__init__.py` (empty), `.pipeline/schemas/primitive_schema.json`
  - Done when: Both directories exist, `__init__.py` is present, `primitive_schema.json` is valid JSON with `$schema: "http://json-schema.org/draft-07/schema#"`, and `python -c "import json; json.load(open('.pipeline/schemas/primitive_schema.json'))"` succeeds.

- [ ] Task 2: Create `primitives.py` with all dataclasses and helper classes
  - What: Create `.pipeline/code/primitives.py` with helper dataclasses (Vector3, Quaternion, Velocity, Acceleration, ForceLimits, Duration), base class `MotionPrimitive`, and 6 concrete subclasses (`GraspPrimitive`, `PlacePrimitive`, `SlidePrimitive`, `PushPrimitive`, `LiftPrimitive`, `RotatePrimitive`). Each class must have `__post_init__` validation. Define `VALID_PRIMITIVE_TYPES = ("grasp", "place", "slide", "push", "lift", "rotate")`.
  - Files: `.pipeline/code/primitives.py`
  - Done when: All 7 classes and `VALID_PRIMITIVE_TYPES` are importable via `from pipeline.code.primitives import MotionPrimitive, GraspPrimitive, PlacePrimitive, SlidePrimitive, PushPrimitive, LiftPrimitive, RotatePrimitive, VALID_PRIMITIVE_TYPES` and `python -c "from pipeline.code.primitives import MotionPrimitive, GraspPrimitive, PlacePrimitive, SlidePrimitive, PushPrimitive, LiftPrimitive, RotatePrimitive, VALID_PRIMITIVE_TYPES; print('OK')"` prints OK.

- [ ] Task 3: Add factory function, validation helpers, and error handling
  - What: In `primitives.py`, add `create_primitive(type: str, **kwargs) -> MotionPrimitive` factory that dispatches to the correct subclass. Add `validate_primitive(primitive: MotionPrimitive) -> bool` that checks all fields. Add `validate_schema(data: dict) -> bool` that validates against the JSON schema. Add `PrimitiveValidationError` exception class. Add utility functions: `normalize_quaternion(q)`, `clamp_value(val, min_val, max_val)`, `validate_vector3(v)`.
  - Files: `.pipeline/code/primitives.py` (append)
  - Done when: `from pipeline.code.primitives import create_primitive, validate_primitive, validate_schema, PrimitiveValidationError, normalize_quaternion, clamp_value, validate_vector3` succeeds, and `create_primitive("grasp", position={"x":0,"y":0,"z":0}, orientation={"w":1,"x":0,"y":0,"z":0}, velocity={"linear":{"x":0.1,"y":0,"z":0},"angular":{"x":0,"y":0,"z":0}}, acceleration={"linear":{"x":0.5,"y":0,"z":0},"angular":{"x":0,"y":0,"z":0}}, force_limits={"max_force":100,"max_torque":50}, duration=1.0, grasp_force=50, grip_mode="parallel")` returns a GraspPrimitive instance.

- [ ] Task 4: Run verification and clean up
  - What: Update `verify.py` to import all 7 classes and 3 helper functions, create instances of all 6 primitive types, validate them, and check schema validity. Run the verification script. Then remove `verify.py` per Phase 1 Task 6 cleanup instructions.
  - Files: `verify.py` (update then delete), workspace root
  - Done when: `python verify.py` prints success for all 6 primitive types, then `verify.py` is removed, and `ls workspace/` shows no `verify.py`.

- [ ] Task 5: Add comprehensive pytest test suite
  - What: Create/update `tests/test_primitives.py` with tests for: (a) valid instantiation of all 7 classes, (b) invalid input rejection (bad vectors, bad quaternions, out-of-range values), (c) factory dispatch for all 6 primitive types, (d) validation helpers (validate_primitive, validate_schema), (e) utility functions (normalize_quaternion, clamp_value, validate_vector3).
  - Files: `tests/test_primitives.py`
  - Done when: `pytest tests/test_primitives.py -v` runs with 0 failures and 0 errors, covering all 6 primitive types and all helper functions.

- [ ] Task 6: Add README.md and requirements.txt
  - What: Create `README.md` with project overview, installation instructions, quick-start examples for all 6 primitives, API reference (classes, factory, validation), and schema reference. Create `requirements.txt` with pinned dependencies (pytest, jsonschema).
  - Files: `README.md`, `requirements.txt`
  - Done when: `README.md` exists with sections for overview, installation, quick-start, API reference, and schema reference. `requirements.txt` contains `pytest` and `jsonschema`. `pip install -r requirements.txt` succeeds.