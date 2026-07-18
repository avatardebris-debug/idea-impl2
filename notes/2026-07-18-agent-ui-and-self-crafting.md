# Future: agent as UI, system crafts toward the person

**Status:** note only — do not build now  
**Date:** 2026-07-18  
**Context:** mission/values in `master_ideas.md`, factory complexity, mental fatigue of many files and knobs

## Intent

Sometime in the future, introduce an **AI agent that understands this whole system** so the
**UI is just interacting with that agent**.

### Why

- The user should not need to know complicated backend details (queues, ship-prove,
  `PIPELINE_DIR`, seed policy, prompt files, etc.).
- The user should not even need to keep a working document of ideas if they do not want to.
- Longer term: **let the system craft itself toward what the person wants** — missions,
  goals, and software emerge from dialogue and observed preference, not from the human
  operating five surfaces (master_ideas, mission.yaml, dropbox, COMMANDS, cloud scripts).

### Relationship to current design

Today we deliberately simplified toward **one ops surface** for product missions/values
(`master_ideas.md`) plus rare hard rules (`mission.yaml`) and live steer (`dropbox.md`).
That is the right *manual* layer.

The agent-UI is the next layer **on top**: it would edit those surfaces (or replace the
need to touch them) on the user’s behalf, with human gates for hard-value demotion,
deletes, and factory self-modification.

### Non-goals for now

- No new agent process or chat UI in the runner.
- No auto-rewrite of factory architecture without explicit product decision.
- Does not replace ship-prove / field validation; still need truth on disk for software.

### Open questions

- Where does conversation history live (output repo vs factory)?
- How much may the agent change without dropbox-style confirmation?
- How does this compose with multi-mission construct/deconstruct already in ideator?
