# Phase 1 Tasks

- [x] Task 1: Create project structure and package skeleton
  - What: Set up the Python package directory `shared_libs/RobotPrimitives/` with `__init__.py`, `pyproject.toml`, and `requirements.txt`
  - Files: shared_libs/RobotPrimitives/__init__.py, shared_libs/RobotPrimitives/pyproject.toml, shared_libs/RobotPrimitives/requirements.txt
  - Done when: Package directory exists with valid `__init__.py` (empty or with version), `pyproject.toml` with project metadata, and `requirements.txt` listing any dependencies (none required for MVP)

- [x] Task 2: Define the Primitive base class and data model
  - What: Create `primitive.py` with a `Primitive` base class that defines the canonical interface for all robot action primitives. Include fields: name, category, parameters (schema), description, preconditions, postconditions, and a `execute()` method signature.
  - Files: shared_libs/RobotPrimitives/primitive.py
  - Done when: `Primitive` class is defined with name, category, parameters, description, preconditions, postconditions attributes and an abstract `execute()` method; class can be instantiated and imported

- [x] Task 3: Implement locomotion primitives
  - What: Create `locomotion.py` with concrete primitive subclasses: `MoveTo`, `RotateTo`, `Approach`, `Retreat`. Each should define its specific parameters and category.
  - Files: shared_libs/RobotPrimitives/locomotion.py
  - Done when: All 4 locomotion primitives are defined as subclasses of `Primitive`, each with correct category="locomotion", and can be imported from the package

- [x] Task 4: Implement manipulation primitives
  - What: Create `manipulation.py` with concrete primitive subclasses: `Grasp`, `Release`, `Push`, `Pull`, `Lift`, `Place`, `Insert`, `RotateObject`. Each should define its specific parameters and category.
  - Files: shared_libs/RobotPrimitives/manipulation.py
  - Done when: All 8 manipulation primitives are defined as subclasses of `Primitive`, each with correct category="manipulation", and can be imported from the package

- [x] Task 5: Implement observation and force primitives
  - What: Create `observation.py` with `LookAt`, `Scan`, `MeasureDistance`, `DetectObject` and `force.py` with `ApplyForce`, `ApplyTorque`, `MaintainContact`. Each with correct category and parameters.
  - Files: shared_libs/RobotPrimitives/observation.py, shared_libs/RobotPrimitives/force.py
  - Done when: All 7 observation/force primitives are defined with correct categories and can be imported from the package

- [x] Task 6: Implement control flow primitives and wire up the package
  - What: Create `control_flow.py` with `Sequence`, `Parallel`, `RepeatUntil`, `Conditional`, `Wait`, `SignalDone`, `RequestHuman`. Update `__init__.py` to export all primitives at the package level for easy importing.
  - Files: shared_libs/RobotPrimitives/control_flow.py, shared_libs/RobotPrimitives/__init__.py
  - Done when: All 7 control flow primitives are defined with correct category="control_flow"; `__init__.py` exports all primitives so `from RobotPrimitives import MoveTo, Grasp, LookAt, Sequence` works; all ~29 primitives are importable as a single package import