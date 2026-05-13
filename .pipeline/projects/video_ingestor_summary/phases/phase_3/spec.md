## Phase 3: Model-Agnostic LLM Harness & Advanced Features

### Description
Abstract the LLM layer to support multiple providers and models, enabling users to swap backends without changing application logic. Add advanced features: multi-video comparison, semantic search across ingested content, and plugin architecture for custom processing.

### Deliverables
- **LLM Harness** — Provider-agnostic interface supporting OpenAI, Anthropic, Google, Ollama/local models
- Configuration system for switching models per operation (summarize vs. Q&A)
- Multi-video comparison and cross-reference capabilities
- Semantic search across all ingested video transcripts
- Plugin system for custom transcription/summarization processors
- Rate limiting, caching, and cost tracking across providers
- Comprehensive API docs, SDK, and deployment guides (Docker, K8s)

### Dependencies
- **Phase 2** (summarization and Q&A must work)
- Multiple LLM provider API keys (for testing)
- Containerization (Docker) and orchestration configs

### Success Criteria
- [ ] Any supported LLM provider can be swapped in under 10 minutes of config change
- [ ] All Phase 2 features work identically across ≥3 LLM providers
- [ ] Multi-video comparison produces coherent cross-video summaries
- [ ] Semantic search returns relevant results across ≥100 ingested videos
- [ ] Cost tracking accurately logs per-operation provider and cost
- [ ] System is fully containerized with documented deployment paths

### Risks & Mitigations
| Risk | Mitigation |
|---|---|
| Provider API changes break abstraction | Write integration tests per provider; pin API versions |
| Local model quality is inferior | Clearly document quality tiers; allow per-operation model selection |
| Feature creep in harness layer | Scope strictly to abstraction + multi-video + search; defer plugins to v2 |
| Vendor lock-in in vector DB | Use portable format exports; abstract vector store behind interface |

---

## Cross-Phase Architecture Notes

### Technology Recommendations
| Layer | Recommendation | Alternatives |
|---|---|---|
| API Framework | FastAPI (Python) | Express.js, Go + Gin |
| Transcription | OpenAI Whisper (open-source) | AssemblyAI, Deepgram |
| Vector Store | ChromaDB (MVP) → pgvector (scale) | FAISS, Weaviate |
| LLM Harness | Custom abstraction layer | LiteLLM, LangChain |
| Storage | SQLite (MVP) → PostgreSQL | MongoDB, S3 + metadata DB |
| Task Queue | Celery + Redis | RQ, BullMQ |
| Deployment | Docker Compose (MVP) → Kubernetes | ECS, Fly.io |

### Data Flow
1. **Ingest**: Video → audio extraction → transcription → timestamped text → store
2. **Summarize**: Text → chunk → embed → index → LLM summarize → store summary
3. **Query**: User question → embed → retrieve chunks → LLM answer with citations → return

### Security Considerations
- Validate and sanitize all video inputs (malicious payloads in video files)
- Rate limit API endpoints
- Encrypt stored transcripts at rest
- Audit log all LLM API calls
- Supp