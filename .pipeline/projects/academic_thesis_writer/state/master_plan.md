# Academic Thesis Writer — Master Implementation Plan

## 1. Idea Analysis

**Core Deliverable:** An AI-assisted research paper generator that enables users to produce publication-ready academic theses through automated literature review synthesis, intelligent citation management, and strict academic formatting compliance.

**Key Capabilities:**
- AI-driven content generation grounded in cited sources
- Bibliography/citation manager (APA, MLA, Chicago, IEEE, etc.)
- Literature review synthesis engine
- Multi-format academic output (LaTeX, DOCX, PDF, HTML)
- Plagiarism-aware generation with source attribution

**Architecture Notes:**
- **Frontend:** Web-based editor with real-time preview (React/Next.js)
- **Backend:** Python API service (FastAPI) orchestrating LLM calls and document processing
- **LLM Layer:** Modular prompt system with configurable models (OpenAI, Anthropic, local)
- **Storage:** SQLite for project metadata; vector store (ChromaDB) for literature embeddings
- **Document Engine:** python-docx + textract + pandoc for multi-format export
- **Citation Engine:** biblatex-compatible parser + CSL (Citation Style Language) formatter

**Risks:**
| Risk | Impact | Mitigation |
|------|--------|------------|
| Hallucinated citations | Critical — undermines academic integrity | Mandatory source-grounding; citation verification pass; user-facing confidence scores |
| LLM cost at scale | High — literature review can be expensive | Chunked processing; caching; fallback to local models; rate limiting |
| Plagiarism concerns | Critical — legal/ethical | Built-in paraphrase engine; similarity detection against source corpus; clear AI-assistance disclosure |
| Formatting compliance | Medium — user trust | Formal schema validation; test suite against style guides; user-editable templates |
| Scope creep | Medium — timeline | Strict phase gates; defer "collaboration" and "journal submission" to post-MVP |

---

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

## Phase 2 — Intelligence: Literature Review Synthesis & Advanced Citation Management

> **Goal:** Elevate the system from a citation-aware generator to an intelligent research assistant that can synthesize literature, manage complex bibliographies, and detect source conflicts.

### Description
Add a literature review synthesis engine that reads through uploaded sources, clusters them by theme/topic, identifies gaps and contradictions, and generates a synthesized literature review section. Expand the citation manager to handle BibTeX import/export, deduplication, and conflict resolution. Introduce a source-grounding verification pass that checks generated claims against source material.

### Deliverables
1. **Literature Synthesis Engine** — Clusters sources by thematic similarity; generates a synthesized literature review with cross-source comparisons, identified research gaps, and consensus/conflict mapping.
2. **BibTeX Import/Export** — Full BibTeX parser and writer; drag-and-drop `.bib` file support.
3. **Citation Deduplication & Conflict Resolver** — Detects duplicate entries across sources; flags conflicting claims between sources; presents resolution options to the user.
4. **Source-Grounding Verification Pass** — Post-generation check that verifies each claim in the draft has at least one supporting source; flags unsupported claims for user review.
5. **Source Similarity Search** — Vector-based retrieval over the source corpus; enables "find similar sources" and "find supporting evidence" queries.
6. **Enhanced Web Editor** — Source management panel, literature review preview, verification report dashboard, and inline editing of generated content.

### Dependencies
- Phase 1 (Thesis Project Model, Citation Engine, Draft Generation Pipeline, Web Editor foundation)

### Success Criteria
- [ ] Literature synthesis correctly identifies ≥3 thematic clusters from a 20-source corpus.
- [ ] BibTeX import produces accurate entries with no data loss (tested against 50 real `.bib` files).
- [ ] Citation deduplication correctly identifies ≥90% of duplicate entries in mixed-source sets.
- [ ] Source-grounding verification catches ≥95% of unsupported claims in a controlled test set.
- [ ] User can edit any generated section inline and see the citation bibliography update in real time.
- [ ] Literature review synthesis completes in < 3 minutes for a 20-source project.

---

## Phase 3 — Polish: Academic Formatting Suite, Export Ecosystem & Collaboration

> **Goal:** Deliver a production-quality tool with full academic formatting compliance, multi-format export, and basic collaboration features suitable for academic use.

### Description
Complete the product with rigorous academic formatting support (section numbering, figure/table captions, equation blocks, footnotes), a comprehensive export ecosystem (LaTeX, PDF, HTML, DOCX with all styles), and collaboration features (shareable project links, comment threads, version history). Add a template library of common thesis structures by discipline.

### Deliverables
1. **Academic Formatting Engine** — Full compliance with major style guides: section numbering, figure/table cross-references, equation numbering, footnotes/endnotes, running headers, page numbering.
2. **LaTeX Export with Template Library** — Generates compilable `.tex` files with discipline-specific templates (STEM, Humanities, Social Sciences, Medicine); includes figure/table placement hints.
3. **PDF Export Pipeline** — Renders final thesis to PDF via LaTeX compilation or pandoc; preserves all formatting.
4. **HTML Export** — Semantic HTML output for web publication or LMS upload.
5. **Collaboration Layer** — Shareable project links; comment threads on sections; basic version history (diff view).
6. **Discipline Template Library** — Pre-built templates for common thesis structures across 5+ disciplines (Computer Science, Psychology, Biology, History, Economics).
7. **AI Disclosure & Integrity Module** — Automated AI-assistance disclosure statement; similarity check against source corpus; configurable "AI contribution" watermark for institutional compliance.

### Dependencies
- Phase 1 (all deliverables)
- Phase 2 (Literature Synthesis Engine, Citation Deduplication, Source-Grounding Verification, Source Similarity Search)

### Success Criteria
- [ ] LaTeX export produces compilable output with zero errors across 5 discipline templates.
- [ ] PDF export preserves all formatting (citations, figures, tables, equations) to within 1% visual fidelity of the source document.
- [ ] HTML export passes WCAG 2.1 AA accessibility checks.
- [ ] Collaboration features support ≥2 concurrent users editing the same project.
- [ ] Version history captures ≥99% of meaningful edits with accurate diff output.
- [ ] AI disclosure module generates institutionally-compliant disclosure statements for ≥10 major university policies.
- [ ] End-to-end thesis generation (from topic to PDF) completes in < 8 minutes for a 50-source project.

---

## Phase Summary

| Phase | Name | Scope | Est. Duration |
|-------|------|-------|---------------|
| 1 | Core Thesis Engine + Citation Backbone | MVP: generate cited thesis drafts | 6–8 weeks |
| 2 | Literature Synthesis + Advanced Citations | Intelligence: synthesis, verification, BibTeX | 6–8 weeks |
| 3 | Formatting Suite + Export + Collaboration | Polish: LaTeX, PDF, HTML, collaboration | 6–8 weeks |

**Total Estimated Duration:** 18–24 weeks

## Open Questions / Decisions Needed
1. **LLM Provider Strategy:** Default to OpenAI GPT-4o for generation, with Anthropic Claude 3 as fallback? Or support both from day one?
2. **Local Model Support:** Phase 1 should we include a local model path (e.g., Ollama + Llama 3) for air-gapped institutions?
3. **Plagiarism Detection:** Integrate with an external API (Turnitin-style) or build a lightweight cosine-similarity checker over the source corpus?
4. **Authentication:** Phase 1 — anonymous/local projects only? Phase 3 — full auth with institutional SSO (Shibboleth/CAS)?
5. **Monetization:** Free tier with usage limits? Academic institutional licensing?

## Glossary
- **CSL:** Citation Style Language — the standard for formatting citations.
- **Source-Grounding:** The process of ensuring every generated claim maps to at least one uploaded source.
- **BibTeX:** The standard bibliography file format used in LaTeX.
- **Vector Store:** A database optimized for similarity search over text embeddings.
