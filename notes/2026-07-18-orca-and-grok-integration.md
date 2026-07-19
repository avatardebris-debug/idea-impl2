# Orca, Grok Build, and multi-agent leverage (updated)

**Status:** research / strategy note — do not build integration yet  
**Updated:** 2026-07-18  
**Sources:** [stablyai/orca](https://github.com/stablyai/orca), local zip `Downloads/orca-main.zip` (~1.4.145-rc.3), product site onorca.dev

## What Orca actually is (corrected)

**Orca is an ADE (Agent Development Environment)** — a desktop/mobile **IDE for fleets of coding agents**, not an unattended software factory and not primarily an “agent factory that redesigns its own graph.”

| Orca does | Orca does not (out of the box) |
|-----------|--------------------------------|
| Run many CLI coding agents in parallel | Replace `pipeline/runner.py` / message bus |
| Isolate each agent in a **git worktree** | Own missions, ship-prove, finetune corpus |
| Use **your** Claude / Codex / **Grok CLI** / Cursor / … subscriptions | Decide product missions or field-prove tools |
| Mobile companion to steer agents | Self-rewrite idea-impl overnight |
| Orca CLI (worktree create, snapshot, click, fill…) | Guaranteed “debate tools then spawn agents” brain |
| Bundled skills (computer-use, orca-cli, orchestration, Linear…) | Same skill system as Grok Build `~/.grok/skills` |

Stack: TypeScript + Electron, MIT license, Stably AI. Install via releases is easier than building the full source zip.

**Earlier over-read:** “less rigid self-reconfiguring architecture” is *our* goal. Orca’s product is **human + parallel coding agents in worktrees**. Flexibility comes from *which agents you launch and how you script Orca*, not from Orca rewriting itself like a goal factory.

## Operator vision (how we might still use it)

Not: replace idea-impl with Orca.  
Not: long-term **human-steered** Orca as the product (fine short-term to learn; not the destination).

Yes (preferred hypotheses):

### A. Tool used by a single meta-agent (like Hermes)

idea-impl (or a future “one agent” control plane) **invokes Orca as a capability** when it needs parallel coding worktrees / multi-CLI fleets — same pattern as optional Hermes for research goals.

1. **Single meta-agent** (Grok-class / eventual idea-impl front agent): debates tools, picks path.  
2. **Orca runtime** (`orca serve` headless + **Orca CLI**): spins worktrees, terminals, handoffs, orchestration DAGs — **agents drive Orca**, not a human clicking the ADE.  
3. **idea-impl / thepipeline**: source of truth for ideas, statuses, ship-prove, missions, corpus.

Evidence Orca is built for agent-driven use (not only human UI):

- Public **`orca` CLI** with `--json` for machine control (worktrees, terminals, browser, status).  
- Bundled **`orca-cli` skill** and **`orchestration` skill** for agents (task-create, dispatch, DAGs, worker_done, decision gates).  
- **`orca serve`** headless Linux server mode (runtime without desktop window).  
- Docs: agents can hand off worktrees / coordinate multi-agent tasks via RPC to running runtime.

Human mobile/desktop remains optional **observer**; long-term operator preference is **agent steers Orca**.

### B. Inside the runner (Hermes-shaped integration)

```
runner / single agent
  ├─ ship-prove path (native)
  ├─ Hermes path (optional research)
  └─ Orca path (optional parallel coding fleet)
         orca serve + orca worktree / orchestration CLI
```

Preconditions: Orca runtime available; experimental orchestration enabled where required; cost/isolation policy; factory remains source of truth for *what* to work on.

What matters philosophically:

- Debate merits of tools/skills, then proceed.  
- Flexibility to use agents differently or construct new agent roles.  
- Scale attention across **many** in-progress projects (volume-as-feature).  
- **No permanent human-in-the-loop for Orca** as a design requirement — human gates only for hard values / delete / money (dropbox-class).

Possible mix-up: another product that is more of an **agent factory** (spawn specialized agents as first-class objects). Orca is an **agent IDE + agent-operable runtime**; the “factory of agents” brain can still be *our* single meta-agent + idea-impl.

## Integration sketch (future, not built)

```
                    ┌──────────────────────────────┐
  person  ─────────►│ Grok Build / meta-agent      │  skills, tool debate, plan
                    │ (or thin “control plane”)    │
                    └──────────────┬───────────────┘
                                   │ decide: which slug, which agent type
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
    idea-impl factory       Orca worktrees            direct tools
    (bus, ship-prove,       (Grok CLI, Claude,        (scripts, pytest,
     missions, corpus)       Codex… in parallel)       ship scripts)
           │                       │
           └────────── state ──────┘
              thepipeline projects/, statuses, master_ideas
```

**Minimal experiment later (cheap):**  
Manually open idea-impl2 + one project slug in Orca; run Grok CLI + one other agent on two worktrees for one real failure class (e.g. package layout). Learn friction before any glue code.

**Glue (medium):** script that lists `field_test_planning` / `ship_insufficient` / active phases and prints suggested Orca worktree commands — human still launches.

**Deep (expensive):** Orca CLI driven by factory manager, or factory subprocess that shells into Orca — only if manual experiment wins.

## MIT license — can we use it how we want?

**Short answer: yes for almost all practical uses**, with normal open-source obligations.

MIT typically allows:

- Commercial use  
- Modification  
- Distribution  
- Private use  
- Use as a dependency / alongside proprietary systems  

Requirements (usual MIT):

- Keep the copyright + MIT notice in distributed copies of **Orca’s code** (or substantial portions).  
- License is provided **as-is** (no warranty).

MIT does **not** force your **idea-impl** or **thepipeline** code to become MIT just because you run Orca next to them or call its CLI. If you **fork and redistribute Orca**, you ship Orca under MIT terms with attribution.

**Not legal advice** — if you embed Orca into a commercial product you sell, re-read `LICENSE` in the zip/repo and your counsel. For local experimental use, orchestration glue, and private forks, MIT is one of the most permissive licenses.

Telemetry: Orca may collect anonymous usage data; they document opt-out in product docs — check if that matters for your threat model.

## Is Orca “too far away”?

| Distance | Assessment |
|----------|------------|
| From **parallel coding on many worktrees** | **Near** — that is the product |
| From **agent-driven (not human-driven) control** | **Near–medium** — CLI + orchestration + headless serve exist; we still write glue |
| From **Grok in the loop** | **Near** — Grok CLI supported; Grok Build skills need mapping |
| From **Hermes-shaped optional path in runner** | **Medium** — same integration *shape*; different binary/runtime |
| From **unattended idea-impl overnight as sole owner of truth** | **Near if Orca is a tool** — far if Orca were to own missions/ship |
| From **agent debates tools then spawns fleet** | **Medium** — meta-agent is ours; Orca is the fleet substrate |
| From **agentic corporation factory** | **Far** — Orca is a component |

**Verdict:** Not too far as **agent-operable parallel coding substrate** (tool or Hermes-like side path). Wrong if framed as “human must steer Orca forever” or “Orca replaces the factory.”

## MiroFish and “agent factory” confusion

**MiroFish** (and similar “spin up lots of agents” demos) often targets **simulation / swarm / multi-persona debate** use cases. That can be useful for *research* or *opinion aggregation*, but is usually a weak fit for:

- git worktrees + real code edits  
- ship-prove / package layout  
- long-running factory state on disk  

Useful metaphor; rarely a drop-in for thepipeline project execution. Re-evaluate only if their docs show **code + tool** agents bound to repos.

## Other tools to consider (leverage map)

Group by *job*, not hype.

### A. Parallel coding / worktree fleets (Orca’s lane)

| Tool | Role |
|------|------|
| **Orca** | ADE, multi-agent worktrees, mobile, many CLI agents including Grok |
| **Cursor / multi-agent IDE features** | Same human-in-the-loop coding lane |
| **Claude Code / Codex / Grok CLI alone** | Single-agent depth; less fleet UI |

### B. Unattended multi-agent product pipelines (idea-impl’s lane)

| Tool | Role |
|------|------|
| **idea-impl (this repo)** | Your fail-forward factory, missions, ship-prove, corpus |
| **OpenHands / similar** | Autonomous software agent loops (different product assumptions) |
| **Aider** | Repo-focused coding agent, scriptable |

### C. Agent orchestration frameworks (programmable graphs)

| Tool | Role |
|------|------|
| **LangGraph / CrewAI / AutoGen-class** | Explicit agent graphs in code — “construct new agents” flexibility |
| **Custom thin orchestrator** | Read thepipeline state → spawn CLI agents or call idea-impl — often enough |

These are closer to **agent factory** mental models than Orca is — but you must own reliability, isolation, and cost.

### D. Skills / tool routing (Grok Build lane)

| Tool | Role |
|------|------|
| **Grok Build skills** | Progressive disclosure, tool selection, human-adjacent sessions |
| **MCP servers** | Tool surface for agents (you already experiment here) |
| **idea-impl capability registry** | Invoke-before-rebuild, shared_libs |

### E. Simulation swarms (usually different problem)

| Tool | Role |
|------|------|
| **MiroFish-like swarms** | Many agents, often social/sim; weak default fit for factory shipping |

## How we get where we’re aiming (path, not big bang)

Aligned with fail-forward / replace-yourself ladder:

1. **Keep idea-impl as the scale kernel** (overnight, ship-prove, missions, corpus).  
2. **Use Orca (or similar) as optional high-bandwidth layer** when *you* need parallel agents on real projects — learn, don’t integrate first.  
3. **Meta-agent behavior** (debate tools → pick path) lives in **Grok Build / prompts / a thin control plane**, not inside Electron.  
4. **Glue only after pain is real:** script “list in-progress slugs → suggested worktrees.”  
5. **Field truth** remains ship-prove / goal validation — Orca doesn’t replace it.  
6. **Corporation factory / robot arc** stays higher ladder rungs; borrow tools per layer, don’t merge everything into one monorepo dependency.

## Non-goals (still)

- No Orca in `requirements.txt` / no Electron dep in the factory.  
- No assumption that MIT Orca code must be vendored into idea-impl2.  
- No MiroFish-scale agent spam without a clear coding+git job.

## Next concrete steps (when energy allows)

1. Install Orca release (not necessarily build from zip).  
2. Point it at `idea-impl2` + one `thepipeline` project; run Grok CLI + one other agent.  
3. Write a half-page “friction log” in `notes/`.  
4. Only then design glue from project statuses → worktree spawn list.
