# extraction

Turn source material (articles, transcripts, how-to guides, SOPs) into a structured recipe or step-by-step sequence.

## Overview

`extraction` is a Python library and CLI tool that extracts structured, ordered steps from unstructured text. It uses an LLM (via [Ollama](https://ollama.com/)) for intelligent extraction, with a rule-based fallback when the LLM is unavailable.

**Supported input types:** cooking recipes, how-to guides, SOPs, tutorials, processes, instructions.

**Output:** A JSON object with `title`, `topic`, `format`, `description`, `components`, `steps`, `tips`, and `metadata`.

## Installation

### From source

```bash
cd /workspace/idea\ impl/.pipeline/projects/extraction/workspace
pip install -e .
```

### Dev dependencies

```bash
pip install -e ".[dev]"
```

## Ollama Dependency

By default, `extraction` uses Ollama (running locally) for LLM-powered extraction.

1. [Install Ollama](https://ollama.com/)
2. Pull a model (e.g., `ollama pull qwen3:6b`)
3. Ensure Ollama is running on `http://localhost:11434`

If Ollama is unavailable, the tool automatically falls back to a rule-based extraction engine.

## CLI Usage

### Basic usage (file input)

```bash
python -m extraction article.txt --topic "how to make sourdough" --format recipe
```

### Format choices

```bash
# Recipe format (with ingredients/components)
python -m extraction recipe.txt --format recipe

# Steps format (ordered instructions)
python -m extraction guide.txt --format steps

# SOP format (Standard Operating Procedure)
python -m extraction process.txt --format sop
```

### Output to file

```bash
python -m extraction article.txt --format steps --output output.json
```

### Pretty-print JSON

```bash
python -m extraction article.txt --format steps --pretty
```

### Use rule-based extraction (no Ollama)

```bash
python -m extraction article.txt --no-llm --format steps
```

### Pipe from stdin

```bash
cat transcript.txt | python -m extraction - --format sop
```

### Specify a custom Ollama model

```bash
python -m extraction article.txt --model "llama3" --format steps
```

### Full example

```bash
python -m extraction my_article.txt \
    --topic "how to bake sourdough bread" \
    --format recipe \
    --output sourdough.json \
    --pretty
```

## Python API Usage

```python
from extraction import extract

result = extract(
    text="First, mix the flour and water. Then let it rest for 30 minutes.",
    topic="sourdough starter",
    fmt="recipe",
    model="qwen3:6b",
)

print(result["title"])       # "Sourdough Starter Guide"
print(result["format"])      # "recipe"
print(result["steps"])       # [{"step_number": 1, "action": "...", ...}]
print(result["metadata"])    # {"source_length": ..., "model": ..., "extracted_at": ...}
```

### Fallback extraction

```python
from extraction import _fallback_extract

result = _fallback_extract(
    text="Step one. Step two. Step three.",
    topic="manual process",
    fmt="sop",
)
```

## Output Schema

```json
{
  "title": "Concise title of the extracted procedure",
  "topic": "Topic description (inferred or provided)",
  "format": "recipe | steps | sop",
  "description": "One-sentence overview",
  "components": [
    {
      "name": "ingredient/component name",
      "quantity": "amount",
      "unit": "unit of measure",
      "notes": "optional notes"
    }
  ],
  "steps": [
    {
      "step_number": 1,
      "action": "Short verb phrase describing the step",
      "detail": "Full description of the step",
      "duration": "Time if applicable (e.g., '10 minutes')",
      "tools": ["tool1", "tool2"],
      "warnings": ["warning if any"]
    }
  ],
  "tips": ["tip1", "tip2"],
  "metadata": {
    "source_length": 1234,
    "model": "qwen3:6b",
    "extracted_at": "2025-01-01T00:00:00+00:00"
  }
}
```

### Schema Notes

- `components` is populated for `recipe` format (ingredients).
- `steps` are always numbered starting from 1.
- `metadata.model` is `"fallback"` when rule-based extraction is used.
- All fields are guaranteed to be present (defaults applied automatically).

## Development & Testing

### Running tests

```bash
cd /workspace/idea\ impl/.pipeline/projects/extraction/workspace
pytest
```

### Test files

| File | Coverage |
|------|----------|
| `tests/test_fallback.py` | Rule-based extraction engine |
| `tests/test_cli.py` | CLI argument parsing, validation, output |
| `tests/test_json_parsing.py` | JSON extraction edge cases |
| `tests/test_extract.py` | LLM extraction path (mocked) |
| `tests/test_integration.py` | End-to-end pipeline tests |

### Project structure

```
workspace/
├── extraction/
│   ├── __init__.py      # Public API (extract, _fallback_extract)
│   ├── __main__.py      # CLI entry point
│   ├── cli.py           # CLI argument parsing and validation
│   └── extractor.py     # Core extraction engine
├── tests/
│   ├── test_fallback.py
│   ├── test_cli.py
│   ├── test_json_parsing.py
│   ├── test_extract.py
│   └── test_integration.py
├── pyproject.toml
└── README.md
```

### Adding new tests

1. Create a test file in `tests/`
2. Use `pytest` classes with descriptive method names
3. Run `pytest -v` to verify

## License

MIT
