# PodcastSEO Metadata Optimizer

An automation tool that extracts keywords from podcast transcripts, generates show notes, and produces platform-specific metadata for podcast distribution.

## Installation

```bash
pip install -e .
python -m spacy download en_core_web_sm
```

## Usage

### CLI

```bash
# Extract keywords from a transcript
podcastseo keywords sample.srt --top 20

# Output to a JSON file
podcastseo keywords sample.srt --top 20 --output keywords.json
```

### Programmatic API

```python
from podcastseo.transcript_parser import TranscriptParser
from podcastseo.keyword_extractor import KeywordExtractor

parser = TranscriptParser()
text = parser.parse("sample.srt")

extractor = KeywordExtractor()
keywords = extractor.extract(text)
```

## Supported Formats

- SRT (SubRip Subtitle)
- VTT (WebVTT)
- TXT (Plain text)
- DOCX (Microsoft Word)

## Output Schema

```json
[
  {
    "keyword": "example",
    "score": 0.95,
    "category": "topic",
    "occurrences": 12
  }
]
```

## License

MIT
