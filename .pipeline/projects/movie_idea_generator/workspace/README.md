# Movie Idea Generator

A rule-based movie idea generator that produces creative movie concepts using templates and randomization.

## Installation

### From PyPI

```bash
pip install movie-idea-generator
```

### From Source

```bash
git clone <repository-url>
cd movie_idea_generator
pip install -e .
```

### Development Dependencies

```bash
pip install pytest  # for running tests
```

No other dependencies required. The generator uses only Python standard library modules.

For detailed build, test, and publish instructions, see [docs/deployment.md](docs/deployment.md).

## Usage

### CLI

Generate a single movie idea:

```bash
python -m movie_idea_generator
```

Generate multiple ideas:

```bash
python -m movie_idea_generator --count 5
```

Filter by genre:

```bash
python -m movie_idea_generator --genre Horror
```

Output as JSON:

```bash
python -m movie_idea_generator --format json
```

Combine flags:

```bash
python -m movie_idea_generator --genre Sci-Fi --count 3 --format json --seed 42
```

### CLI Flags

| Flag | Short | Description | Default |
|------|-------|-------------|---------|
| `--genre` | `-g` | Filter by genre (e.g. Action, Comedy, Drama, Horror, Sci-Fi, Romance, Thriller, Fantasy, Mystery, Adventure) | None (random) |
| `--count` | `-n` | Number of ideas to generate | 1 |
| `--format` | `-f` | Output format: `text` or `json` | text |
| `--seed` | | Random seed for reproducibility | None |

### Programmatic API

```python
from movie_idea_generator import MovieIdeaGenerator

# Create a generator (optional seed for reproducibility)
gen = MovieIdeaGenerator(seed=42)

# Generate a single idea
idea = gen.generate()
print(idea["title"])
print(idea["genre"])
print(idea["logline"])

# Generate with a specific genre
horror_idea = gen.generate(genre="Horror")

# Generate a batch of ideas
ideas = gen.generate_batch(count=5, genre="Comedy")

# Each idea is a dict:
# {
#   "title": "The Last Horizon",
#   "genre": "Comedy",
#   "logline": "The Last Horizon: A detective accidentally becomes the detective of a small coastal town.",
#   "characters": [
#     {"name": "Alex Mercer", "description": "A dangerous detective who is save the world.", "role": "protagonist"},
#     ...
#   ]
# }
```

## Available Genres

The generator supports 10 genres:

- **Action** — High-stakes physical confrontations
- **Comedy** — Humorous situations and witty dialogue
- **Drama** — Emotional, character-driven stories
- **Horror** — Fear-inducing, supernatural or psychological terror
- **Sci-Fi** — Futuristic, technological, or space-themed concepts
- **Romance** — Love stories and relationships
- **Thriller** — Suspenseful, tension-filled narratives
- **Fantasy** — Magical worlds and mythical creatures
- **Mystery** — Puzzles, investigations, and hidden truths
- **Adventure** — Journeys, exploration, and discovery

## Output Format

### Text (default)

```
🎬 The Last Horizon
   Genre: Action
   Logline: The Last Horizon: A detective must save the world before time runs out.
   Characters:
     • Alex Mercer (protagonist) — A dangerous detective who is save the world.
     • Jordan Blake (ally) — A brilliant chef who is find the truth.
     • Sam Rivera (mentor) — A desperate soldier who is expose the truth.
```

### JSON

```json
{
  "title": "The Last Horizon",
  "genre": "Action",
  "logline": "The Last Horizon: A detective must save the world before time runs out.",
  "characters": [
    {
      "name": "Alex Mercer",
      "description": "A dangerous detective who is save the world.",
      "role": "protagonist"
    }
  ]
}
```

## Error Handling

The generator validates inputs and raises `ValueError` with descriptive messages:

```python
from movie_idea_generator import MovieIdeaGenerator

gen = MovieIdeaGenerator()

# Invalid genre
gen.generate(genre="ZombiePunk")
# ValueError: Invalid genre: 'ZombiePunk'. Must be one of: Action, Comedy, ...

# Negative count
gen.generate_batch(count=-1)
# ValueError: count must be >= 0, got -1

# Zero count returns empty list
gen.generate_batch(count=0)
# []
```

## Running Tests

```bash
cd /workspace/idea impl/.pipeline/projects/movie_idea_generator/workspace
pytest test_movie_idea_generator.py test_cli.py -v
```

## Contributing

Contributions are welcome! Please ensure all tests pass before submitting changes:

```bash
pytest -v
```

### Adding a New Genre

1. Add the genre name to the `GENRES` list in `generator.py`.
2. Add template strings to `GENRE_TEMPLATES` for the new genre.
3. Add any new data pools (e.g., `NEW_ELEMENTS`) if needed.
4. Update the README with the new genre.
