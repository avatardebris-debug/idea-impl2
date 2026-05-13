# Player Attribute Library

A Python library for creating, querying, and matching football (soccer) player attribute profiles.

## Installation

```bash
pip install player_attribute_library
```

## Quick Start

```python
from player_attribute_library.core import (
    create_player,
    get_attribute,
    get_all_attributes,
    match_players,
)

# Create a player
messi = create_player("Messi", speed=85, shooting=95, passing=93, defending=35, physical=65, mental=95)

# Get a single attribute
print(get_attribute(messi, "shooting"))  # 95.0

# Get all attributes
print(get_all_attributes(messi))
# {'speed': 85.0, 'shooting': 95.0, 'passing': 93.0, 'defending': 35.0, 'physical': 65.0, 'mental': 95.0}
```

## Matching Players

Find players similar to a target profile using cosine similarity or Euclidean distance:

```python
from player_attribute_library.core import create_player, match_players

# Create a target profile (e.g., a fast, attacking winger)
target = create_player("Target", speed=95, shooting=88, passing=80, defending=30, physical=60, mental=85)

# Create candidate players
c1 = create_player("Player A", speed=92, shooting=85, passing=78, defending=32, physical=58, mental=82)
c2 = create_player("Player B", speed=70, shooting=95, passing=90, defending=50, physical=80, mental=90)
c3 = create_player("Player C", speed=94, shooting=90, passing=82, defending=28, physical=62, mental=87)

# Match using cosine similarity (default)
results = match_players(target, [c1, c2, c3], metric="cosine", top_n=2)
for r in results:
    print(f"{r['player'].name}: {r['score']}")
# Player C: 0.9987
# Player A: 0.9856

# Match using Euclidean distance
results = match_players(target, [c1, c2, c3], metric="euclidean", top_n=2)
for r in results:
    print(f"{r['player'].name}: {r['score']}")
# Player C: 0.9891
# Player A: 0.9756
```

## CLI Usage

The library includes a command-line interface:

```bash
# Create a player and save to JSON
python -m player_attribute_library.cli create \
    --name "Ronaldo" \
    --speed 88 --shooting 95 --passing 80 --defending 40 --physical 75 --mental 90 \
    --output player.json

# Match players
python -m player_attribute_library.cli match \
    --target-file target.json \
    --candidates-file candidates.json \
    --output matches.json

# List all players in a file
python -m player_attribute_library.cli list --file players.json
```

## Serialization

Players can be serialized to and loaded from JSON:

```python
from player_attribute_library import save_players, load_players

# Save
players = [create_player("P1", speed=80, shooting=80, passing=80, defending=80, physical=80, mental=80)]
save_players(players, "players.json")

# Load
loaded = load_players("players.json")
```

## Development

### Setup

```bash
cd workspace
pip install -e ".[dev]"
pre-commit install
```

### Running Tests

```bash
pytest
```

### Building

```bash
python -m build
```

### Docker

```bash
docker build -t player-attribute-library .
docker run player-attribute-library python -m player_attribute_library.demo
```

## Project Structure

```
player_attribute_library/
├── pyproject.toml          # Project metadata, dependencies, CLI entry point
├── README.md               # This file
├── CHANGELOG.md            # Version history
├── LICENSE                 # MIT License
├── Dockerfile              # Container build instructions
├── .gitignore              # Git ignore rules
├── .pre-commit-config.yaml # Pre-commit hooks
├── player_attribute_library/
│   ├── __init__.py         # Package init, exports
│   ├── models.py           # PlayerAttribute dataclass
│   ├── core.py             # Core functions (create, query, match, save/load)
│   ├── demo.py             # Demo script
│   └── tests/
│       ├── __init__.py
│       ├── test_models.py  # Unit tests for models
│       ├── test_core.py    # Unit tests for core functions
│       └── test_integration.py  # Integration / end-to-end tests
├── scripts/
│   └── cli.py              # CLI entry point
└── .github/
    └── workflows/
        └── ci.yml          # GitHub Actions CI/CD pipeline
```

## License

MIT
