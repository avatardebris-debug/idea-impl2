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
- A/B testing for metadata vari