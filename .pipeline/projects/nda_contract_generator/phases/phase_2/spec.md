## Phase 2: AI-Assisted Legal Phrasing + Expanded Jurisdictions

**Description:** Add an optional AI-assisted phrasing layer that generates and refines clause text using LLM APIs. Support multiple LLM backends (OpenAI, Ollama). Expand jurisdiction coverage to 8+ regions. Add a clause marketplace concept — users can save, share, and load custom clause sets. This phase significantly improves the quality and flexibility of generated clauses.

**Deliverable:**
- `ai/phrasing_engine.py` — AI clause generation and refinement engine
- `ai/prompt_templates/` — system prompts for clause generation, refinement, and tone adjustment
- `ai/providers/openai.py`, `ai/providers/ollama.py` — LLM provider implementations
- `ai/providers/base.py` — abstract provider interface
- Jurisdiction expansion to 8+ regions (US: NY, DE, TX; UK; EU; Canada; Australia; Singapore)
- `core/clause_library.py` extended with save/load custom clause sets
- `cli/commands/customize.py` extended with AI-assisted clause generation
- `tests/test_ai_phrasing.py` — integration tests for AI provider interface (mocked)
- Updated documentation with AI usage examples

**Dependencies:** Phase 1 (template engine, clause library, jurisdiction registry)

**Success Criteria:**
- [ ] AI phrasing generates coherent, legally-appropriate clause text for all 20+ clause types
- [ ] OpenAI and Ollama providers both work (configurable via `--ai-provider openai|ollama`)
- [ ] AI refinement mode (`--ai-refine`) rewrites existing clauses with adjusted tone (formal, plain-language, aggressive, balanced)
- [ ] 8+ jurisdictions produce correct governing law and required clause sets
- [ ] Custom clause sets can be saved to JSON and loaded: `--load-clauses my_clauses.json`
- [ ] AI calls are cached to avoid redundant API calls
- [ ] Graceful fallback when AI provider is unavailable (uses built-in templates)
- [ ] CLI: `python -m nda_contract_generator draft --template mutual --jurisdiction california --ai-provider ollama --ai-refine --output output.txt`

---

