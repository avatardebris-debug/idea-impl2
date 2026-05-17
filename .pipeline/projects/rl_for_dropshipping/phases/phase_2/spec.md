## Phase 2: RL Agent Training & Optimization

**Goal**: Train a deep RL agent in the simulation that outperforms baseline strategies.

**Description**:
- Implement the RL agent using Deep RL Zoo (start with PPO for stability, then evaluate SAC/DQN)
- Define the full state space: market conditions, competitor pricing, inventory levels, ad account status, seasonality
- Define the action space: product selection, markup pricing, daily ad budget allocation across channels, bid adjustments
- Design reward function: weighted combination of net profit, ROI, revenue-per-cost, with penalty for stockouts and ad account flags
- Implement imitation learning warm-up: pre-train on cloned successful strategies before RL fine-tuning
- Run extensive training in simulation with varying market conditions (competitive density, demand shocks, platform policy changes)
- Implement auto-research integration: RL agent triggers product research when inventory is low or new opportunities detected
- Hyperparameter sweep and ablation studies on reward weights

**Deliverable**:
- Trained RL agent (PPO or SAC) that outperforms baseline by ≥20% in simulated profit
- Trained model checkpoints and training logs
- Reward function specification document
- Ablation study report showing which reward components drive performance
- Auto-research pipeline integrated with agent decision loop

**Dependencies**:
- Phase 1 deliverables (simulation environment, baseline strategies)
- GPU compute (RTX 3090+ or cloud GPU instance)
- Stable Baselines3 / CleanRL / DRL-zoo
- Ray RLlib or similar for distributed training (optional, for scale)

**Success Criteria**:
- [ ] RL agent achieves ≥20% higher profit than rule-based baseline over 500+ training episodes
- [ ] Agent demonstrates generalization across at least 3 different simulated market conditions
- [ ] Training converges (reward stabilizes within ±5% over last 50 episodes)
- [ ] Auto-research triggers are effective (≥70% of triggered products are viable)
- [ ] Model can be saved, loaded, and inference runs in <500ms per decision

---

