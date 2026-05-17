## Phase 1: Simulation Environment & Baseline Strategies (MVP)

**Goal**: Build a working simulated marketplace and establish baseline strategies by cloning successful dropshippers.

**Description**:
- Set up MiroFish as the multi-agent simulation environment
- Build a dropshipping-specific environment wrapper (state space, action space, reward function)
- Collect and structure data on successful dropshipping strategies (product selection, pricing, ad spend patterns)
- Implement strategy cloning: convert successful strategies into baseline policies for imitation learning
- Build the product research auto-agent that can discover and evaluate product opportunities
- Create a simple rule-based baseline agent for comparison

**Deliverable**:
- A runnable simulation environment where a rule-based agent can operate and generate metrics
- Cloned baseline strategies from at least 5 successful dropshipping cases
- Product research pipeline that outputs scored product opportunities
- Metrics dashboard showing profit, traffic, and revenue-per-cost in simulation

**Dependencies**:
- MiroFish framework (GitHub: `mirofish` or equivalent multi-agent sim)
- Deep RL Zoo (GitHub: `DRL-zoo` or `stable-baselines3-contrib`)
- Product research data sources (AliExpress API, Jungle Scout API, or web scraping)
- Python 3.10+, gymnasium for environment interface

**Success Criteria**:
- [ ] Simulation runs with at least 3 agent types (competitor, consumer, operator)
- [ ] Rule-based baseline agent achieves measurable profit in simulation over 100 episodes
- [ ] Product research pipeline produces ≥10 scored product recommendations per run
- [ ] Metrics (profit, traffic, revenue-per-cost) are logged and queryable
- [ ] Baseline strategies are reproducible from cloned data

---