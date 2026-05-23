# Phase 3 Tasks

- [ ] Task 1: Create the `pipeline` Python package infrastructure and core module
  - What: Create the `.pipeline/` package directory structure with `__init__.py` files, then build `.pipeline/code/primitives.py` containing all dataclasses (Vector3, Quaternion, Velocity, Acceleration, ForceLimits, ForceLimit), the base class (MotionPrimitive), 6 concrete subclasses (GraspPrimitive, PlacePrimitive, SlidePrimitive, PushPrimitive, LiftPrimitive, RotatePrimitive), helper functions (normalize_quaternion, validate_vector3, clamp_value), factory function (create_primitive), validation helpers (validate_primitive, validate_against_schema, load_schema), exception classes (PrimitiveValidationError, PrimitiveTypeError), and the VALID_PRIMITIVE_TYPES constant.
  - Files: `.pipeline/__init__.py`, `.pipeline/code/__init__.py`, `.pipeline/code/primitives.py`
  - Done when: `python -c "from pipeline.code.primitives import MotionPrimitive, GraspPrimitive, PlacePrimitive, SlidePrimitive, PushPrimitive, LiftPrimitive, RotatePrimitive, Vector3, Quaternion, Velocity, Acceleration, ForceLimits, ForceLimit, VALID_PRIMITIVE_TYPES, create_primitive, validate_primitive, validate_against_schema, load_schema, PrimitiveValidationError, PrimitiveTypeError, normalize_quaternion, validate_vector3, clamp_value; print('All imports OK')"` succeeds with no errors.

- [ ] Task 2: Create the JSON schema file
  - What: Create `primitive_schema.json` with a draft-07 JSON Schema defining all 6 primitive types (grasp, place, slide, push, lift, rotate) with common fields (primitive_type, position, orientation, velocity, acceleration, force_limits, duration) and type-specific fields (grasp_force, grip_margin for grasp; placement_tolerance for place; contact_point, direction for slide; push_force, contact_point for push; lift_height, clearance for lift; rotation_axis, rotation_angle for rotate).
  - Files: `.pipeline/schemas/primitive_schema.json`
  - Done when: `python -c "import json; json.load(open('.pipeline/schemas/primitive_schema.json')); print('Schema is valid JSON')"` succeeds.

- [ ] Task 3: Create the CLI module
  - What: Create `cli/primitives_cli.py` with a `main()` function that provides a CLI interface for creating, validating, and serializing motion primitives. The CLI should accept commands like `create`, `validate`, and `serialize` with appropriate arguments.
  - Files: `cli/__init__.py`, `cli/primitives_cli.py`
  - Done when: `python -m cli.primitives_cli --help` runs without error and shows help text.

- [ ] Task 4: Create the setup.py for package installation
  - What: Create `setup.py` that allows the package to be installed via `pip install -e .` and makes the CLI available as a console script.
  - Files: `setup.py`
  - Done when: `pip install -e .` succeeds and `python -c "import pipeline; print(pipeline.__version__)"` works.

- [ ] Task 5: Run and verify the test suite
  - What: Run `pytest tests/` to verify all tests pass. The test suite includes tests for all 6 primitive types, factory dispatch, validation, schema validation, helper functions, and serialization round-trips.
  - Files: `tests/test_primitives.py` (already exists), `conftest.py` (already exists)
  - Done when: `pytest tests/ -v` runs and all tests pass with no errors.

- [ ] Task 6: Create deployment documentation
  - What: Create `README.md` with installation instructions, usage examples, and API documentation. Create `DEPLOYMENT.md` with deployment steps for production use.
  - Files: `README.md`, `DEPLOYMENT.md`
  - Done when: Both files exist and contain accurate information about the package.