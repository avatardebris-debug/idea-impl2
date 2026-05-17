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

