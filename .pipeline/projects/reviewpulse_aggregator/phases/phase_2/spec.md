## Phase 2 — Multi-Platform Support + Auto Response Drafts

### Description
Expand the ingestion layer to support **multiple review platforms** (Yelp, Facebook, TripAdvisor). Add the **response draft generator** that produces context-aware reply suggestions using an LLM, incorporating business profile data (tone, services, policies). Introduce a business profile management system.

### Deliverables
- [ ] Yelp API integration
- [ ] Facebook Graph API integration (reviews endpoint)
- [ ] Unified review abstraction layer (platform-agnostic model)
- [ ] Business profile model (name, category, tone preferences, response policies)
- [ ] LLM-powered response draft generator (prompt templates + business context injection)
- [ ] Response draft API endpoint (POST /responses/draft → returns 1–3 draft options)
- [ ] Admin dashboard (Phase 1 API wrapper) — view reviews, sentiment distribution, draft responses
- [ ] Platform-specific auth management (OAuth flows, token refresh)
- [ ] Rate-limit handling and retry logic per platform

### Dependencies
- Phase 1 (ingestion + sentiment pipeline)
- Yelp Developer API credentials
- Facebook Developer account + app with reviews permission
- OpenAI API key or hosted LLM endpoint
- React frontend (minimal dashboard)

### Success Criteria
- [ ] Ingests reviews from ≥ 3 platforms simultaneously
- [ ] Unified dashboard shows aggregated sentiment across all platforms
- [ ] Response drafts are generated within 5 seconds and are contextually relevant
- [ ] Business owners can customize response tone (formal, friendly, apologetic, etc.)
- [ ] Platform auth tokens auto-refresh without manual intervention
- [ ] Dashboard renders sentiment summary charts and review list

### Estimated Effort
~3–4 weeks

---

