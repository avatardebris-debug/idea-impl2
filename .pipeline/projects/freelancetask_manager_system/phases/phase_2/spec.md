## Phase 2: Client Matcher + Job Automation

**Description:** Implement the client-opportunity matching engine and the job automation tool. The matcher evaluates freelance job listings against available service SOPs and client profiles, scoring and ranking matches. The automation tool scrapes job feeds from freelance platforms, applies the matcher, and notifies the user of high-confidence matches.

**Deliverable:**
- `core/opportunity.py` — Opportunity/job model
- `client_matcher/matcher.py` — Core matching algorithm (rule-based scoring)
- `client_matcher/scoring.py` — Weighted scoring (skills match, budget fit, timeline alignment)
- `client_matcher/filters.py` — Hard filters (rate, availability, location)
- `client_matcher/feed_parser.py` — Parse job feeds from platforms
- `automation/job_scraper.py` — Scrape/listings from freelance platforms
- `automation/auto_bidder.py` — Automated proposal submission for high-confidence matches
- `automation/notification.py` — Alert system (CLI output, email, webhook)
- `automation/scheduler.py` — Schedule periodic job scanning
- Updated CLI with `match scan`, `match list`, `automation start/stop` commands
- Integration tests for matcher + scraper pipeline
- `benchmarks/sample_opportunities.json`

**Dependencies:** Phase 1 (SOP engine, proposal generator, domain models)

**Success Criteria:**
- [ ] Matcher correctly scores and ranks at least 90% of test opportunities against SOPs
- [ ] Scoring is configurable (user-defined weight adjustments)
- [ ] Feed parser handles at least 2 platform formats (e.g., Upwork RSS, Fiverr Gigs API)
- [ ] Job scraper can poll 50+ listings per minute with configurable rate limits
- [ ] Auto-bidder submits proposals for matches above a configurable confidence threshold
- [ ] Notification system delivers alerts within 5 minutes of a new high-confidence match
- [ ] CLI: `ftm match scan --platform upwork --threshold 0.75` and `ftm automation start --interval 300`

---

