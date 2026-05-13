## Phase 2: Summarization & Question Answering

### Description
Build the LLM-powered content understanding layer on top of the Phase 1 pipeline. This phase adds automatic summarization of ingested videos and a Q&A engine that answers user questions grounded in the video's transcript.

### Deliverables
- Automatic content summarization (short summary + key points)
- Text chunking and vector indexing of transcripts
- Q&A endpoint: user asks questions, system retrieves relevant transcript segments and generates answers
- Citation support (answers include timestamp references)
- Summarization configuration (length, tone, format options)
- Web UI or API documentation for interaction

### Dependencies
- **Phase 1** (transcribed transcripts must exist)
- Vector database (e.g., ChromaDB, FAISS, or pgvector)
- LLM integration (initially one provider, e.g., OpenAI or Anthropic)
- Prompt engineering for summarization and retrieval-augmented generation (RAG)

### Success Criteria
- [ ] Summaries are generated within 30 seconds of transcription completion
- [ ] Summaries capture key topics, decisions, and action items (evaluated by human review)
- [ ] Q&A answers are grounded in transcript with ≥90% factual accuracy on test queries
- [ ] Retrieved citations include accurate timestamps (±5 seconds)
- [ ] System supports ≥5 concurrent video ingestions without degradation
- [ ] Q&A latency is under 10 seconds for queries on videos up to 30 minutes

### Risks & Mitigations
| Risk | Mitigation |
|---|---|
| Long transcripts exceed LLM context limits | Implement chunking + retrieval (RAG) strategy |
| Hallucinated answers | Ground all answers in retrieved chunks; add confidence scoring |
| Vector search quality degrades | Experiment with embedding models; add re-ranking |
| Cost of LLM calls at scale | Implement caching; batch summarization; rate limiting |

---

