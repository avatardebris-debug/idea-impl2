## Phase 1 — MVP: Core Thesis Engine with Citation Backbone

> **Goal:** Ship a working system that can generate a properly cited, formatted academic paper from a user-provided topic and a small set of source references.

### Description
Build the foundational thesis generation pipeline: a user inputs a research topic, uploads or provides a small set of source documents (PDFs, URLs, or manual entries), and the system produces a draft thesis with inline citations and a bibliography. This phase establishes the core data model, the LLM orchestration layer, and the citation formatting engine.

### Deliverables
1. **Thesis Project Model** — Data structures for topics, sources, sections, citations, and bibliography entries.
2. **Source Ingestion Module** — Ability to add sources via URL, PDF upload, or manual entry; extracts text and metadata (title, authors, year, abstract).
3. **Citation Engine** — CSL-based citation formatter supporting APA 7th, MLA 9th, Chicago 17th, and IEEE styles. Generates both inline citations and a bibliography.
4. **Draft Generation Pipeline** — LLM-powered section-by-section thesis generation (Abstract, Introduction, Literature Review, Methodology, Results, Discussion, Conclusion) with inline citation insertion.
5. **Web Editor (Minimal)** — Single-page app with: topic input, source list, generated draft preview, and citation style selector.
6. **Export** — Markdown and DOCX export of the generated thesis.

### Dependencies
- None (this is the foundation phase)

### Success Criteria
- [ ] User can create a new thesis project with a topic and add ≥3 sources.
- [ ] System generates a complete 5+ page thesis draft with ≥10 inline citations.
- [ ] Bibliography is correctly formatted in the selected citation style (verified against style guide).
- [ ] All inline citations have a corresponding bibliography entry and vice versa.
- [ ] Exported DOCX preserves citation formatting and section structure.
- [ ] End-to-end flow completes in < 5 minutes for a 10-source project.

---