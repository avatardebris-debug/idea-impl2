# VideoPow

Convert text descriptions of video edits into actual video transformations.

## Quick Start

```bash
pip install -e .
python -m videopow --description "slow zoom on a forest" --input sample.mp4 --output result.mp4
```

## Usage

### Python API

```python
from videopow.pipeline import generate_video

generate_video(
    description="a sunset over the ocean with slow zoom",
    input_video_path="input.mp4",
    output_path="output.mp4",
)
```

### CLI

```bash
python -m videopow --description "slow zoom on a forest" --input sample.mp4 --output result.mp4
```

## Architecture

- `videopow.core` — `VideoProcessor` for loading, frame extraction, and video writing.
- `videopow.describer` — `VideoDescriber` for parsing text descriptions into structured editing instructions.
- `videopow.pipeline` — `generate_video()` end-to-end pipeline.
- `videopow.cli` — CLI entry point.
