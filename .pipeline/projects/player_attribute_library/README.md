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

## API Reference

### `create_player(name: str, **attrs: float) -> PlayerAttribute`

Create a new player record. Accepts optional attribute overrides.

**Valid attributes:** `speed`, `shooting`, `passing`, `defending`, `physical`, `mental`

**Raises:**
- `ValueError` if name is empty or whitespace-only
- `ValueError` if an unknown attribute name is provided
- `TypeError` if an attribute value is not a number

### `get_attribute(player: PlayerAttribute, attr_name: str) -> float`

Retrieve a single attribute value from a player record.

**Raises:**
- `TypeError` if player is not a PlayerAttribute instance
- `KeyError` if attr_name is not a valid attribute

### `get_all_attributes(player: PlayerAttribute) -> dict`

Return a dictionary of all attribute values for a player.

**Raises:**
- `TypeError` if player is not a PlayerAttribute instance

### `match_players(target: PlayerAttribute, candidates: Iterable[PlayerAttribute], *, metric: str = "cosine", top_n: Optional[int] = None) -> List[dict]`

Match a target player profile against a list of candidates.

**Parameters:**
- `target`: The reference player profile
- `candidates`: Iterable of PlayerAttribute objects to compare against
- `metric`: Either `"cosine"` (higher is better) or `"euclidean"` (inverted, higher is better)
- `top_n`: If provided, return only the top N matches

**Returns:**
- List of dicts: `[{"player": PlayerAttribute, "score": float}, ...]` sorted by best match first

**Raises:**
- `TypeError` if target or any candidate is not a PlayerAttribute instance
- `ValueError` if metric is not "cosine" or "euclidean"
- `ValueError` if top_n is not a positive integer

## Development

Run tests:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```
