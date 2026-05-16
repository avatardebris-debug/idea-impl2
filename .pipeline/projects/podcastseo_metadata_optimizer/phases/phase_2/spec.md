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

