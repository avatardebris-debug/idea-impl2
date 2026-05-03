## Phase 4: Content Pipeline & Scheduling

**Description**: Build a production-ready content pipeline that can generate, review, and schedule content for publishing. This makes the bot practically useful.

**Deliverable**:
- Content pipeline: topic research → generation → review → scheduling
- Topic generator that suggests topics based on current events and Adams' typical subjects
- Review system: automated style checks + optional human review
- Scheduler: integrates with Twitter/X API, LinkedIn API, or RSS feed
- Dashboard for monitoring content output and engagement

**Dependencies**: Phase 2 (content generation) or Phase 3 (fine-tuned model)

**Success Criteria**:
- Pipeline can generate and schedule a week's worth of content autonomously
- Content passes automated style checks (≥ 80% style match score)
- Scheduler successfully posts to at least one platform (Twitter/X or RSS)
- Dashboard shows real-time content pipeline status

**Tasks**:
- [ ] Task 23: Topic research module — current events aggregation, topic suggestion algorithm
- [ ] Task 24: Content review system — automated style checks, quality filters
- [ ] Task 25: Platform integrations — Twitter/X API, LinkedIn API, RSS
- [ ] Task 26: Scheduler — cron-based or event-driven content scheduling
- [ ] Task 27: Dashboard — web-based or CLI dashboard for pipeline monitoring
- [ ] Task 28: End-to-end pipeline test — generate and publish a week of content
- [ ] Task 29: Documentation — deployment guide, API reference

---

