## Phase 2 — Character Consistency & Visual Planning

**Goal:** Add robust character management, visual identity systems, and AI image/storyboard prompt generation.

**Description:**
This phase extends the pipeline with:
1. **Character Registry** — Deep character profiles with: physical appearance, voice notes, personality traits, backstory, costume descriptions, and a "visual anchor" (key visual reference). Characters are versioned and cross-referenced across all scenes.
2. **Character Consistency Engine** — Ensures characters are described identically across all scenes. Generates a "character sheet" prompt optimized for AI image generation (Midjourney, DALL-E, Stable Diffusion).
3. **Storyboard Prompt Generator** — For each scene, generates AI image generation prompts with:
   - Character appearance (pulled from registry)
   - Scene composition, camera angle, lighting, mood
   - Style guidance (e.g., "cinematic, 35mm film, anamorphic lens")
   - Negative prompts and parameters
4. **Visual Mood Board** — Aggregates generated prompts and allows users to collect reference images per scene/character.
5. **Scene-to-Image Pipeline** — Optional integration with image generation APIs (Midjourney via Discord bot, DALL-E API, or local Stable Diffusion) to produce actual storyboard frames.

**Deliverable:**
- `characters.json` — enriched character registry with visual anchors and cross-scene consistency
- `storyboard_prompts/` — per-scene AI image prompts with parameters
- `mood_boards/` — per-character and per-scene visual reference collections
- Optional: live image generation integration (configurable per user)

**Dependencies:**
- Phase 1 (screenplay core must be complete)
- Image generation API access (optional for MVP of this phase)

**Success Criteria:**
- [ ] Character registry enforces consistent visual descriptions across all scenes
- [ ] Each character has a generated "character sheet" prompt for AI image models
- [ ] Each scene has 1-3 storyboard prompts with camera, lighting, and style guidance
- [ ] Prompts are optimized for the target image model (user-selectable)
- [ ] Mood boards can be assembled and exported per character and per scene
- [ ] User can generate actual storyboard images (if API connected) and review them

---

#