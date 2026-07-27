# Phase 5 Tasks: External ingest manual — pin, sandbox, human gate

- [x] Task 1: Quarantine layout + pin/provenance record
  - What: Add `pipeline/external_ingest.py` (new) defining schema `external_asset.v1` under `$PIPELINE_DIR/external/` (or `state/external_ingest/`): kinds `skill | software | mcp | external_mcp`; fields at least id, kind, source_url_or_path, pin (commit SHA and/or content_sha256), license_note, status (`quarantined|scanned|approved|rejected|promoted|revoked`), risk_class, created_at. Implement **pin from local path or fixture tarball/dir** (no live `git clone` required for tests; optional live URL only behind explicit flag default off). Copy/snapshot into quarantine dir so promote never depends on mutable outside path.
  - Files: `pipeline/external_ingest.py`, `pipeline/paths.py` (optional `external_dir()`), `test_external_ingest.py`
  - Done when: pin creates quarantine tree + JSON record; re-pin same id is explicit force or rejected; content hash stable for fixture.

- [x] Task 2: Static scan + sandbox checks
  - What: Static scan on quarantined payload: size caps, reject obvious secrets patterns (reuse or share patterns with `block_registry` where sensible), path traversal / disallowed extensions, basic license file note if present. Status → `scanned` on pass, stay `quarantined` or `rejected` on fail with report. No network egress from scan.
  - Files: `pipeline/external_ingest.py`, `test_external_ingest.py`
  - Done when: fixture clean asset scans pass; fixture with fake secret or path escape fails with named check; report JSON on disk.

- [x] Task 3: Human CLI gate (approve / reject)
  - What: CLI `scripts/external_ingest.py` with subcommands e.g. `pin`, `scan`, `approve`, `reject`, `list`, `show`. **Promote is impossible without prior `approve`.** Approve records actor (env `EXTERNAL_INGEST_ACTOR` or `USER`/`USERNAME`), timestamp, optional notes. Reject sets status rejected + reason. Append-only **audit log** under PIPELINE_DIR (jsonl).
  - Files: `scripts/external_ingest.py`, `pipeline/external_ingest.py`, tests
  - Done when: pytest covers approve-then-promote path and promote-without-approve raises/fails; audit log has pin/scan/approve lines.

- [x] Task 4: Promote to draft registry shape + smoke hook
  - What: On promote: write `external_*` draft usable by later phases (manifest under external/ or thin registry row) with provenance pin hash; status `promoted`. Optional light smoke: skill SKILL.md exists / software has entrypoint marker / mcp has server stub — **presence only**, not field_prove. Compose/attempt must **not** git-clone; document that graph nodes only reference promoted ids. Wire `goal_trace` / `set_outcome` with `trust=external` and low train_weight (use Phase 3 clamp).
  - Files: `pipeline/external_ingest.py`, `pipeline/goal_trace.py` (call only), tests
  - Done when: one full fixture path pin → scan → approve → promote under temp PIPELINE_DIR; trace or report shows external + weight ≤ EXTERNAL_MAX; promote without approve blocked.

- [x] Task 5: Docs + non-goals
  - What: COMMANDS.md operator path; notes/agi-lmaooo2.md Layer C / P5 status honest (manual only). Explicit: no unattended GitHub search/auto-pull; Phase 6 will teach smoke_graph/policy about external nodes.
  - Files: `COMMANDS.md`, `notes/agi-lmaooo2.md`, `state/master_plan.md` (status when implemented)
  - Done when: operator can run CLI sequence from docs without reading source; auto-ingest listed as out of scope.

- [x] Task 6: Verification suite
  - What: Focused tests + any regression on goal_trace external clamp.
  - Files: `test_external_ingest.py`, related
  - Done when: `python -m pytest test_external_ingest.py test_goal_trace.py -q` passes on Windows (adjust if needed).

## Out of scope
- Unattended GitHub search / clone / auto-promote
- Compose policy + smoke_graph external node rules (Phase 6)
- Field dual-gate changes (Phase 2 done)
- Graph engineer (Phase 8)
- MCP factory reimplementation
- Live network tests in CI (fixture-only)

## Notes
- Factory root paths (not product `workspace/`).
- Prefer local fixture “fake skill” dir with SKILL.md for e2e test—not network.
- Human gate is security control: log + require explicit approve command (not a silent default).
- Align status vocabulary with registry-style draft/sandboxed/verified only where it reduces confusion; quarantine statuses may stay external-ingest-specific until Phase 6.
