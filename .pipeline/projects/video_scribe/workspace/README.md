# Video Scribe

Translate videos into rich, structured scene descriptions powered by an LLM.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Set your API key
export OPENAI_API_KEY="your-key-here"

# Analyze a video (outputs to stdout)
python video_scribe.py input.mp4

# Analyze and save to a file
python video_scribe.py input.mp4 --output description.md

# Use Claude instead of GPT-4o
export ANTHROPIC_API_KEY="your-key-here"
python video_scribe.py input.mp4 --provider claude
```

## Configuration

API keys can be set via environment variables or a `.env` file:

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Output Format

The output is a markdown document with the following sections:

- **Scene Content** — Summary of what happens in the scene
- **Visual Elements** — Objects, people, colors, and composition details
- **Camera Position/Angle** — Camera techniques (pan, tilt, zoom, etc.)
- **Lighting & Color** — Lighting conditions and color palette notes

## Project Structure

```
video_scribe/
├── __init__.py
├── cli.py          # CLI entry point and argument parsing
├── config.py       # Configuration and API key loading
├── frame_extractor.py  # Frame extraction and key frame selection
├── vlm_analyzer.py     # VLM integration for frame analysis
├── output_formatter.py # Markdown output formatting
tests/
└── test_pipeline.py    # End-to-end smoke test
```
