## Phase 1 — Keyword Extraction Engine (MVP)

**Goal:** The smallest useful thing — extract and rank keywords from any transcript.

### Description

Build the core keyword extraction pipeline. This phase focuses on ingesting transcript files (SRT, VTT, TXT), cleaning the text, and producing a ranked list of relevant keywords/phrases with frequency scores. No show notes or platform output yet — just raw keyword intelligence.

This is the MVP because keyword extraction is the foundational capability everything else depends on. Without it, show notes and metadata have no data source.

### Deliverables

1. **`transcript_parser.py`** — Detects and parses SRT, VTT, TXT, and DOCX transcript formats into a unified text representation.
2. **`keyword_extractor.py`** — Applies TF-IDF + spaCy NER + custom stopword filtering to extract ranked keywords and keyphrases.
3. **`cli.py`** — CLI entry point: `podcastseo keywords input.srt --top 20 --output keywords.json`
4. **`keywords.json`** — Output format: `[{ "keyword": "...", "score": 0.95, "category": "topic/brand/tech", "occurrences": 12 }]`
5. **Unit tests** — For parser (all formats) and extractor (edge cases, empty input, special characters).

### Dependencies

- None. This is the foundation phase.

### Success Criteria

- [ ] Parses SRT, VTT, TXT, and DOCX transcripts without errors.
- [ ] Extracts at least 15 meaningful keywords from a 30-minute podcast transcript.
- [ ] Keyword scores correlate with human judgment (validated on 5 sample transcripts).
- [ ] CLI runs end-to-end: `podcastseo keywords sample.srt --top 20 --output out.json` produces valid JSON.
- [ ] All tests pass (`pytest`); coverage ≥ 80%.
- [ ] Processing time < 10 seconds for a 50,000-word transcript on a standard laptop.

---