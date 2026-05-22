# [robot primitive vocabulary] — Master Plan

## Idea Summary
Design document and shared library module defining ~25-30 canonical atomic robot action primitives. Locomotion: move_to, rotate_to, approach, retreat. Manipulation: grasp, release, push, pull, lift, place, insert, rotate_object. Observation: look_at, scan, measure_distance, detect_object. Force: apply_force, apply_torque, maintain_contact. Control flow: sequence, parallel, repeat_until, conditional, wait, signal_done, request_human. Published as shared_libs/RobotPrimitives/ so all robot projects

## Phase 1: Core MVP
**Goal**: Build the minimum viable version of [robot primitive vocabulary].
**Deliverable**: Working prototype with core functionality.
**Success Criteria**: Core features work and are importable.

## Phase 2: Testing & Polish
**Goal**: Add tests, error handling, and documentation.
**Deliverable**: Test suite passing, README complete.

## Phase 3: Integration & Documentation
**Goal**: Final integration, CLI/API surface, and deployment docs.
**Deliverable**: Production-ready package.
