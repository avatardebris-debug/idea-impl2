# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and data pipeline foundation
  - What: Create the Chronovision project structure, install dependencies, and build the SEC data ingestion pipeline that ingests ≥10,000 SEC filings with full parsing. Includes setting up PostgreSQL schema for financial entities, building the sec_importer integration module, and a data loader that produces a clean, queryable dataset of company financial states over time.
  - Files: chronovision/requirements.txt, chronovision/pyproject.toml, chronovision/src/data/__init__.py, chronovision/src/data/sec_importer.py, chronovision/src/data/schema.sql, chronovision/src/data/loader.py, chronovision/src/data/fixtures/sample_filings.json
  - Done when: Pipeline can ingest ≥10,000 SEC filings into PostgreSQL with parsed fields (ticker, filing_type, date, financial_metrics); unit tests verify parsing accuracy on ≥95% of sample filings; data loader exposes a clean API for downstream components.

- [ ] Task 2: State-space representation and world model
  - What: Build a graph-based 2D state-space representation of financial entities (companies, stocks, markets) that serves as the world model. Each node represents a company with features (price, volume, market cap, filing history); edges represent sector/industry relationships. The state space is updated incrementally as new data arrives.
  - Files: chronovision/src/model/__init__.py, chronovision/src/model/state_space.py, chronovision/src/model/graph_builder.py, chronovision/src/model/entity.py, chronovision/src/model/updater.py
  - Done when: State space can represent ≥5 companies with ≥10 features each; graph structure supports neighbor queries and feature lookups; state updates from new data complete in <1 second; integration test verifies state consistency after sequential data ingestion.

- [ ] Task 3: Five baseline prediction models and hypothesis pool manager
  - What: Implement 5 distinct prediction model architectures (linear regression, LSTM, transformer-based, graph neural network, and ensemble/baseline) that predict next-step financial state (stock price direction, filing content) for 1-5 companies. Build the hypothesis pool manager that spawns, monitors, scores, prunes, and evolves these models.
  - Files: chronovision/src/predictor/__init__.py, chronovision/src/predictor/linear_model.py, chronovision/src/predictor/lstm_model.py, chronovision/src/predictor/transformer_model.py, chronovision/src/predictor/gnn_model.py, chronovision/src/predictor/ensemble_model.py, chronovision/src/predictor/hypothesis_pool.py, chronovision/src/predictor/base.py
  - Done when: All 5 models produce predictions on the same input; hypothesis pool can spawn, score, and rank all 5 models; directional accuracy on held-out test data ≥60% for at least 3 models; each model architecture is independently testable with unit tests.

- [ ] Task 4: Surprise calculator and RL minimization loop
  - What: Build the surprise calculator that quantifies the gap between predicted and actual outcomes using multiple metrics (MAE, classification accuracy, Brier score). Implement the basic RL weight update loop (Thompson Sampling / bandit algorithm) that updates hypothesis weights based on surprise scores, with convergence detection.
  - Files: chronovision/src/surprise/__init__.py, chronovision/src/surprise/calculator.py, chronovision/src/rl/__init__.py, chronovision/src/rl/bandit_optimizer.py, chronovision/src/rl/convergence_detector.py
  - Done when: Surprise calculator computes MAE, classification accuracy, and Brier score for any prediction/actual pair; RL loop updates hypothesis weights over 50 epochs with weight distribution converging (KL divergence between epoch 40-50 weights < threshold); surprise computed for ≥95% of predictions; integration test verifies end-to-end prediction → surprise → update cycle completes in <5 minutes.

- [ ] Task 5: Web dashboard, integration tests, and documentation
  - What: Build a Streamlit-based web dashboard showing predictions, actuals, surprise metrics, and hypothesis performance. Write integration tests and evaluation harness. Document the system architecture, setup instructions, and demo procedures.
  - Files: chronovision/dashboard/app.py, chronovision/tests/__init__.py, chronovision/tests/test_integration.py, chronovision/tests/test_evaluation.py, chronovision/tests/conftest.py, chronovision/README.md, chronovision/demo/run_demo.py
  - Done when: Dashboard displays live predictions, actual outcomes, surprise scores, and hypothesis performance rankings; integration tests pass with ≥60% directional accuracy on test data; demo script runs end-to-end showing next-day stock direction prediction with surprise tracking; README includes setup, usage, and architecture documentation.