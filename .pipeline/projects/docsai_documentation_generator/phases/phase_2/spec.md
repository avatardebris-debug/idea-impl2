## Phase 2 — README Generator with Templates

### Description
Extend the pipeline to generate README.md files. This phase adds a template engine and an LLM-powered content generator that produces project overviews, installation instructions, usage examples, and architecture summaries.

### Deliverable
- A CLI subcommand `docsai readme` that generates a complete README.md.
- Template system supporting custom markdown templates.
- LLM-generated content: project description, usage examples, architecture notes.
- Integration with Phase 1: the README can reference the generated API spec.

### Dependencies
- Phase 1 (API spec generator must exist and produce parseable output).

### Success Criteria
- [ ] `docsai readme ./my_project` produces a complete, well-formatted README.md.
- [ ] README includes: project overview, install steps, usage examples, API reference link, architecture diagram (text-based).
- [ ] Custom templates can override default sections.
- [ ] Generated content is coherent and accurate for a sample project.
- [ ] README references the Phase 1 API spec output.

---

