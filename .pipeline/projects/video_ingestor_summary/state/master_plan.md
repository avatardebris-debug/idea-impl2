# Video Ingestor Summary — Master Implementation Plan

## Idea Overview

A system that ingests videos, transcribes their dialogue via speech-to-text, summarizes content, and enables users to ask questions about video content — all through a model-agnostic LLM harness.

### Core Capabilities
1. **Video Ingestion** — Accept video uploads (file or URL)
2. **Dialogue Transcription** — Extract spoken dialogue as text
3. **Content Summarization** — Produce concise summaries of video content
4. **Question Answering** — Answer user queries grounded in video content
5. **Model-Agnostic LLM Harness** — Swappable LLM backend (OpenAI, Anthropic, local models, etc.)

---

## Architecture Overview

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Video Input  │────▶│  Transcription    │────▶│  Text Store     │
│  (upload/URL) │     │  (Whisper/ASR)    │     │  (chunks + meta)│
└──────────────┘     └──────────────────┘     └────────┬────────┘
                                                        │
                                                        ▼
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Q&A Engine   │◀────│  LLM Harness      │◀────│  Summarization  │
│  (user queries)│    │  (model-agnostic) │     │  + Indexing     │
└──────────────┘     └──────────────────┘     └─────────────────┘
```

### Key Components
| Component | Responsibility |
|---|---|
| **Ingestor** | Accepts video, extracts audio, handles errors/retries |
| **Transcriber** | Converts audio → text with timestamps |
| **Summarizer** | Generates structured summaries of content |
| **LLM Harness** | Abstraction over LLM providers for summarization & Q&A |
| **Indexer** | Chunks text, builds vector index for retrieval |
| **Q&A Engine** | Retrieves relevant chunks, formulates answers |
| **API** | REST/gRPC interface for all operations |

---

## Phase 1: Video Ingestion & Transcription Pipeline (MVP)

### Description
Build the foundational pipeline: accept a video, extract its audio track, transcribe the audio to timestamped text, and store the results. This is the smallest useful thing — it produces a searchable transcript from any video.

### Deliverables
- REST API endpoint for video upload (file or URL)
- Audio extraction module (FFmpeg-based)
- Speech-to-text transcription using Whisper or compatible ASR model
- Timestamped transcript storage (JSON or SQLite)
- Health check & status endpoint for job tracking
- Basic CLI tool for local testing

### Dependencies
- FFmpeg (audio extraction)
- Whisper or OpenAI Whisper-compatible library (transcription)
- Python 3.10+ with FastAPI (or equivalent framework)
- Storage backend (SQLite for MVP, configurable for later)

### Success Criteria
- [ ] Upload a video file or provide a URL and receive a transcript within 5 minutes for a 10-minute video
- [ ] Transcript includes word-level or sentence-level timestamps
- [ ] Transcript accuracy on clear dialogue exceeds 85% (WER < 15%) on test set
- [ ] System handles common video formats (MP4, MOV, AVI, MKV)
- [ ] API returns structured JSON with transcript, metadata, and status
- [ ] Graceful handling of unsupported formats and network errors

### Risks & Mitigations
| Risk | Mitigation |
|---|---|
| Large video files overwhelm memory | Stream audio extraction; process in chunks |
| Whisper inference is slow | Use faster model variants (tiny/base); add async processing |
| Non-English audio mis-transcribed | Use multilingual Whisper model; document language support |
| Storage grows unbounded | Implement retention policies early |

---

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
- Support data retention and deletion policies (GDPR compliance)

---

## Timeline Estimate

| Phase | Duration | Key Milestone |
|---|---|---|
| Phase 1 | 2-3 weeks | MVP: upload video → get transcript |
| Phase 2 | 3-4 weeks | Summarization + Q&A working end-to-end |
| Phase 3 | 3-4 weeks | Model-agnostic harness + multi-video + search |

**Total estimated timeline: 8-11 weeks**

---

## Open Questions
1. What is the target video length range? (affects chunking strategy)
2. Are there specific languages beyond English that need first-class support?
3. What is the expected scale (number of concurrent users, videos per day)?
4. Should the system support real-time streaming transcription?
5. Are there compliance requirements (HIPAA, SOC2) for stored video data?
