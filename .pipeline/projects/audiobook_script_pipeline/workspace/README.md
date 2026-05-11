# Audiobook Script Pipeline

A Python tool that converts plain-text manuscripts into formatted audio scripts with pacing markers, ready for Text-to-Speech (TTS) consumption.

## Overview

The Audiobook Script Pipeline parses manuscript files (plain text with chapter headings) and produces structured audio scripts with:

- **[PAUSE: Ns]** — Natural breaks between sentences/paragraphs
- **[EMPHASIS]** — Key terms detected via capitalization patterns or proper nouns
- **[SLOW]** / **[FAST]** — Tempo changes at section boundaries
- **Chapter structure** — Preserved from the original manuscript

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd audiobook_script_pipeline

# Install dependencies
pip install -r requirements.txt
```

## Usage

### CLI

```bash
# Basic usage — prints to stdout
python audiobook_script_pipeline/cli.py manuscript.txt

# Save to a file
python audiobook_script_pipeline/cli.py manuscript.txt -o output.txt

# Custom pause duration (default: 1.0s)
python audiobook_script_pipeline/cli.py manuscript.txt --pause 2.0
```

### Python API

```python
from audiobook_script_pipeline.pipeline.script_pipeline import ScriptPipeline

# Create pipeline with custom pause duration
pipeline = ScriptPipeline(default_pause=2.0)

# Run from a file
audio_script = pipeline.run("manuscript.txt")

# Or run from raw text
audio_script = pipeline.run_from_text("# Chapter One\n\nHello world.")

# Format to string
output = pipeline.formatter.format_to_string(audio_script)
print(output)
```

## Manuscript Format

The pipeline expects manuscripts in plain text format with chapter headings. It supports two heading styles:

### Style 1: Markdown-style headings

```
# Chapter One

Some text here.

# Chapter Two

More text.
```

### Style 2: "Chapter N" headings

```
Chapter 1: The Beginning

Some text here.

Chapter 2: The Journey

More text.
```

### Mixed headings

Both styles can be mixed:

```
# Introduction

Intro text.

Chapter 2: Middle

Middle text.

# Conclusion

End text.
```

### No headings

If no chapter headings are detected, the entire text is wrapped in a single "Untitled" chapter.

## Output Format

The output is a structured audio script with pacing markers:

```
=== Chapter One ===
--- Chapter One ---
[SLOW] Chapter One [/SLOW]
[PAUSE: 1.5s]
Hello world.
[PAUSE: 1.5s]
This is a test.
[PAUSE: 1.5s]
[FAST] [/FAST]
--- Chapter Two ---
[SLOW] Chapter Two [/SLOW]
[PAUSE: 1.5s]
Another chapter here.
[PAUSE: 1.5s]
[FAST] [/FAST]
```

## Architecture

```
audiobook_script_pipeline/
├── cli.py                          # CLI entry point
├── pipeline/
│   ├── script_pipeline.py          # Pipeline orchestrator
│   └── __init__.py
├── parser/
│   ├── manuscript_parser.py        # Manuscript parsing logic
│   └── __init__.py
├── formatter/
│   ├── audio_formatter.py          # Audio script formatting logic
│   └── __init__.py
├── tests/
│   ├── manuscript_parser_test.py   # Unit tests for parser
│   ├── audio_formatter_test.py     # Unit tests for formatter
│   ├── pipeline_test.py            # Unit tests for pipeline
│   └── cli_integration_test.py     # CLI integration tests
├── requirements.txt
├── README.md
└── __init__.py
```

### Components

1. **ManuscriptParser** — Parses manuscript text into structured chapters with titles, bodies, and sentences.
2. **AudioScriptFormatter** — Adds pacing markers, emphasis, and tempo changes to chapter data.
3. **ScriptPipeline** — Orchestrates the parsing and formatting steps.
4. **CLI** — Command-line interface for end users.

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/manuscript_parser_test.py
pytest tests/audio_formatter_test.py
pytest tests/pipeline_test.py
pytest tests/cli_integration_test.py
```

## Error Handling

The pipeline handles the following error cases:

- **File not found**: Returns exit code 1 with error message
- **Empty manuscript**: Returns exit code 1 with error message
- **Invalid input**: Raises appropriate exceptions with descriptive messages

## License

MIT License

## Contributing

Contributions are welcome! Please submit pull requests or open issues for bugs and feature requests.

## Acknowledgments

Built with Python 3.10+ and standard library modules.
