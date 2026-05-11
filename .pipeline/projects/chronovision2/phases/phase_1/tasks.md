# Phase 1 Tasks

- [x] Task 1: Project scaffolding and package setup
  - What: Create the Python package structure for chronovision2 with __init__.py, pyproject.toml, and base configuration
  - Files: chronovision2/__init__.py, chronovision2/config.py, pyproject.toml, chronovision2/core/__init__.py
  - Done when: Package is importable via `import chronovision2` and `from chronovision2.core import WorldSimulator, PredictionEngine, SurpriseMeter` without errors

- [x] Task 2: World simulation engine
  - What: Build the core WorldSimulator class that can create and step forward a simulated world state given an initial observation and a set of rules/hypotheses
  - Files: chronovision2/core/world_simulator.py
  - Done when: WorldSimulator can be instantiated, accepts an initial state dict, and produces a forward-predicted state after stepping; stepping is deterministic and reproducible

- [x] Task 3: Prediction engine
  - What: Build the PredictionEngine class that takes real-world observations, runs multiple world simulations in parallel with different hypotheses, and produces a composite prediction
  - Files: chronovision2/core/prediction_engine.py
  - Done when: PredictionEngine can be instantiated, accepts a list of hypothesis configs, runs simulations, and returns a prediction result object with per-hypothesis and aggregate outputs

- [x] Task 4: Surprise meter (prediction error measurement)
  - What: Build the SurpriseMeter class that compares predicted states against actual observed states and computes a surprise score
  - Files: chronovision2/core/surprise_meter.py
  - Done when: SurpriseMeter accepts predicted and actual state dicts and returns a numeric surprise score; supports at least L1 and L2 distance metrics

- [x] Task 5: Hypothesis manager and RL reward loop
  - What: Build the HypothesisManager that stores, updates, and scores hypotheses based on surprise scores, and wires the RL reward loop that adjusts hypothesis weights over time
  - Files: chronovision2/core/hypothesis_manager.py
  - Done when: HypothesisManager can add hypotheses, score them via SurpriseMeter, update weights using a simple RL-style reward mechanism, and return updated hypothesis configs for the next prediction cycle

- [x] Task 6: Code review
  - What: Review all Phase 1 code and generate review.md
  - Files: phases/phase_1/review.md
  - Done when: Review file exists with verdict and findings