## Phase 2: RL Training Infrastructure & Baseline Comparison

### Description
Build the RL environment and training system. Wrap the physics simulator in a Gym-compatible interface, design the agent architecture and reward function, implement the training loop, and integrate NFL play-call baselines for comparison.

### Deliverable
- **Gym-compatible environment:** `FootballEnv` with `reset()`, `step()`, `render()`, and proper `ObservationSpace` / `ActionSpace` definitions. Observation includes down/distance, field position, score, formation, and player states. Action is play selection + audibles.
- **Agent architecture:** Policy network (CNN + LSTM for spatial-temporal processing of field state) with support for multi-agent (QB, skill positions).
- **Reward function suite:** Multiple reward configs (sparse: win/loss; dense: yards-per-play, expected points added; risk-aware: turnover penalty).
- **Training loop:** Integration with Stable-Baselines3 (PPO) or custom trainer. Configurable hyperparameters via YAML.
- **NFL baseline integration:** Dataset of standard NFL play calls (run/pass probabilities by down/distance/field position). The simulator can run these baselines against trained agents.
- **Training results:** Performance curves showing agent progress over training steps.

### Dependencies
- Phase 1 deliverable (physics engine must be stable and deterministic)
- Stable-Baselines3 or RLlib
- PyTorch
- NFL play-call dataset (e.g., from NFL Next Gen Stats or publicly available datasets)

### Success Criteria
- [ ] Gym environment passes `gym.make` creation and `env.step()` / `env.reset()` round-trip without errors.
- [ ] Agent trains for at least 100k steps without NaNs or divergence.
- [ ] Reward function produces meaningful gradients (loss decreases during training).
- [ ] NFL baseline plays execute in the simulator and produce statistically plausible outcomes.
- [ ] Trained agent achieves ≥ baseline NFL success rate on at least one play type (run or pass) after training.
- [ ] Training logs produce interpretable metrics (win rate, yards/play, turnover rate) over time.

---

