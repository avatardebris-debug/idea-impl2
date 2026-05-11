# AI Movie Gen Suite

Generate screenplays with AI.

## Quick Start

```bash
# Install
pip install -e .

# Generate a screenplay
python -m ai_movie_gen_suite.cli \
    --title "The Last Light" \
    --logline "A lighthouse keeper discovers a secret that could change the world" \
    --genre "Drama" \
    --tone "dark"
```

## Output Formats

- `json` (default) — Structured JSON
- `yaml` — Human-readable YAML
- `fdx` — Final Draft XML

## Pipeline Stages

1. **Beat Generator** — Save-the-Cat beat sheet
2. **Character Generator** — Character profiles
3. **Script Writer** — Full screenplay
4. **Scene Description Engine** — Visual descriptions
5. **Formatter** — JSON/YAML/FDX output
