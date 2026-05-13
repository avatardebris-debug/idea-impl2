# Code Review — Phase 3

## Phase Overview
Phase 3 delivers a model-agnostic LLM harness, vector store integration (ChromaDB), semantic search, multi-video comparison support, and advanced summarization/Q&A features. The harness abstracts LLM providers, the vector store indexes transcript chunks for retrieval, and the summarizer/question-answering services leverage this infrastructure.

## Deliverables Assessment

### 1. LLM Harness (`llm_harness.py`) ✅
- **Provider-agnostic interface**: `LLMHarness` class with `provider`, `model`, and `api_key` parameters.
- **Supported providers**: Currently only OpenAI is implemented. The `generate()` method dispatches to `_call_openai()` and raises `ValueError` for unsupported providers.
- **JSON generation**: `generate_json()` parses LLM text responses as JSON, with fallback logic to extract JSON from wrapped text.
- **Configuration**: Reads from `settings` (env vars) with sensible defaults.
- **Missing**: Anthropic, Google, and Ollama providers are mentioned in the spec but not implemented. Only OpenAI is functional.

### 2. Configuration System (`config.py`) ✅
- Comprehensive `Settings` class loading from environment variables.
- Covers all Phase 3 concerns: LLM provider/model, embedding model, vector DB path, chunking parameters.
- Supports `.env` file loading via `python-dotenv`.
- **Note**: `OPENAI_API_KEY` defaults to empty string — this is acceptable for development but should be flagged in production docs.

### 3. Vector Store (`vector_store.py`) ✅
- ChromaDB integration with per-job collections.
- `upsert()` method handles chunk insertion with auto-generated embeddings if missing.
- `search()` method performs semantic similarity search with configurable `top_k`.
- `delete_collection()` for cleanup.
- **Issue**: Embeddings are generated inline in `upsert()` and `search()` by importing `EmbeddingGenerator` — this creates a tight coupling between the vector store and the embedding module.

### 4. Summarizer (`summarizer.py`) ✅
- `Summarizer` class with configurable length, tone, and format.
- Uses `LLMHarness.generate_json()` for structured output.
- Limits context to last 50 segments and 4000 characters to avoid token limits.
- `summarize_from_text()` provides a simpler text-only path.
- **Issue**: The `context_segments` logic uses `segments[-50:]` which takes the *last* 50 segments — this may miss important early content in long transcripts.

### 5. Question Answering (`question_answering.py`) ✅
- `QuestionAnswerer` class with vector store integration.
- Retrieves relevant chunks via semantic search, builds context, and generates answers.
- Handles missing chunks, missing response keys, and None values gracefully.
- `answer_from_text()` provides a fallback for raw text without vector store.
- **Issue**: `system_prompt` parameter is accepted but never used in the prompt construction — it's silently ignored.

### 6. Multi-Video Comparison
- **Not implemented**. The spec calls for "multi-video comparison and cross-reference capabilities" but no code exists for this.

### 7. Semantic Search
- **Partially implemented**. Single-video semantic search works via `VectorStore.search()`. Cross-video search across multiple jobs is not implemented.

### 8. Plugin System
- **Not implemented**. The spec mentions "plugin architecture for custom processing" but no plugin system exists.

### 9. Rate Limiting, Caching, Cost Tracking
- **Not implemented**. No rate limiting, caching, or cost tracking code found.

### 10. Containerization (Docker, K8s)
- **Not implemented**. No Dockerfile, docker-compose, or K8s manifests found.

### 11. API Docs, SDK, Deployment Guides
- **Partially implemented**. FastAPI API exists with auto-generated docs at `/docs`. No separate SDK or deployment guides found.

## Blocking Bugs

### Bug 1: LLM Harness Only Supports OpenAI
The spec requires support for OpenAI, Anthropic, Google, and Ollama/local models. Only OpenAI is implemented. The `generate()` method raises `ValueError` for any other provider. This is a **blocking** issue because the core deliverable (model-agnostic harness) is incomplete.

### Bug 2: `system_prompt` Parameter Silently Ignored
In `question_answering.py`, the `answer()` method accepts a `system_prompt` parameter but never incorporates it into the prompt sent to the LLM. This is misleading API design — the parameter should either be used or removed.

### Bug 3: Missing Phase 3 Deliverables
The following spec deliverables are entirely absent:
- Multi-video comparison
- Cross-video semantic search
- Plugin system
- Rate limiting
- Caching
- Cost tracking
- Docker/K8s containerization
- Deployment guides

These are not minor omissions — they constitute a significant portion of the Phase 3 spec.

## Non-Blocking Notes

### Code Quality
- Code is well-structured with clear class hierarchies and docstrings.
- Error handling is consistent — custom exception classes (`SummarizationError`, `QandAError`) are used appropriately.
- Type hints are present throughout.
- Tests are comprehensive (28 passing tests) with good mock coverage.

### Design Concerns
1. **Tight coupling in VectorStore**: `upsert()` and `search()` import `EmbeddingGenerator` directly. This should be injected via constructor or a factory pattern.
2. **Context window management**: Both `Summarizer` and `QuestionAnswerer` hardcode 4000-character limits. These should be configurable.
3. **`_call_openai` kwargs passthrough**: The `generate()` method passes `**kwargs` to `_call_openai()` but `_call_openai()` only uses `model`, `temperature`, and `max_tokens`. Other kwargs (like `system_prompt`) are silently dropped.
4. **`api.py` uses deprecated `@app.on_event()`**: Should migrate to lifespan event handlers.
5. **No retry logic**: LLM API calls have no retry mechanism for transient failures.

### Test Coverage
- 28 tests covering harness, summarizer, and question answering.
- Good mock-based testing strategy.
- No integration tests with real LLM or vector store.
- No tests for `config.py`, `api.py`, or `embedding_generator.py`.

## Recommendations

### Must Fix (Blocking)
1. **Implement missing LLM providers** (Anthropic, Google, Ollama) or update the spec to reflect that only OpenAI is supported in Phase 3.
2. **Fix `system_prompt` handling** in `QuestionAnswerer.answer()` — either use it in the prompt or remove the parameter.
3. **Address missing Phase 3 deliverables** — either implement them or update the spec to reflect the reduced scope.

### Should Fix
4. **Inject `EmbeddingGenerator`** into `VectorStore` instead of importing it directly.
5. **Make context length limits configurable** in `Summarizer` and `QuestionAnswerer`.
6. **Add retry logic** for LLM API calls.
7. **Migrate from `@app.on_event()`** to lifespan event handlers in `api.py`.

### Nice to Have
8. Add integration tests with mock LLM/vector store.
9. Add tests for `config.py` and `api.py`.
10. Add rate limiting and caching implementations.
11. Add Docker/K8s containerization.

## Verdict
**Phase 3 is partially complete.** The core LLM harness, vector store, summarizer, and question answering components are implemented and tested. However, significant spec deliverables are missing (multi-video comparison, plugin system, containerization, etc.), and the LLM harness only supports OpenAI despite claiming model-agnosticism. The code quality is good, but several design issues should be addressed before merging.
