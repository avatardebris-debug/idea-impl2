## Phase 1 — Core Engine & Script Generator (MVP)

### Description
Build the foundational meta-learning engine that can take any topic and produce a structured course outline with production-ready video scripts. This is the core value proposition: turning "I want to teach X" into a sequenced, deconstructed course with scripts.

### Deliverables
1. **Topic Deconstruction Engine**
   - Input: Topic name + optional domain context
   - Output: Deconstructed skill tree with Pareto-optimal subset (80/20 rule)
   - Uses Tim Ferriss DESSC framework: Deconstruction → Selection → Sequencing

2. **Sequencing & Stakes Engine**
   - Optimal learning path ordering
   - Accountability mechanism suggestions per module
   - Compression targets (what to skip, what to emphasize)

3. **Video Script Generator**
   - Per-video lesson scripts with: hook, core content, examples, recap, CTA
   - Multiple tone options (conversational, authoritative, humorous, etc.)
   - Estimated duration per script
   - Udemy-ready formatting

4. **CLI Interface**
   - Command: `brain-download create --topic "Python for Data Science" --output ./course/`
   - Generates full course outline + all video scripts in one command

### Dependencies
- None (this is the foundation)
- LLM API key (OpenAI or equivalent) for content generation
- Python 3.10+

### Success Criteria
- [ ] Can deconstruct any topic into a skill tree with Pareto-optimal selection
- [ ] Generates a complete course outline with logical sequencing
- [ ] Produces video scripts that a course creator could record from directly
- [ ] Scripts include hooks, core content, examples, and calls-to-action
- [ ] CLI command works end-to-end: topic → course outline + scripts
- [ ] At least 3 tone options produce distinctly different scripts
- [ ] Scripts are formatted for Udemy (proper pacing, section breaks)

#