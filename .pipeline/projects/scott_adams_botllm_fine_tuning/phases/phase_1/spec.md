## Phase 1: Corpus Collection & Style Analysis (Smallest Useful Thing)

**Description**: Collect a representative corpus of Scott Adams' writing and perform initial style analysis. This produces a curated dataset and a style profile that informs all downstream work.

**Deliverable**:
- Curated corpus of 500-1000 writing samples (blog posts, tweets, book excerpts) in a structured format (JSONL with text, metadata, source)
- Style analysis report documenting: average sentence length, paragraph structure, humor patterns, recurring themes, rhetorical devices, tone distribution
- A "style prompt" template that captures the key stylistic features

**Dependencies**: None — this is the foundational phase

**Success Criteria**:
- Corpus contains at least 500 samples spanning multiple years and content types
- Style analysis identifies at least 10 distinct stylistic features with quantitative measurements
- A prompt template using 5 few-shot examples can generate text that a blind human rater identifies as "possibly Scott Adams" ≥ 40% of the time

**Tasks**:
- [ ] Task 1: Set up project — directory structure, requirements, data schema
- [ ] Task 2: Build corpus scraper — scrape scottadamsslog.com, Twitter/X archives, book excerpts (fair use)
- [ ] Task 3: Clean and deduplicate corpus — remove boilerplate, ads, comments
- [ ] Task 4: Annotate corpus — tag samples by type (blog, tweet, book, interview), date, theme
- [ ] Task 5: Quantitative style analysis — sentence length, word frequency, rhetorical devices, humor markers
- [ ] Task 6: Qualitative style analysis — recurring themes, contrarian patterns, "Stack of Luck" framing
- [ ] Task 7: Draft style prompt template with few-shot examples
- [ ] Task 8: Write style analysis report

---

