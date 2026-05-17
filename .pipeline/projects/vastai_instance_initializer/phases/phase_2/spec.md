## Phase 2 — Multi-Instance Batch Initialization

**Goal:** Launch multiple instances from one or more presets with timing control and batch monitoring.

**Description:**
- Extend the preset system to support **multi-preset batches**: a user can specify multiple presets in a single launch config.
- Add a **timing configuration** option: fixed delay between each instance launch (e.g., 30s, 60s, 120s) or staggered by percentage of prior instance status.
- Add **concurrency control**: max parallel launches to avoid API rate limits.
- Implement a **batch orchestrator** that:
  - Queues instances to launch
  - Respects timing/concurrency settings
  - Tracks the state of every instance in the batch
  - Provides a live progress view (CLI spinner/table)
- Add a **batch status report** on completion (all running, some failed, summary).
- Support **instance count parameter** in presets (e.g., `count: 5` to launch 5 identical instances).

**Deliverable:**
- CLI command `vastai-init batch launch <batch-config>` supporting multi-preset, multi-instance launches.
- Real-time progress tracking in the terminal.
- Batch completion report with per-instance status.

**Dependencies:**
- Phase 1 (single-instance launcher and preset format)
- VAST.ai API rate limit documentation

**Success Criteria:**
- [ ] Can define a batch config with multiple presets and instance counts
- [ ] Instances launch with correct timing between them
- [ ] Concurrency limits are respected (no API throttling)
- [ ] Live progress view shows per-instance status
- [ ] Batch report accurately reflects final state of all instances
- [ ] Failed instances are clearly flagged with error details
- [ ] Can pause/resume a batch launch

**Estimated Effort:** 3–4 weeks

---

#