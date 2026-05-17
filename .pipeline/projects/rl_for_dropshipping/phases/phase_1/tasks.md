# Phase 1 Tasks

- [ ] Task 1: Project scaffolding, dependencies, and configuration
  - What: Create the project directory structure, requirements, and base config files. Set up Python 3.10+ virtual environment with gymnasium, stable-baselines3, numpy, pandas, and logging infrastructure.
  - Files: `rl_dropshipping/requirements.txt`, `rl_dropshipping/pyproject.toml`, `rl_dropshipping/config/settings.yaml`, `rl_dropshipping/src/__init__.py`, `rl_dropshipping/src/config/`, `rl_dropshipping/tests/__init__.py`
  - Done when: `pip install -e .` succeeds, imports work (`from rl_dropshipping.config import settings`), and a minimal smoke-test passes (`pytest tests/test_smoke.py`)

- [ ] Task 2: Gymnasium-compatible dropshipping simulation environment
  - What: Build the core environment class that wraps the MiroFish multi-agent marketplace. Define state space (market conditions, inventory levels, ad performance metrics, competitor pricing), action space (product selection, markup pricing, daily ad budget allocation), and reward function (net profit, ROI, revenue-per-cost). Implement episode reset, step, and rendering hooks.
  - Files: `rl_dropshipping/src/env/dropshipping_env.py`, `rl_dropshipping/src/env/spaces.py`, `rl_dropshipping/src/env/reward.py`, `rl_dropshipping/src/env/__init__.py`
  - Done when: `env = gym.make('Dropshipping-v0')` creates an env with `obs = env.reset()` returning a valid state vector, `obs, reward, done, info = env.step(action)` advances the simulation, and the env runs for 100 steps without error

- [ ] Task 3: Multi-agent population (competitor, consumer, operator agents)
  - What: Implement the three agent types that populate the simulation. Competitor agents follow static or semi-static pricing/inventory policies derived from cloned data. Consumer agents have demand curves and purchase probabilities based on price, product quality, and ad exposure. Operator agents are the RL agent's counterpart (initially rule-based). Wire them into the environment so the market simulates supply, demand, and competition.
  - Files: `rl_dropshipping/src/agents/competitor.py`, `rl_dropshipping/src/agents/consumer.py`, `rl_dropshipping/src/agents/operator.py`, `rl_dropshipping/src/agents/__init__.py`, `rl_dropshipping/src/market/marketplace.py`
  - Done when: Simulation runs with all 3 agent types active, consumer agents generate purchase events, competitor agents react to pricing, and the environment logs agent interactions per step

- [ ] Task 4: Strategy cloning — baseline policies from 5 successful dropshippers
  - What: Collect and structure data on 5 successful dropshipping cases (product selection patterns, pricing markups, ad spend ratios, channel allocation). Convert each into a reproducible policy object that can be loaded into the simulation as a competitor or operator agent. Store raw data and derived policies separately.
  - Files: `rl_dropshipping/data/baseline_strategies/strategy_1.json` through `strategy_5.json`, `rl_dropshipping/src/strategies/cloner.py`, `rl_dropshipping/src/strategies/policy.py`, `rl_dropshipping/src/strategies/__init__.py`, `docs/baseline_strategies.md`
  - Done when: 5 distinct strategy JSON files exist with fields (product_categories, avg_markup_pct, ad_budget_pct, channels, seasonality_weights), `Cloner.load("strategy_1")` returns a valid Policy object, and each policy can be instantiated in the simulation and produces measurable profit over 100 episodes

- [ ] Task 5: Product research auto-agent pipeline
  - What: Build a pipeline that discovers and scores product opportunities. Implement a mock data source (since external APIs like Jungle Scout/AliExpress may require keys) that generates realistic product data with fields: category, cost, estimated_demand, competition_level, margin_pct, seasonality_score. Score each product with a composite score (demand * margin / competition). Output ≥10 scored recommendations per run.
  - Files: `rl_dropshipping/src/research/product_researcher.py`, `rl_dropshipping/src/research/scorer.py`, `rl_dropshipping/src/research/sources/mock_source.py`, `rl_dropshipping/src/research/sources/api_source.py`, `rl_dropshipping/src/research/__init__.py`, `tests/test_product_research.py`
  - Done when: `ProductResearcher.run()` returns ≥10 scored products, each with fields (product_id, name, category, cost, estimated_demand, competition_level, margin_pct, composite_score), and the scoring logic is testable with `pytest tests/test_product_research.py`

- [ ] Task 6: Rule-based baseline agent and metrics dashboard
  - What: Implement a simple rule-based operator agent (e.g., "always pick highest-margin product with demand > threshold, allocate 30% budget to Facebook, 70% to Google, markup 2.5x") and a metrics logging/dashboard system. Log profit, traffic, and revenue-per-cost per episode. Provide a queryable store (CSV + in-memory dict) and a simple HTML/CLI dashboard for visualization.
  - Files: `rl_dropshipping/src/agents/rule_based_agent.py`, `rl_dropshipping/src/metrics/logger.py`, `rl_dropshipping/src/metrics/dashboard.py`, `rl_dropshipping/src/metrics/__init__.py`, `rl_dropshipping/run_baseline.py`, `tests/test_baseline_agent.py`
  - Done when: `run_baseline.py` executes 100 episodes, logs profit/traffic/revenue-per-cost to `metrics/episodes.csv`, the rule-based agent achieves positive net profit over the 100 episodes, and `pytest tests/test_baseline_agent.py` passes