## Phase 2: CLIP Integration + Per-Frame Heatmaps

**Description:**
Add CLIP embedding cosine similarity as the third metric. Generate per-frame heatmap overlays (PNG) showing pixel-level difference regions. Improve frame alignment logic.

**Deliverable:**
- CLIP embedding computation using `clip` (openai/clip) or `transformers` CLIP
- Cosine similarity per frame
- Heatmap generation: difference maps rendered as color-coded overlays saved as PNG
- Updated JSON report with CLIP scores
- Frame alignment: FPS normalization, configurable frame range

**Dependencies:**
- `clip` (openai/clip) or `transformers` + `torch` for CLIP
- `matplotlib` or `PIL` + `numpy` for heatmap rendering
- Phase 1 code (frame extraction, SSIM, pHash)

**Success Criteria:**
- [ ] CLIP cosine similarity computed per frame
- [ ] Heatmap PNGs generated for each frame (saved to output dir)
- [ ] JSON report includes all three metrics per frame
- [ ] Global score updated to include CLIP component
- [ ] FPS normalization works correctly
- [ ] Heatmaps visually show difference regions
- [ ] Integration tests with real+sim video pairs pass

---

#