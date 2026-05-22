# [subgoal generator] — Master Plan

## Idea Summary
General-purpose LLM goal decomposition engine. Takes any high-level goal ("build a house", "make $10k/month", "learn Spanish") and uses an LLM to produce an ordered list of subgoals with dependencies. Each subgoal is formatted as a pipeline idea entry and injected into master_ideas.md for the runner to execute. Operates on any domain: robotics, software, business, learning. The agent's hypothesis and goal-creation layer — enables recursive autonomous expansion of any objective into buildable sub

## Phase 1: Core MVP
**Goal**: Build the minimum viable version of [subgoal generator].
**Deliverable**: Working prototype with core functionality.
**Success Criteria**: Core features work and are importable.

## Phase 2: Testing & Polish
**Goal**: Add tests, error handling, and documentation.
**Deliverable**: Test suite passing, README complete.

## Phase 3: Integration & Documentation
**Goal**: Final integration, CLI/API surface, and deployment docs.
**Deliverable**: Production-ready package.
