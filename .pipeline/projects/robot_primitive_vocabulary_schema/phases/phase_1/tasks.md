# Phase 1 Tasks

- [ ] Task 1: Create directory structure
  - What: Create `.pipeline/schemas/` and `.pipeline/code/` directories in the workspace. Create an empty `__init__.py` in `.pipeline/code/` so it is a proper Python package (allows `from pipeline.code.primitives import ...`).
  - Files: `.pipeline/schemas/` (dir), `.pipeline/code/` (dir), `.pipeline/code/__init__.py` (empty file)
  - Done when: Both directories exist, `__init__.py` is present in `.pipeline/code/`, and `python -c "import pipeline.code.primitives"` fails only because the module doesn't exist yet (not because of import errors).

- [ ] Task 2: Define JSON schema for motion primitives
  - What: Create `primitive_schema.json` using JSON Schema draft-07 (`$schema: "http://json-schema.org/draft-07/schema#"`). Define a top-level object with `oneOf` for all 6 primitive types. Each primitive must include: `primitive_type` (discriminator enum), `position` (object with x, y, z floats), `orientation` (object with w, x, y, z floats for quaternion), `velocity` (float), `acceleration` (float), `force_limits` (object with max_force and max_torque floats), `duration` (float). Add type-specific properties for each:
    - grasp: `grasp_force` (float), `grip_mode` (enum: pinch, power, parallel)
    - place: `surface_type` (enum: flat, curved, rough, smooth), `release_velocity` (float)
    - slide: `friction_coefficient` (float), `slide_direction` (object with x, y, z)
    - push: `push_force` (float), `contact_point` (object with x, y, z)
    - lift: `lift_height` (float), `orientation_delta` (object with w, x, y, z)
    - rotate: `rotation_axis` (object with x, y, z), `rotation_angle` (float), `pivot_point` (object with x, y, z)
  - Files: `.pipeline/schemas/primitive_schema.json`
  - Done when: Schema file exists with correct `$schema` version, all 6 types are defined with their type-specific fields, and the file is valid JSON.

- [ ] Task 3: Create base MotionPrimitive dataclass and 6 concrete subclasses
  - What: Create `.pipeline/code/primitives.py` with:
    - Base class `MotionPrimitive` (dataclass) with fields: `primitive_type: str`, `position: dict`, `orientation: dict`, `velocity: float`, `acceleration: float`, `force_limits: dict`, `duration: float`.
    - `GraspPrimitive` (subclass) adds: `grasp_force: float`, `grip_mode: str`.
    - `PlacePrimitive` (subclass) adds: `surface_type: str`, `release_velocity: float`.
    - `SlidePrimitive` (subclass) adds: `friction_coefficient: float`, `slide_direction: dict`.
    - `PushPrimitive` (subclass) adds: `push_force: float`, `contact_point: dict`.
    - `LiftPrimitive` (subclass) adds: `lift_height: float`, `orientation_delta: dict`.
    - `RotatePrimitive` (subclass) adds: `rotation_axis: dict`, `rotation_angle: float`, `pivot_point: dict`.
    - Each class must have a `__post_init__` that validates `primitive_type` matches the class name (lowercased).
  - Files: `.pipeline/code/primitives.py`
  - Done when: All 7 classes are defined and importable. Each subclass has at least its type-specific fields. Instantiation of each class with required args succeeds.

- [ ] Task 4: Add factory function and validation helpers
  - What: In `.pipeline/code/primitives.py`, add:
    - `create_primitive(data: dict) -> MotionPrimitive`: reads `primitive_type` from dict, instantiates the correct subclass with remaining fields. Raises `ValueError` for unknown types.
    - `validate_primitive(primitive: MotionPrimitive) -> bool`: checks all required fields are present and non-None, position has x/y/z, orientation has w/x/y/z, force_limits has max_force/max_torque.
    - `validate_schema(schema_path: str = None) -> bool`: loads the JSON schema file (defaulting to `.pipeline/schemas/primitive_schema.json`), verifies it is valid JSON with `$schema` key set to draft-07.
  - Files: `.pipeline/code/primitives.py` (append)
  - Done when: `create_primitive` dispatches correctly for all 6 types. `validate_primitive` returns True for valid instances, False for invalid. `validate_schema` returns True for the existing schema file.

- [ ] Task 5: Verify end-to-end functionality
  - What: Write a temporary verification script at `.pipeline/code/verify.py` that:
    - Imports all 7 classes and 3 helper functions.
    - Creates one instance of each primitive type using direct class instantiation.
    - Creates one instance of each type via `create_primitive` factory.
    - Validates all instances with `validate_primitive`.
    - Validates the schema with `validate_schema`.
    - Prints a summary line per primitive type (PASS/FAIL).
  - Files: `.pipeline/code/verify.py` (new)
  - Done when: Script runs with `python .pipeline/code/verify.py` and prints PASS for all 6 primitive types plus schema validation.

- [ ] Task 6: Clean up and confirm deliverables
  - What: Remove `.pipeline/code/verify.py`. Confirm the three deliverable files are in place. Run a final import check.
  - Files: Remove `.pipeline/code/verify.py`
  - Done when: Only `.pipeline/schemas/primitive_schema.json`, `.pipeline/code/__init__.py`, and `.pipeline/code/primitives.py` remain in the workspace (besides `conftest.py`). `python -c "from pipeline.code.primitives import MotionPrimitive, GraspPrimitive, PlacePrimitive, SlidePrimitive, PushPrimitive, LiftPrimitive, RotatePrimitive, create_primitive, validate_primitive, validate_schema; print('ALL IMPORTS OK')"` prints success.