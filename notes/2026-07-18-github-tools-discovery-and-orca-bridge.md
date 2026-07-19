# GitHub per-project support, tool discovery, Orca, Hermes

**Status:** strategy note — do not build full stack now  
**Date:** 2026-07-18  
**Related:** operator fail-forward note, Orca/Grok integration note, agent-as-UI note

## Context (from discussion)

- Prefer **agent-driven** Orca (CLI / orchestration / headless), not permanent human steer.  
- Orca = optional **tool or Hermes-shaped path**, not factory replacement.  
- Valued Orca traits: manager spins subagents; **multiple PR / worktree trees**.  
- Question: does **GitHub support for individual pipeline projects** bridge gaps even without Orca?  
- Longer idea: agent **decides tools it needs** → search GitHub → crawl/read → evaluate → security loop → pull/use.  
- Even longer: own **app store / integration surface** for agentic tools (needs network effects; after factory + marketing stack).  
- GitHub as global tool supply = self-improve via world + agents contributing OSS.  
- Hermes already in runner — can it do discovery?

---

## 1. Per-project GitHub support — meaningful bridge?

**Yes — high leverage, Orca-independent.**

Today thepipeline projects are mostly **folders under `PIPELINE_DIR/projects/<slug>`**. Agents and tools that speak **git remotes, PRs, issues, Actions** cannot attach cleanly. Orca’s multi-PR/worktree model assumes a real repo.

### What “GitHub support” could mean (levels)

| Level | What | Bridge value |
|-------|------|----------------|
| **L1** | Each project is a **git repo** (local), optional private remote | Diffs, branches, rollback; Orca worktrees work |
| **L2** | Push to GitHub (org or `pipeline-<slug>`), default branch, README | External agents, CI, human review, Orca PR trees |
| **L3** | Issues/PRs as task surface; labels from factory status | Manager/meta-agent assigns work via GitHub API |
| **L4** | Actions CI = field-ish gates; release tags | Closer to “real product” packaging |
| **L5** | Template + capability publish to org | Early “internal app store” |

### Why meaningful even without Orca

- **Standard interface** for any coding agent (Grok CLI, Claude Code, Codex, Aider, OpenHands).  
- **Multi-PR trees** without Orca (native gh + worktrees).  
- **Fail-forward artifacts** become shareable/clonable, not only local disk.  
- **Security/review** can attach to PR (CODEOWNERS, scanners).  
- Aligns ship-prove with “merge only if green.”  
- Does **not** require network effects — works as private org with one user.

### What it does *not* buy alone

- Missions, corpus quality, field truth still factory problems.  
- Does not auto-discover world tools.  
- Public GitHub without hygiene = noise/secrets risk.

### Verdict

**Worth doing as a mid-term infrastructure step** on the replace-yourself ladder: makes the factory’s *outputs* legible to every git-native agent and to any future Orca path. Prioritize **L1→L2** before Orca glue.

---

## 2. Orca + manager subagents + multi-PR trees

With GitHub (or local git) projects:

- Meta-agent / manager: “slug X needs layout fix; slug Y needs field tests.”  
- Spawns Orca worktrees or native `git worktree` + agent CLIs per branch/PR.  
- Orchestration DAG optional (Orca experimental) or factory bus remains coordinator of *lifecycle*.

Factory still owns: what is in flight, ship status, missions.  
Orca/GitHub own: parallel code edits and PR comparison.

---

## 3. Tool decides tools: GitHub search → evaluate → secure → pull → use

### Desired loop

```
need capability
  → search GitHub (and/or registry)
  → clone/shallow fetch candidates
  → crawl README, structure, license, deps
  → evaluate fit (score vs need)
  → security loop (malware, typosquat, secret exfil, license, supply chain)
  → pin version / vendor / wrap as capability
  → invoke in sandbox
  → promote to capability registry if field-proven
```

### Feasibility

| Step | Feasible now? | Notes |
|------|----------------|-------|
| Search GitHub | **Yes** | `gh search`, GitHub API, web search |
| Crawl/read files | **Yes** | clone sparse, tree walk, README/LICENSE |
| Evaluate fit | **Partial** | LLM judge + heuristics; high false positive/negative |
| Security loop | **Partial–hard** | Static heuristics easy; real supply-chain security is deep |
| Pull and use | **Yes with sandbox** | venv, allowlisted commands (you already care about this hard value) |
| Auto-promote to production | **Dangerous** | Need quarantine + human/hard gate |

**Feasible as a staged capability** if:

1. **Quarantine** new tools (not trusted until proven).  
2. **Sandbox invoke** (existing hard value: no unsandboxed shell).  
3. **Pin** commit SHA / release tag.  
4. **License allowlist** (MIT/Apache/BSD preferred).  
5. **Human or hard gate** before promoting to default invoke-before-seed.  
6. Log every adoption for corpus/RSI.

**Not feasible safely as fully unsupervised “install anything from GitHub”** in the near term.

### Fit with self-improve

This *is* a self-improve layer: world + agents on GitHub become a tool market. It compounds *after* you can evaluate and field-test. Until then, it amplifies junk and risk.

---

## 4. Long-term: app store / integration surface

Makes sense **after**:

- Reliable factory (build + ship-prove),  
- Something worth publishing,  
- Optional marketing/network.

Until then, **GitHub + private capability registry** is the “store for one.”  
Public network effects are a later rung — don’t block the ladder on them.

---

## 5. Hermes — can it do this?

Hermes path today: **research-style goals** with worker/critic, not a dedicated supply-chain tool smith.

| Use Hermes for | Don’t expect Hermes alone for |
|----------------|-------------------------------|
| Survey “best MIT libs for X” | Trusted install into production |
| Write comparison docs (like URDF research) | Continuous registry curation |
| One-shot discovery reports | Secure sandbox invoke policy |

**Better split:**

- **Hermes (or dedicated discover agent):** search + shortlist + write evaluation memo.  
- **Capability pipeline (new or extended registry):** security checklist, pin, quarantine, sandbox test, promote.  
- **Executor / Orca:** integrate chosen tool into a project.  
- **Ship-prove:** prove the *using* project still works.

Specific existing solution classes (not endorsements):

- `gh` + GitHub code search  
- Security: OpenSSF Scorecard, Dependabot, pip-audit, osv-scanner (as gates, not magic)  
- Agent frameworks that “use tools” still need *your* quarantine policy  
- Your **capability registry + invoke whitelist** is the right *home* for “approved tools”

---

## 6. Recommended order (aligned with fail-forward)

1. **Git per project (L1)** — local repo at least; enables worktrees/PRs mentally.  
2. **Optional GitHub remote (L2)** — private org; independent of Orca.  
3. **Discover-as-research** — Hermes or one-shot agent: shortlist tools into markdown; human/meta-agent approves.  
4. **Quarantine + pin + sandbox invoke** — only then auto-use.  
5. **Orca optional path** — agent-driven CLI against git-backed projects.  
6. **Public app store / network** — much later.

---

## Non-goals now

- Auto-install random GitHub repos into the factory runtime.  
- Public marketplace.  
- Replacing capability registry with “just npm/pip install whatever.”  
- Blocking ship-prove progress on Orca or GitHub.

## Open questions

- Monorepo vs one-repo-per-project for thepipeline?  
- When is a project “born” as a git repo (seed time vs complete)?  
- Org structure: `avatardebris-debug/pipeline-projects/*` vs single monorepo with packages?  
- Security bar for auto-pull: MIT-only? stars threshold? maintainer age?  
