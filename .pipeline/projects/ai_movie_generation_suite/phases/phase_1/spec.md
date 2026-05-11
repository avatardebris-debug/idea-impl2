## Phase 1 — Screenplay Writing Core (MVP)

**Goal:** Ship a functional screenplay development tool that takes a story concept and produces a complete beat sheet, full script, scene descriptions, and dialogue.

**Description:**
This phase builds the core pipeline:
1. **Beat Sheet Generator** — Uses Save-the-Cat (Blake Snyder) beat structure. User provides a logline; the system generates a structured beat sheet with all 15 beats mapped.
2. **Script Writer** — Expands each beat into formatted screenplay scenes using industry-standard format (Final Draft-compatible).
3. **Scene Description Engine** — For each scene, generates detailed visual direction: setting, lighting, camera angles, mood, action beats.
4. **Dialogue Generator** — Produces character-specific dialogue with voice differentiation.
5. **Project Manager** — CLI/GUI for managing projects, saving/loading, and navigating between beats, scenes, and characters.

**Deliverable:**
- A working CLI (with optional simple web UI) that accepts a logline and outputs:
  - `beats.json` — structured beat sheet
  - `script.fdx` (or `.fdx`-compatible JSON) — formatted screenplay
  - `scenes/` directory — detailed scene descriptions per scene
  - `characters.json` — initial character roster with basic descriptions
- All output is machine-readable and structured for downstream phases.

**Dependencies:**
- None (standalone MVP)
- Requires LLM API access (GPT-4o or Claude 3.5 Sonnet recommended)

**Success Criteria:**
- [ ] User can input a logline and generate a complete Save-the-Cat beat sheet (15 beats)
- [ ] Beat sheet is exportable to standard screenplay format
- [ ] Script is generated with proper scene headings, action lines, character names, and dialogue
- [ ] Scene descriptions include visual direction, camera notes, and mood
- [ ] Dialogue is character-consistent (each character has a distinguishable voice)
- [ ] Project can be saved and reloaded without data loss
- [ ] User can edit any beat/scene/character and regenerate downstream content

---

#