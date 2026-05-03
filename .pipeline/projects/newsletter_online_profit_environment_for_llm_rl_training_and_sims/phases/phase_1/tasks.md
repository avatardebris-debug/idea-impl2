# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and config module
  - What: Create the package structure, pyproject.toml, and SimConfig dataclass with all tunable simulation parameters
  - Files: 
    - Create: `pyproject.toml`, `profit_env/__init__.py`, `profit_env/config.py`, `tests/test_config.py`
  - Done when: `pyproject.toml` is valid with package metadata; `SimConfig` dataclass has all parameters (subscriber_count, cpc, retention_rate, arpu, ad_rate, sponsor_rate, content_cost, operational_cost, growth_rate, churn_rate, seasonal_factor, competitor_count, market_saturation, acquisition_channel_mix, conversion_rate, engagement_rate, sponsorship_fill_rate, refund_rate, tax_rate, discount_rate); `pytest tests/test_config.py` passes with tests for default values, validation, and serialization

- [ ] Task 2: State module and simulator core
  - What: Create NewsletterState dataclass with serialization, and NewsletterSimulator class with acquisition/churn/revenue/costs logic
  - Files:
    - Create: `profit_env/state.py`, `profit_env/simulator.py`, `tests/test_state.py`, `tests/test_simulator.py`
  - Done when: `NewsletterState` has fields (week, subscribers, revenue, costs, profit, cumulative_profit, churned, acquired, engagement_score, sponsor_revenue, ad_revenue); state serializes to/from JSON; `NewsletterSimulator.run_week()` advances one week with subscriber acquisition (based on CPC, conversion_rate, acquisition_channel_mix), churn (based on churn_rate, seasonal_factor), revenue (arpu * subscribers, ad_rate * impressions, sponsor_rate * sponsor_revenue), and costs (content_cost, operational_cost); `pytest tests/test_state.py tests/test_simulator.py` passes

- [ ] Task 3: Observation space and RL environment
  - What: Create ObservationSpace definition with all metrics and NewsletterEnv gymnasium-compatible wrapper
  - Files:
    - Create: `profit_env/observation.py`, `profit_env/environment.py`, `tests/test_observation.py`, `tests/test_environment.py`
  - Done when: `ObservationSpace` defines all observation metrics (subscriber_count, revenue, costs, profit, churn_rate, acquisition_rate, engagement_score, week_number, seasonal_factor, competitor_pressure); `NewsletterEnv` extends `gymnasium.Env` with `reset()`, `step(action)`, `render()` methods; action space is continuous (budget allocation across acquisition, content, sponsorship, operational efficiency); observation space is a Dict with all metrics; `pytest tests/test_observation.py tests/test_environment.py` passes

- [ ] Task 4: CLI entry point and unit tests
  - What: Create CLI with `pe sim run/stats/export` commands and complete unit test suite
  - Files:
    - Create: `profit_env/cli.py`, `tests/test_cli.py`
  - Done when: `pe sim run` executes a 52-week simulation and prints weekly summary; `pe sim stats` prints aggregate statistics (total revenue, total costs, net profit, avg subscribers, avg churn rate); `pe sim export --format csv/json` exports simulation results to file; CLI has argparse with proper subcommands and help text; `pytest tests/` passes with all unit tests

- [ ] Task 5: Documentation
  - What: Create usage documentation and configuration reference
  - Files:
    - Create: `docs/usage.md`, `docs/config_reference.md`, `README.md`
  - Done when: `README.md` describes the project, installation, and quick start; `docs/usage.md` covers all CLI commands with examples; `docs/config_reference.md` documents all SimConfig parameters with defaults and descriptions; all documentation is clear and accurate