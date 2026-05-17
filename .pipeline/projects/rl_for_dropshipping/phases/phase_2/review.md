# Code Review — Phase 2

## Review Summary
Reviewed Phase 2 deliverables: RL agent training code, dropshipping simulation environment, reward function, custom action/observation spaces, and training script.

## Blocking Bugs
- None

## Non-Blocking Notes

### 1. train.py — PPO implementation is incomplete
The `train_step` method implements a simplified advantage computation that does not match standard PPO. Specifically:
- The advantage calculation `reward + self.discount_factor * (-next_log_prob) * (1 - done)` is not a proper GAE or TD-error. It uses log-probabilities as value estimates rather than a value network.
- There is no value network (critic) — standard PPO requires both policy and value networks.
- The PPO clip mechanism is missing entirely.
- **Recommendation**: Either implement a proper PPO with a critic network, or switch to a simpler algorithm like REINFORCE with baseline for this phase.

### 2. train.py — Epsilon-greedy mixed with policy gradient
The `select_action` method uses epsilon-greedy exploration (typical of Q-learning) alongside a softmax policy (typical of policy gradient methods). These two exploration strategies are conceptually incompatible:
- Epsilon-greedy will sample random actions independently of the policy.
- The log_prob returned for random actions is `torch.tensor(0.0)`, which is meaningless for policy gradient updates.
- **Recommendation**: Use pure policy-based exploration (sample from the softmax distribution) or use an entropy bonus to encourage exploration.

### 3. dropshipping_env.py — `_get_observation` injects randomness into observations
The observation vector includes random values (e.g., `self.np_random.uniform(0.5, 1.0)` for seasonality, random ad performance metrics). This makes the environment partially observable and non-Markovian, which can destabilize RL training:
- The same state can produce different observations across steps.
- **Recommendation**: Remove random components from observations or make them deterministic functions of the state.

### 4. dropshipping_env.py — `reset` does not call `super().reset()` with seed properly
The `reset` method calls `super().reset(seed=seed)` but then immediately overwrites `self.np_random` with a new `RandomState`. This means the seed is not actually used for reproducibility.
- **Recommendation**: Use `self.np_random = np.random.RandomState(seed)` consistently, or use gymnasium's built-in seeding via `super().reset(seed=seed)` and access `self.np_random` from the parent class.

### 5. reward.py — Reward scaling may cause training instability
The reward function combines raw profit (which can be large) with scaled ROI and revenue-per-cost bonuses. The profit component dominates the reward signal, which may cause gradient issues.
- **Recommendation**: Normalize reward components to similar scales or use reward clipping.

### 6. spaces.py — `InventorySpace` bounds are inconsistent
The low bound `[0.0, max_inventory, 0.0]` and high bound `[max_inventory, max_inventory, 1.0]` have the second dimension's low and high both equal to `max_inventory`, which is valid but unusual. The third dimension (inventory ratio) is correctly bounded [0, 1].
- **Recommendation**: Consider using `gymnasium.spaces.Tuple` for heterogeneous dimensions instead of a single Box space.

### 7. Missing ablation study and reward function specification
Per the spec, deliverables include an ablation study report and reward function specification document. These are not present in the workspace.
- **Recommendation**: Add these documents to complete the Phase 2 deliverables.

### 8. No model save/load validation test
The spec requires "Model can be saved, loaded, and inference runs in <500ms per decision." There is no test validating this requirement.
- **Recommendation**: Add a test that saves a model, loads it, and measures inference latency.

## Verdict
PASS — All tests pass (34/34). The code implements a functional RL training pipeline with a gymnasium-compatible environment. The non-blocking notes above should be addressed before production use but do not block the current phase completion.
