# AgentFlow Drophip — Implementation Plan

## Project Overview
AgentFlow Drophip is an AI-powered dropshipping automation system that:
1. Parses natural language business descriptions into structured specs
2. Orchestrates a multi-agent workflow (sourcing → listing → fulfillment)
3. Manages the workflow via a DAG-based engine

## Current State Analysis

### Completed Modules
| Module | Status | Notes |
|--------|--------|-------|
| `models/business_spec.py` | ✅ Complete | Pydantic models for BusinessSpec, TargetMarket, BrandingConfig, PricingConfig, enums |
| `agents/base.py` | ✅ Complete | BaseAgent, AgentResult dataclasses |
| `agents/sourcing_agent.py` | ✅ Complete | Mock product sourcing |
| `agents/listing_agent.py` | ✅ Complete | Mock listing creation |
| `agents/fulfillment_agent.py` | ✅ Complete | Mock fulfillment with tracking |
| `config.py` | ✅ Complete | Env-based config loader |
| `exceptions.py` | ✅ Complete | Custom exception hierarchy |
| `intent_parser/parser.py` | ✅ Complete | Regex-based intent parsing |
| `workflow/dag.py` | ✅ Complete | DAG with cycle detection, topological sort |
| `workflow/task.py` | ✅ Complete | Task model with status management |

### Incomplete / Missing Modules
| Module | Priority | Description |
|--------|----------|-------------|
| `workflow/engine.py` | 🔴 Critical | WorkflowEngine — executes DAG tasks, manages state |
| `workflow/dsl.py` | 🔴 Critical | DSL for defining workflows declaratively |
| `orchestrator/orchestrator.py` | 🔴 Critical | Orchestrator — ties parser + agents + workflow together |
| `config/config.py` | 🟡 Medium | Config subpackage (seems duplicate of root config.py) |
| `integrations/supplier/` | 🟡 Medium | Supplier adapter interfaces |
| `integrations/storefront/` | 🟡 Medium | Storefront adapter interfaces |
| `cli/` | 🟢 Low | CLI subpackage (seems empty) |
| `__init__.py` files | 🟢 Low | Package init files for integrations |

## Implementation Tasks

### Phase 1: Core Engine (Critical Path)

#### Task 1.1: `workflow/engine.py` — WorkflowEngine
**Purpose:** Execute the DAG, manage task state, handle retries and errors.

**Key responsibilities:**
- Initialize from DAG + task definitions
- Execute tasks in topological order
- Handle task failures with retry logic
- Propagate data between tasks (task outputs → next task inputs)
- Provide execution status and results

**API Design:**
```python
class WorkflowEngine:
    def __init__(self, dag: DAG, config: Optional[Dict] = None): ...
    def execute(self) -> WorkflowExecutionResult: ...
    def execute_task(self, task_id: str) -> TaskResult: ...
    def get_status(self) -> Dict: ...
    def get_execution_log(self) -> List[Dict]: ...
```

**Implementation approach:**
- Use the DAG's `topological_sort()` to determine execution order
- For each task, instantiate the appropriate agent (SourcingAgent, ListingAgent, FulfillmentAgent)
- Pass data between tasks via a shared context dict
- Track execution log with timestamps and results

#### Task 1.2: `workflow/dsl.py` — Workflow DSL
**Purpose:** Declarative workflow definition language.

**Key responsibilities:**
- Define workflow steps with dependencies
- Map steps to agent types
- Generate DAG from DSL definition

**API Design:**
```python
class WorkflowDSL:
    def __init__(self): ...
    def add_step(self, name: str, agent_type: str, dependencies: List[str] = None, **kwargs) -> "WorkflowDSL": ...
    def build(self) -> Tuple[DAG, Dict[str, Dict]]: ...
    def to_dict(self) -> Dict: ...
    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowDSL": ...
```

**Implementation approach:**
- Builder pattern for fluent API
- `build()` creates DAG nodes and edges from the DSL definition
- Support default workflow templates (e.g., `dropshipping_workflow()`)

#### Task 1.3: `orchestrator/orchestrator.py` — Orchestrator
**Purpose:** High-level coordinator that ties everything together.

**Key responsibilities:**
- Parse user intent → BusinessSpec
- Configure agents based on spec
- Build and execute workflow
- Return comprehensive results

**API Design:**
```python
class Orchestrator:
    def __init__(self, config: Optional[Config] = None): ...
    def setup_business(self, description: str) -> BusinessSpec: ...
    def run_full_workflow(self, spec: Optional[BusinessSpec] = None) -> AgentResult: ...
    def source_products(self, spec: BusinessSpec) -> AgentResult: ...
    def create_listings(self, spec: BusinessSpec, products: List[Dict]) -> AgentResult: ...
    def fulfill_orders(self, spec: BusinessSpec, orders: List[Dict]) -> AgentResult: ...
```

**Implementation approach:**
- Use IntentParser to parse descriptions
- Configure agents based on BusinessSpec fields
- Use WorkflowEngine for orchestration
- Return structured results

### Phase 2: Integration Layer

#### Task 2.1: `integrations/supplier/` — Supplier Adapters
**Purpose:** Interface for connecting to real supplier platforms.

**Key responsibilities:**
- Define adapter interface (ABC)
- Implement AliExpress adapter (mock for now)
- Implement Spocket adapter (mock for now)

**API Design:**
```python
class SupplierAdapter(ABC):
    @abstractmethod
    def search_products(self, niche: str, **kwargs) -> List[Dict]: ...
    @abstractmethod
    def get_product(self, product_id: str) -> Dict: ...
    @abstractmethod
    def place_order(self, product_id: str, quantity: int, shipping_info: Dict) -> Dict: ...

class AliExpressAdapter(SupplierAdapter): ...
class SpocketAdapter(SupplierAdapter): ...
```

#### Task 2.2: `integrations/storefront/` — Storefront Adapters
**Purpose:** Interface for connecting to real storefront platforms.

**Key responsibilities:**
- Define adapter interface (ABC)
- Implement Shopify adapter (mock for now)
- Implement WooCommerce adapter (mock for now)

**API Design:**
```python
class StorefrontAdapter(ABC):
    @abstractmethod
    def create_product(self, product: Dict) -> Dict: ...
    @abstractmethod
    def update_product(self, product_id: str, updates: Dict) -> Dict: ...
    @abstractmethod
    def delete_product(self, product_id: str) -> bool: ...
    @abstractmethod
    def get_products(self, **kwargs) -> List[Dict]: ...

class ShopifyAdapter(StorefrontAdapter): ...
class WooCommerceAdapter(StorefrontAdapter): ...
```

### Phase 3: Polish & Testing

#### Task 3.1: Package Structure
- Add `__init__.py` files to all packages
- Create proper package exports
- Ensure CLI works with `python -m agentflow_drophip`

#### Task 3.2: Testing
- Unit tests for IntentParser
- Unit tests for DAG (cycle detection, topological sort)
- Unit tests for WorkflowEngine
- Integration tests for Orchestrator
- Mock supplier/storefront adapters

#### Task 3.3: Documentation
- Add docstrings to all public APIs
- Create README with usage examples
- Add type hints throughout

## File Structure After Implementation

```
agentflow_drophip/
├── __init__.py
├── config.py                    # Config loader
├── exceptions.py                # Custom exceptions
├── models/
│   ├── __init__.py
│   └── business_spec.py         # Pydantic models
├── agents/
│   ├── __init__.py
│   ├── base.py                  # BaseAgent, AgentResult
│   ├── sourcing_agent.py        # SourcingAgent
│   ├── listing_agent.py         # ListingAgent
│   └── fulfillment_agent.py     # FulfillmentAgent
├── intent_parser/
│   ├── __init__.py
│   └── parser.py                # IntentParser
├── workflow/
│   ├── __init__.py
│   ├── dag.py                   # DAG, Node, Edge
│   ├── task.py                  # Task, TaskResult, TaskStatus
│   ├── engine.py                # WorkflowEngine (NEW)
│   └── dsl.py                   # WorkflowDSL (NEW)
├── orchestrator/
│   ├── __init__.py
│   └── orchestrator.py          # Orchestrator (NEW)
├── integrations/
│   ├── __init__.py
│   ├── supplier/
│   │   ├── __init__.py
│   │   ├── base.py              # SupplierAdapter ABC
│   │   ├── aliexpress.py        # AliExpressAdapter
│   │   └── spocket.py           # SpocketAdapter
│   └── storefront/
│       ├── __init__.py
│       ├── base.py              # StorefrontAdapter ABC
│       ├── shopify.py           # ShopifyAdapter
│       └── woocommerce.py       # WooCommerceAdapter
├── cli/
│   ├── __init__.py
│   └── main.py                  # CLI commands
└── tests/
    ├── __init__.py
    ├── test_intent_parser.py
    ├── test_dag.py
    ├── test_workflow_engine.py
    ├── test_orchestrator.py
    └── test_agents.py
```

## Implementation Order

1. **workflow/engine.py** — Core execution engine
2. **workflow/dsl.py** — Declarative workflow definition
3. **orchestrator/orchestrator.py** — High-level coordinator
4. **integrations/supplier/base.py** — Supplier adapter interface
5. **integrations/storefront/base.py** — Storefront adapter interface
6. **Package structure** — `__init__.py` files, CLI setup
7. **Testing** — Unit and integration tests
8. **Documentation** — Docstrings, README

## Key Design Decisions

1. **Mock-first approach:** All integrations start as mocks for testing, with real implementations behind feature flags
2. **DAG-based execution:** Uses topological sort for deterministic task ordering
3. **Pydantic models:** Type-safe data structures for BusinessSpec
4. **Builder pattern:** For WorkflowDSL and agent configuration
5. **Exception hierarchy:** Custom exceptions for clear error handling
