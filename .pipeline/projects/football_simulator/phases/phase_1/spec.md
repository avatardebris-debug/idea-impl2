## Phase 1: Core Physics & Field Simulation (MVP)

### Description
Build the foundational simulation engine: regulation-field geometry, player and ball physics, collision detection, and a play definition/execution system. This is the smallest useful thing — a simulator where you can define a play, execute it, and see physics-based outcomes.

### Deliverable
A working football simulator with:
- **Regulation field support:** NFL (100yd + 2×10yd endzones), College (100yd + 2×10yd endzones), High School (100yd + 2×5yd endzones) — configurable.
- **Entity physics engine:** Players as rigid bodies with position, velocity, acceleration, and configurable attributes (speed, agility, strength). Ball physics with parabolic trajectory, spiral stability, and air resistance.
- **Collision system:** Player-player and player-ball collision detection with force transfer.
- **Play execution:** A playbook data format (JSON or YAML) defining routes, blocks, and assignments. Play execution runs the physics simulation frame-by-frame.
- **Outcome determination:** Automatic yardage calculation, touchdown detection, fumble/interception triggers based on physics states.
- **CLI / API:** Function calls to define plays, set down/distance, execute, and retrieve results.

### Dependencies
- None (foundation layer — no external training dependencies)
- Python 3.10+, NumPy, optional Pygame for debug visualization

### Success Criteria
- [ ] All three field sizes render correctly with regulation dimensions (verified against NFL rulebook specs).
- [ ] A pass play executes with physically plausible ball trajectory (parabolic arc, realistic hang time).
- [ ] Collision detection fires correctly when players occupy the same space.
- [ ] A complete play (snap to whistle) executes deterministically — same inputs produce same outputs.
- [ ] Outcome metrics (yards, TD, turnover) are computed and returned accurately.
- [ ] At least 3 sample plays (run, pass, screen) are defined and execute correctly.

---