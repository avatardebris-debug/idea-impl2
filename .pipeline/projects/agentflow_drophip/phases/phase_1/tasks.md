# Phase 1 Tasks

- [ ] Task 1: Project Scaffolding & BusinessSpec Data Model
  - What: Create the project directory structure, Python package layout, and define the `BusinessSpec` data model that the Intent Parser will output. Set up project dependencies, configuration, and base types.
  - Files:
    - `src/agentflow_drophip/__init__.py`
    - `src/agentflow_drophip/models/business_spec.py` — Pydantic model for BusinessSpec (supplier, niche, pricing, fulfillment, target_market, markup, branding, etc.)
    - `src/agentflow_drophip/config.py` — Configuration loader (env vars, defaults)
    - `src/agentflow_drophip/exceptions.py` — Custom exception hierarchy
    - `pyproject.toml` — Project metadata, dependencies (pydantic, httpx, rich, click)
    - `tests/models/test_business_spec.py` — Unit tests for BusinessSpec validation
  - Done when: `pyproject.toml` installs cleanly; `BusinessSpec` validates correct input and rejects invalid input; all model unit tests pass; directory structure matches the target layout from the master plan.

- [ ] Task 2: Intent Parser Module
  - What: Build the `IntentParser` class that accepts a natural-language string and produces a validated `BusinessSpec` object. Use an LLM call (with a fallback rule-based parser for determinism) to extract fields like niche, supplier preference, target market, markup, fulfillment type, and branding preferences.
  - Files:
    - `src/agentflow_drophip/intent_parser/parser.py` — `IntentParser` class with `parse(text: str) -> BusinessSpec`
    - `src/agentflow_drophip/intent_parser/prompts.py` — LLM prompt templates for extraction
    - `src/agentflow_drophip/intent_parser/rule_based.py` — Fallback regex/heuristic parser for when LLM is unavailable
    - `tests/intent_parser/test_parser.py` — Tests with ≥5 test prompts verifying ≥90% field accuracy against known expected specs
    - `tests/intent_parser/test_rule_based.py` — Tests for the fallback parser
  - Done when: `IntentParser.parse()` returns a valid `BusinessSpec` for standard dropshipping prompts; field accuracy ≥90% on the test suite; fallback parser handles all test prompts without crashing; integration tests confirm end-to-end parsing works.

- [ ] Task 3: DAG-Based Workflow Engine
  - What: Build the core `WorkflowEngine` that takes a `BusinessSpec` and generates a directed acyclic graph of tasks, then executes them. Each node in the DAG represents an action (e.g., "source products", "create listings", "configure fulfillment"). Support task dependencies, retry logic, and state tracking.
  - Files:
    - `src/agentflow_drophip/workflow/engine.py` — `WorkflowEngine` class with `generate(spec: BusinessSpec) -> DAG` and `execute(dag: DAG) -> WorkflowResult`
    - `src/agentflow_drophip/workflow/dag.py` — `DAG` data structure with `Node`, `Edge`, topological sort, cycle detection
    - `src/agentflow_drophip/workflow/task.py` — `Task` model with status, retries, dependencies, and result fields
    - `src/agentflow_drophip/workflow/dsl.py` — DSL or builder to define standard workflow templates (e.g., `standard_dropshipping_workflow(spec)`)
    - `tests/workflow/test_dag.py` — Tests for DAG construction, topological sort, cycle detection
    - `tests/workflow/test_engine.py` — Tests for workflow generation from BusinessSpec and execution with mock tasks
  - Done when: A standard dropshipping `BusinessSpec` produces a valid DAG with ≥15 nodes; DAG executes topologically without cycles; retry logic works on simulated failures; workflow state is trackable at every step.

- [ ] Task 4: Starter Agent Implementations
  - What: Implement the three core agents — `SourcingAgent` (finds products matching the spec), `ListingAgent` (creates product listings), and `FulfillmentAgent` (sets up auto-fulfillment rules). Each agent is a callable task node in the workflow DAG.
  - Files:
    - `src/agentflow_drophip/agents/base.py` — `BaseAgent` abstract class with `execute(context: WorkflowContext) -> AgentResult`
    - `src/agentflow_drophip/agents/sourcing_agent.py` — `SourcingAgent` that queries supplier APIs for products matching niche/price criteria
    - `src/agentflow_drophip/agents/listing_agent.py` — `ListingAgent` that creates listings on the connected storefront
    - `src/agentflow_drophip/agents/fulfillment_agent.py` — `FulfillmentAgent` that configures auto-fulfillment rules and order routing
    - `tests/agents/test_sourcing_agent.py` — Tests with mocked supplier API returning sample products
    - `tests/agents/test_listing_agent.py` — Tests with mocked storefront API confirming listing creation
    - `tests/agents/test_fulfillment_agent.py` — Tests confirming fulfillment rules are set correctly
  - Done when: All three agents execute as DAG nodes without errors; `SourcingAgent` returns ≥10 products from mock data; `ListingAgent` confirms ≥10 listings created on mock storefront; `FulfillmentAgent` configures auto-fulfillment rules successfully; all agent unit tests pass.

- [ ] Task 5: Supplier & Storefront Integration Adapters
  - What: Build the pluggable adapter layer with one concrete supplier adapter (AliExpress via AZAPI or Spocket) and one storefront adapter (Shopify). Adapters must follow a common interface so they can be swapped later.
  - Files:
    - `src/agentflow_drophip/integrations/base.py` — `SupplierAdapter` and `StorefrontAdapter` abstract base classes
    - `src/agentflow_drophip/integrations/supplier/aliexpress.py` — `AliExpressSupplierAdapter` with methods: `search_products(niche, max_price)`, `get_product_details(product_id)`, `place_order(product_id, qty, shipping_address)`
    - `src/agentflow_drophip/integrations/storefront/shopify.py` — `ShopifyStorefrontAdapter` with methods: `create_product_listing(product)`, `update_inventory(product_id, quantity)`, `get_orders()`
    - `tests/integrations/test_aliexpress_adapter.py` — Tests with mocked AZAPI responses
    - `tests/integrations/test_shopify_adapter.py` — Tests with mocked Shopify API responses
  - Done when: Both adapters implement their base class interfaces; all adapter methods work with mocked API responses; adapters can be swapped by configuration without code changes; all integration tests pass.

- [ ] Task 6: CLI Dashboard & End-to-End Entry Point
  - What: Build the CLI entry point (`drophip`) that accepts a natural-language prompt, runs the full pipeline (parse → generate DAG → execute), and displays real-time status, agent decisions, and logs in the terminal using Rich for formatting.
  - Files:
    - `src/agentflow_drophip/cli/main.py` — Click-based CLI with commands: `run <prompt>`, `status`, `logs`, `inspect <workflow_id>`
    - `src/agentflow_drophip/cli/dashboard.py` — Real-time terminal dashboard using Rich (live workflow progress, agent decision logs, error highlights)
    - `src/agentflow_drophip/cli/formatters.py` — Output formatters for specs, DAGs, and results
    - `src/agentflow_drophip/__main__.py` — Entry point for `python -m agentflow_drophip`
    - `tests/cli/test_cli.py` — Tests for CLI command parsing and output formatting
    - `README.md` — Setup instructions, usage examples, and configuration guide
  - Done when: `drophip run "I want to sell pet supplies from AliExpress to US customers at 2.5x markup"` executes the full pipeline and displays real-time status; `drophip status` shows active workflows; `drophip logs` shows agent decisions and errors; CLI output is readable and formatted; README documents setup and usage.