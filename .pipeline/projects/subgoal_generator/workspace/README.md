# Subgoal Generator

A general-purpose LLM goal decomposition engine. Takes any high-level goal ("build a house", "make $10k/month", "learn Spanish") and uses an LLM to produce an ordered list of subgoals with dependencies. Each subgoal is formatted as a pipeline idea entry and injected into `master_ideas.md` for the runner to execute.

## Features

- **Domain-agnostic**: Works with any goal — robotics, software, business, personal development
- **Dependency-aware**: Subgoals include dependency lists for correct execution order
- **Priority-ranked**: Each subgoal has a priority score for scheduling
- **Pipeline-ready**: Outputs are formatted as YAML entries for `master_ideas.md`
- **Provider-agnostic**: Supports any OpenAI-compatible API (OpenAI, Ollama, vLLM, etc.)
- **Fully tested**: Comprehensive test suite covering models, parser, prompt builder, output, and integration

## Quick Start

```bash
# Install dependencies
pip install openai pyyaml

# Run the generator
python -m subgoal_generator.main "Build a web application"
```

This will:
1. Build a prompt for the LLM
2. Call the LLM to decompose the goal
3. Parse the response into structured subgoals
4. Append each subgoal to `master_ideas.md`

## Usage

### Programmatic

```python
from subgoal_generator.generator import SubgoalGenerator
from subgoal_generator.llm_client import LLMClient

# Create an LLM client
client = LLMClient(
    provider="openai",
    api_key="your-api-key",
    model="gpt-4o-mini",
)

# Create the generator
generator = SubgoalGenerator(llm_client=client)

# Generate subgoals
subgoals = generator.generate(
    goal="Build a SaaS product",
    output_path="master_ideas.md",
)

for sg in subgoals:
    print(f"{sg.title}: {sg.description} (priority={sg.priority})")
```

### Custom LLM Provider

```python
client = LLMClient(
    provider="ollama",
    base_url="http://localhost:11434/v1",
    model="llama3",
)
```

### Models

```python
from subgoal_generator.models import Subgoal, DependencyGraph

# Create a subgoal
sg = Subgoal(
    title="Design database",
    description="Create schema for user data",
    dependencies=["Define requirements"],
    priority=3,
)

# Create a dependency graph
graph = DependencyGraph()
graph.add_subgoal(Subgoal(title="A", description="First"))
graph.add_subgoal(Subgoal(title="B", description="Second", dependencies=["A"]))
graph.validate()  # Raises ValueError if cycles or missing deps
order = graph.topological_sort()  # Returns subgoals in execution order
```

## Project Structure

```
subgoal_generator/
├── __init__.py
├── main.py              # CLI entry point
├── models.py            # Subgoal dataclass, DependencyGraph
├── parser.py            # Parse LLM text → Subgoal objects
├── prompt_builder.py    # Build LLM prompt from goal
├── llm_client.py        # LLM API abstraction
├── output.py            # Write pipeline entries to master_ideas.md
├── generator.py         # Core engine wiring everything together
└── tests/
    ├── test_models.py
    ├── test_parser.py
    ├── test_prompt_builder.py
    ├── test_output.py
    └── test_integration.py
```

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=subgoal_generator --cov-report=term-missing
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  High-Level  │────▶│  Prompt      │────▶│    LLM      │
│    Goal      │     │  Builder     │     │  Client     │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                  │
                                                  ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ master_ideas │◀────│  Output      │◀────│   Parser    │
│    .md       │     │  Formatter   │     │  Response   │
└─────────────┘     └──────────────┘     └─────────────┘
```

The `SubgoalGenerator` class is the central orchestrator:
1. `build_prompt(goal)` → structured prompt string
2. `llm_client.chat_completion(prompt)` → LLM text response
3. `parse_response(text)` → list of `Subgoal` objects
4. `write_pipeline_entries(subgoals)` → append to `master_ideas.md`

## License

MIT
