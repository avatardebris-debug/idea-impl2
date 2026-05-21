## Phase 3: Instance Management, Cost Controls & Templates

**Goal:** Full lifecycle management of provisioned instances with cost awareness and reusable templates.

**Scope:**
- **Instance lifecycle management:**
  - List all instances from active executions
  - Stop, restart, or delete individual instances
  - View live terminal output (WebSocket or polling)
  - Copy instance terminal commands
- **Cost controls:**
  - Estimated cost per preset (based on GPU price × expected duration)
  - Budget cap per batch execution
  - Real-time cost accumulator during batch run
  - Warning alerts when approaching budget limits
- **Template system:**
  - Pre-built templates (e.g., "PyTorch Training", "LLM Fine-tuning", "Docker Dev Environment")
  - Template gallery with community-shared presets
  - One-click template application
- **Advanced scheduling:**
  - Region-based instance selection (prefer cheapest/available region)
  - GPU availability checker before launch
  - Retry failed instances automatically (configurable max retries)
- **Notifications:**
  - System notifications on batch completion/failure
  - Email/webhook alerts (optional)

**Deliverable:**
A user can:
1. See estimated costs before launching a batch
2. Set a $10 budget cap and get warned at $8
3. Manage all provisioned instances from one view
4. Stop/restart individual instances
5. Use pre-built templates to get started quickly
6. Get notified when batches complete or fail

**Dependencies:**
- Phase 2 (batch scheduler, preset library, execution tracking)

**Success Criteria:**
- [ ] Cost estimation within 10% of actual VAST AI pricing
- [ ] Budget cap enforcement (stops batch when exceeded)
- [ ] Instance management (stop/restart/delete) works reliably
- [ ] Live terminal output updates in < 3 seconds
- [ ] At least 5 pre-built templates included
- [ ] Notifications deliver within 5 seconds of event
- [ ] Retry logic handles transient failures gracefully

**Risks & Mitigations:**
| Risk | Mitigation |
|------|-----------|
| VAST AI pricing changes frequently | Cache pricing data; allow manual override; show "last updated" timestamp |
| Live terminal output reliability | Fallback to polling if WebSocket unavailable; queue output messages |
| Orphaned instances costing money | Auto-detect and alert on instances older than expected; one-click cleanup |
| Template security (arbitrary command execution) | Sanitize template inputs; warn users before running arbitrary commands |

---

## 4. File Structure

```
vastai-instance-initializer/
├── Cargo.toml
├── src/
│   ├── main.rs                 # Tauri app entry point
│   ├── lib.rs                  # Rust library root
│   ├── db/
│   │   ├── mod.rs
│   │   ├── schema.rs           # SQL schema definitions
│   │   ├── presets.rs          # Preset CRUD operations
│   │   ├── executions.rs       # Execution history operations
│   │   └── instances.rs        # Instance status operations
│   ├── api/
│   │   ├── mod.rs
│   │   ├── vastai_client.rs    #