# PodcastSEO Metadata Optimizer — Master Plan

## Overview

**Idea:** Build an automation tool that extracts keywords from podcast transcripts, generates show notes, and produces platform-specific metadata for podcast distribution.

**Core Deliverable:** A CLI + API tool that takes a podcast transcript as input and outputs SEO-optimized keywords, structured show notes, and platform-ready metadata (Apple Podcasts, Spotify, YouTube, etc.).

---

## Architecture Notes

```
┌─────────────────────────────────────────────────────────────┐
│                     PodcastSEO Optimizer                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │  Input   │──▶│  Keyword     │──▶│  Show Notes      │   │
│  │  Layer   │   │  Extractor   │   │  Generator       │   │
│  │          │   │  (Phase 1)   │   │  (Phase 2)       │   │
│  └──────────┘   └──────────────┘   └──────────────────┘   │
│       │                                                │   │
│       │         ┌──────────────┐                       │   │
│       └────────▶│  Metadata    │                       │   │
│                 │  Renderer    │                       │   │
│                 │  (Phase 3)   │                       │   │
│                 └──────────────┘                       │   │
│                                                        │   │
│  ┌──────────────────────────────────────────────────┐  │
│  │              Output Layer                        │  │
│  │  JSON / YAML / HTML / RSS-compatible XML         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Shared Services                        │  │
│  │  - NLP Pipeline (spaCy / transformers)           │  │
│  │  - Transcript Parser (SRT / VTT / TXT / DOCX)    │  │
│  │  - Config / Templates Engine                     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Tech Stack Recommendations:**
- **Language:** Python 3.11+
- **NLP:** spaCy (keyword extraction), HuggingFace transformers (optional LLM-based enhancement)
- **Transcript Parsing:** `webvtt-py`, `srt`, `python-docx`
- **Output:** Jinja2 templating, `pyyaml`, `jmespath`
- **CLI:** `click` or `typer`
- **Testing:** `pytest`

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| NLP keyword extraction quality is poor on domain-specific content | High | Start with rule-based + spaCy; add LLM fallback in Phase 3 |
| Transcript formats vary wildly (SRT, VTT, DOCX, audio-to-text API outputs) | Medium | Build a robust transcript parser with format detection in Phase 1 |
| Platform metadata requirements conflict or change frequently | Medium | Abstract platform configs behind a template engine; version the configs |
| LLM API costs for enhanced keyword extraction | Medium | Make LLM enhancement opt-in; default to open-source models |
| Long transcripts cause memory issues | Low | Implement chunked processing with overlap |

---

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

## Phase 2 — Show Notes Generator

**Goal:** Transform extracted keywords into structured, readable show notes.

### Description

Build on Phase 1's keyword output to generate human-readable, SEO-optimized show notes. This includes a structured template system that produces show notes with: episode summary, key takeaways, timestamps with keyword anchors, related topics, and a call-to-action section. Supports multiple output formats (Markdown, HTML, plain text).

### Deliverables

1. **`show_notes_generator.py`** — Takes keyword data + transcript text and generates structured show notes using a template engine.
2. **Template system** — Jinja2-based templates with:
   - Episode summary (auto-generated from top keywords + transcript context)
   - Key takeaways (bullet list from top-scoring keywords/phrases)
   - Timestamped keyword anchors (maps keywords to first occurrence in transcript)
   - Related topics / tags section
   - CTA placeholder
3. **Output formats** — Markdown (default), HTML, and plain text exporters.
4. **CLI extension** — `podcastseo notes input.srt --format markdown --output show_notes.md`
5. **Config file** — `config.yaml` for template customization (tone, length, section order).
6. **Integration tests** — End-to-end: transcript → keywords → show notes → file output.

### Dependencies

- **Phase 1** must be complete and stable. This phase consumes Phase 1's `keywords.json` output.

### Success Criteria

- [ ] Generates show notes from a Phase 1 keyword output in < 5 seconds.
- [ ] Output includes all required sections: summary, takeaways, timestamps, tags, CTA.
- [ ] Timestamps accurately reference transcript content (validated on 10 samples).
- [ ] Markdown output renders correctly in standard markdown viewers.
- [ ] HTML output is clean, semantic, and passes basic accessibility checks.
- [ ] Config-driven customization works (changing tone/length updates output).
- [ ] Integration tests pass end-to-end.

---

## Phase 3 — Platform-Specific Metadata Renderer

**Goal:** Produce distribution-ready metadata for each podcast platform.

### Description

Build the final output layer that transforms the show notes and keyword data into platform-specific metadata formats. Each platform has unique requirements (character limits, field structures, SEO best practices). This phase abstracts those differences behind a unified rendering engine.

### Deliverables

1. **`metadata_renderer.py`** — Core engine that takes show notes + keywords and renders platform-specific metadata.
2. **Platform profiles** — Configurable profiles for:
   - **Apple Podcasts** — Title, subtitle, description (max 4,000 chars), category tags
   - **Spotify for Podcasters** — Title, description, episode type, explicit flag
   - **YouTube Podcasts** — Title (max 100 chars), description (SEO-optimized), tags
   - **RSS Feed** — `<itunes:subtitle>`, `<itunes:summary>`, `<itunes:keywords>`, `<media:tags>`
   - **Custom / Generic** — JSON output for programmatic use
3. **Template system** — Platform-specific Jinja2 templates with character-limit enforcement and SEO best practices baked in.
4. **SEO scoring** — Built-in SEO score for each platform output (keyword density, title length, description completeness).
5. **CLI extension** — `podcastseo metadata input.srt --platform apple,youtube --output ./metadata/`
6. **Batch mode** — Process an entire season's worth of transcripts in one run.
7. **Documentation** — Usage guide, platform config reference, SEO best practices guide.

### Dependencies

- **Phase 1** — Keyword extraction (data source).
- **Phase 2** — Show notes generation (structural input for metadata).

### Success Criteria

- [ ] Generates valid metadata for Apple Podcasts, Spotify, YouTube, and RSS within platform character/format limits.
- [ ] SEO scores are provided for each platform output and are actionable (≥ 70/100 target).
- [ ] Batch mode processes 10 episodes in < 60 seconds.
- [ ] All platform outputs pass validation (character limits, XML well-formedness for RSS).
- [ ] Documentation covers setup, usage, and customization.
- [ ] Full end-to-end pipeline: `podcastseo all input.srt --platforms apple,youtube,rss --output ./output/` works flawlessly.

---

## Phase Summary

| Phase | Scope | Deliverable | Dependencies |
|-------|-------|-------------|--------------|
| **1 — Keyword Engine** | MVP: Extract & rank keywords from transcripts | CLI tool that outputs ranked keywords in JSON | None |
| **2 — Show Notes** | Generate structured, timestamped show notes from keywords | Template-based show notes in Markdown/HTML/Text | Phase 1 |
| **3 — Platform Metadata** | Render platform-specific metadata for distribution | Multi-platform metadata outputs with SEO scoring | Phase 1 + Phase 2 |

---

## Future Enhancements (Out of Scope)

- LLM-powered episode title generation
- Competitor keyword gap analysis
- Automatic thumbnail text overlay generation
- A/B testing for metadata variants
- Podcast host platform integrations (Libsyn, Buzzsprout, etc.)
- Web dashboard / SaaS interface
