# Phase 1 Tasks

- [x] Task 1: Field geometry & regulation-size configuration
  - What: Implement the Field class supporting NFL (100yd + 2×10yd endzones), College (100yd + 2×10yd endzones), and High School (100yd + 2×5yd endzones) field sizes. Include yard-line markings, hash marks, endzone boundaries, and a coordinate system (yards from own goal line, 0–120 for NFL/College, 0–110 for HS). Provide a config loader (YAML) to switch between field types.
  - Files: src/football_sim/field.py, src/football_sim/config.py, tests/test_field.py
  - Done when: All three field types produce correct total lengths (NFL/College = 120 yd, HS = 110 yd), yard-line positions are accurate, and a config switch correctly changes field dimensions. Verified by asserting field.length_yards matches rulebook specs for each type.

- [ ] Task 2: Player entity physics engine
  - What: Implement the Player class as a rigid body with position (x, y), velocity (vx, vy), acceleration, and configurable attributes (speed, agility, strength, acceleration_rate). Players have a max speed (mph → yd/s conversion), acceleration curve, and directional change penalty via agility. Include a Formation class that places 11 offensive and 11 defensive players at starting positions on the field.
  - Files: src/football_sim/entities.py, src/football_sim/formation.py, tests/test_entities.py, tests/test_formation.py
  - Done when: Player movement is deterministic given identical inputs (no randomness). Acceleration follows a configurable curve to max speed. Agility correctly reduces turning rate. Formations place exactly 22 players at valid field positions. Unit tests verify position updates over discrete time steps match expected kinematic equations.

- [ ] Task 3: Ball physics & pass trajectory
  - What: Implement the Ball class with position (x, y, z), velocity (vx, vy, vz), spiral stability, and air resistance. Throw mechanics: QB imparts initial velocity vector (horizontal direction + angle, speed) producing a parabolic arc. Gravity acts on z-component. Air resistance dampens vx/vy. Spiral stability affects catch radius (tight spiral = smaller effective target). Include catch radius logic for receiver vs defender proximity.
  - Files: src/football_sim/ball.py, tests/test_ball.py
  - Done when: A pass thrown at 50 mph at 45° angle produces a parabolic arc with hang time between 2.5–4.0 seconds (physically plausible). Air resistance reduces horizontal range by ~10–15%. Spiral tightness modifies catch radius. Same throw parameters always produce the same trajectory (deterministic).

- [ ] Task 4: Collision detection & force transfer
  - What: Implement a CollisionSystem that detects player-player and player-ball collisions each frame. Player-player: circle-circle intersection (radius based on player size). On collision, compute impulse based on relative velocity, mass (derived from strength), and direction — apply force transfer to both players' velocities. Player-ball: similar logic with ball mass << player mass so ball deflects realistically. Include a collision event log for debugging.
  - Files: src/football_sim/collision.py, tests/test_collision.py
  - Done when: Collision fires when two players' positions are within combined radii. Force transfer conserves momentum (within numerical tolerance). Player-ball collision deflects ball direction plausibly. Collision events are logged with timestamp, entities involved, and pre/post velocities. Deterministic: same positions always produce same collision response.

- [ ] Task 5: Playbook data format & play execution engine
  - What: Define a JSON playbook schema with plays containing: name, formation, offensive route definitions (player → route type → waypoints), defensive assignment definitions, and snap type (run/pass). Implement the Playbook loader that reads JSON files. Implement the PlayEngine that, given a play definition, assigns target waypoints to each player, runs the physics simulation frame-by-frame (fixed timestep, e.g., 60 fps), and returns per-frame state snapshots.
  - Files: src/football_sim/playbook.py, src/football_sim/play_engine.py, data/playbooks/sample_plays.json, tests/test_playbook.py, tests/test_play_engine.py
  - Done when: Playbook loads JSON without errors. At least 3 sample plays (run, pass, screen) are defined in sample_plays.json and execute from snap to whistle. PlayEngine produces deterministic output: running the same play twice yields identical frame-by-frame states. Frame snapshots include player positions, ball position, and collision events.

- [ ] Task 6: Outcome determination & CLI/API
  - What: Implement outcome calculation: yards gained (difference between ball carrier position at whistle and line of scrimmage), touchdown detection (ball carrier or ball enters endzone), fumble detection (collision force exceeds player strength threshold while ball carrier is airborne), interception detection (defender reaches ball position before receiver). Provide a clean API: set_down_distance(), execute_play(play_name), get_outcome() returning a result dict. Add a CLI entry point (main.py) for running plays from the command line and printing results.
  - Files: src/football_sim/outcome.py, src/football_sim/simulator.py, src/football_sim/cli.py, tests/test_outcome.py, tests/test_api.py
  - Done when: Outcome dict contains yards_gained, is_touchdown, is_interception, is_fumble, play_result string, and final ball position. Touchdown fires when ball enters endzone. Interception fires when defender reaches ball before receiver. Fumble fires on high-force collision. CLI accepts a play name and prints formatted results. API is callable: Simulator().execute_play("fly_right") returns a valid Outcome. All 3 sample plays produce valid outcomes.