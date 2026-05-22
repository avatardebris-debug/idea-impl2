# [Robot primitive vocabulary schema] — Master Plan

## Idea Summary
[goal:bootstrap_robot_training:b001] Create a JSON schema and Python dataclasses for robot motion primitives. Define atomic primitives (grasp, place, slide, push, lift, rotate) with parameters: position (x,y,z), orientation (quaternion), velocity, acceleration, force limits, duration. Output: .pipeline/schemas/primitive_schema.json and .pipeline/code/primitives.py with classes: MotionPrimitive, GraspPrimitive, PlacePrimitive, and validation functions.

## Phase 1: Core MVP
**Goal**: Build the minimum viable version of [Robot primitive vocabulary schema].
**Deliverable**: Working prototype with core functionality.
**Success Criteria**: Core features work and are importable.

## Phase 2: Testing & Polish
**Goal**: Add tests, error handling, and documentation.
**Deliverable**: Test suite passing, README complete.

## Phase 3: Integration & Documentation
**Goal**: Final integration, CLI/API surface, and deployment docs.
**Deliverable**: Production-ready package.
