## Phase 3 — 3D World & Character Export Pipeline

**Goal:** Enable export of characters and environments into 3D pipelines (starting with Unreal Engine 5) for previsualization and final production.

**Description:**
This phase adds the bridge between creative writing and 3D production:
1. **3D Character Description Generator** — Translates character registry entries into 3D character specifications:
   - Body proportions, facial structure, skin texture notes
   - Costume topology and material specifications
   - Rigging requirements (humanoid, proportions, facial blendshapes)
   - Export format recommendations (FBX, USD, GLTF)
2. **Environment/World Builder** — Generates scene environment descriptions suitable for 3D world creation:
   - Spatial layout, dimensions, architectural style
   - Material and lighting specifications
   - Consistent world bible (all scenes share the same world rules)
3. **UE5 Integration Pipeline** — Export formats and workflows for Unreal Engine 5:
   - FBX character export with rigging metadata
   - USD scene export for environment previsualization
   - MetaHuman-compatible character descriptions (for MetaHuman Creator integration)
   - Blueprint integration for scene sequencing
4. **World Consistency Engine** — Maintains a "world bible" ensuring all scenes, characters, and environments share consistent rules (physics, art style, color palette, scale).
5. **Previsualization Pipeline** — Optional: generates basic UE5 Blueprints or USD scenes from the world bible for rough previsualization.

**Deliverable:**
- `characters_3d/` — per-character 3D specifications and export-ready files
- `environments/` — per-scene environment descriptions and 3D asset specs
- `world_bible.json` — consistent world rules, art direction, and style guide
- `ue5_export/` — UE5-compatible export files (FBX, USD, Blueprint templates)
- Integration scripts for importing characters and environments into UE5

**Dependencies:**
- Phase 2 (character registry and visual descriptions must be complete)
- UE5 installed (for testing integration)
- 3D asset pipeline knowledge (FBX/USD export, MetaHuman workflow)

**Success Criteria:**
- [ ] Character descriptions include 3D-ready specifications (proportions, rigging, materials)
- [ ] World bible enforces consistency across all scenes and characters
- [ ] Characters can be exported as FBX/USD with proper rigging metadata
- [ ] Environments can be exported as USD for UE5 previsualization
- [ ] UE5 import pipeline works end-to-end (characters + environments load correctly)
- [ ] World bible can be exported as a style guide for human artists

---

## 4. Architecture Notes

### Data Model (Core)

```
project/
├── project.json              # Project metadata, logline, genre, tone
├── beats.json                # Save-the-Cat beat sheet (15 beats)
├── script.json               # Formatted screenplay (scene-by-scene)
├── characters.json           # Character registry (Phase 1+)
├── characters_3d/            # 3D ch