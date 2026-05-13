# FFO — Football Financial Optimizer

> **Football Financial Optimizer**: Player valuation and salary cap optimization for football (soccer) clubs.

FFO helps football clubs optimize their roster by evaluating player value scores and recommending roster changes within salary cap constraints. It uses a cost-effectiveness model that considers player rating, salary, age, and contract length.

## Features

- **Player Valuation**: Score players based on cost-effectiveness (rating/salary ratio, age factor, contract factor).
- **Salary Cap Management**: Track payroll and enforce salary cap limits.
- **Free Agent Pool**: Filter and rank available free agents by position, rating, and budget.
- **Roster Optimization**: Greedy algorithm to maximize total team value within cap constraints.
- **CLI Interface**: Command-line tools for batch processing and reporting.
- **JSON I/O**: Load and save roster and pool data in JSON format.

## Installation

```bash
pip install ffo
```

Or install from source:

```bash
git clone <repo-url>
cd ffo
pip install -e .
```

## Quick Start

### Command-Line Interface

```bash
# Create sample data
python -m ffo.cli create-sample-data

# Optimize a roster
python -m ffo.cli optimize \
    --roster roster.json \
    --pool pool.json \
    --cap 100000000

# Generate a detailed report
python -m ffo.cli report \
    --roster roster.json \
    --pool pool.json \
    --cap 100000000 \
    --output report.json
```

### Python API

```python
from ffo.api import optimize, generate_report

# From JSON files
report = generate_report(
    roster_path="roster.json",
    pool_path="pool.json",
    cap=100000000,
    age_weight=1.0,
    contract_weight=1.0,
)

print(f"Value improvement: {report['optimized_value'] - report['original_value']:.2f}")
```

### Programmatic Usage

```python
from ffo.models.player import Player, FreeAgent
from ffo.models.salary_cap import SalaryCap
from ffo.models.free_agent_pool import FreeAgentPool
from ffo.optimizer import optimize_roster
from ffo.models.valuation import value_player

# Build roster
roster = [
    Player(name="Player A", position="FWD", overall_rating=85.0,
           age=28, contract_length=3, salary=15000000, value=70000000),
]

# Build pool
pool = FreeAgentPool([
    FreeAgent(name="Agent X", position="FWD", overall_rating=90.0,
              age=24, contract_length=5, salary=18000000, value=80000000,
              available=True, agent_name="EliteAgents", preferred_positions=["FWD"]),
])

# Optimize
cap = SalaryCap(cap_limit=100000000)
optimized = optimize_roster(roster, cap, pool)

# Calculate value
total_value = sum(value_player(p) for p in optimized)
```

## Project Structure

```
ffo/
├── __init__.py          # Package init, version
├── api.py               # Public API (optimize, generate_report)
├── cli.py               # CLI entry point
├── io_utils.py          # JSON load/save utilities
├── models/
│   ├── __init__.py
│   ├── player.py        # Player, FreeAgent models
│   ├── salary_cap.py    # SalaryCap model
│   ├── free_agent_pool.py  # FreeAgentPool model
│   └── valuation.py     # Value calculation functions
├── optimizer.py         # Roster optimization algorithm
├── tests/
│   ├── __init__.py
│   ├── conftest.py      # Shared test fixtures
│   ├── test_player.py
│   ├── test_salary_cap.py
│   ├── test_free_agent_pool.py
│   ├── test_valuation.py
│   ├── test_optimizer.py
│   ├── test_io_utils.py
│   └── test_api.py
├── examples/
│   ├── optimize_roster.py
│   ├── programmatic_api.py
│   ├── cli_usage.py
│   └── create_sample_data.py
├── pyproject.toml       # Project metadata
├── README.md
└── LICENSE
```

## Valuation Model

The value score for a player is calculated as:

```
value_score = (overall_rating / salary) * age_factor * contract_factor
```

Where:
- **overall_rating**: Player's overall rating (0-100)
- **salary**: Annual salary in dollars
- **age_factor**: 1.0 for ages 25-30, decreasing for older/younger players
- **contract_factor**: 1.0 for contracts of 3+ years, decreasing for shorter contracts

Higher value scores indicate better cost-effectiveness.

## Optimization Algorithm

The optimizer uses a greedy approach:

1. Calculate value scores for all current roster players and free agent candidates.
2. Rank all candidates by value score (descending).
3. Iterate through ranked candidates, adding them to the new roster if:
   - The player's position fills a needed position (or replaces a lower-value player in the same position).
   - The salary cap is not exceeded.
4. Return the optimized roster with the highest total value score within the cap.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ffo --cov-report=term-missing

# Run specific test file
pytest tests/test_optimizer.py
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please submit pull requests or open issues on GitHub.

## Acknowledgments

- Inspired by real-world football club financial management challenges.
- Valuation model based on cost-effectiveness principles from sports economics.
