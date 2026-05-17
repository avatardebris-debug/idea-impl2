## Phase 2: Recipe Enrichment & Structured Output
- **Description**: Enhance the recipe output with inferred metadata — ingredient lists, equipment needed, difficulty estimation, estimated total time, and alternative phrasing suggestions. Add support for multiple video formats and improve frame extraction quality.
- **Deliverable**: 
  - Recipe objects with enriched fields: `ingredients`, `equipment`, `difficulty` (easy/medium/hard), `estimated_time_minutes`, `key_takeaways`
  - Support for MP4, MOV, AVI, and YouTube URLs
  - Adaptive frame extraction (more frames during fast-motion, fewer during static shots)
  - A `--enrich` flag that triggers the enrichment pipeline
- **Dependencies**: Phase 1
- **Success criteria**:
  - Processing the same 30-second video now produces 7+ enriched fields
  - Ingredient list contains at least 3 items for cooking videos (validated against ground truth)
  - Adaptive frame extraction reduces total frames processed by ~30% without losing step detection accuracy
  - All supported video formats produce equivalent output quality

