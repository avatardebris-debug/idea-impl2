## Phase 3: Polish, CLI UX, and Evaluation Pipeline Integration

**Description:**
Improve CLI ergonomics, add batch mode (compare multiple sim videos against one real video), add config file support, and produce a polished README with example workflows. Add optional integration hooks for the broader pipeline (e.g., output format compatible with downstream evaluation dashboards).

**Deliverable:**
- Enhanced CLI: `--config`, `--weights`, `--fps`, `--frame-range`, `--no-heatmaps` flags
- Batch mode: compare one real video against multiple sim videos
- Config file (YAML) for default settings
- README with examples, installation, and sim-to-real evaluation workflow
- Optional: output in a format consumable by pipeline evaluation dashboards
- Performance optimizations: frame caching, parallel frame processing

**Dependencies:**
- Phase 2 code (all metrics, heatmaps, CLIP)
- `click` or `typer` for CLI (if not already used)
- `pyyaml` for config file support
- `tqdm` for progress bars

**Success Criteria:**
- [ ] All CLI flags work correctly
- [ ] Batch mode compares N sim videos against 1 real video in one run
- [ ] Config file loads and overrides defaults
- [ ] Heatmaps can be disabled to save disk space
- [ ] README has installation guide + 3 example workflows
- [ ] Performance: processes 30fps, 60s video in under 5 minutes (CPU)
- [ ] All tests pass (unit + integration)

---

## File Mapping: What to Import from `video_ingestor_summary`

| From `video_ingestor_summary` | Used? | Notes |
|-------------------------------|-------|-------|
| `video_ingestor.models.JobStatus` | ❌ | Not needed — no job tracking |
| `video_ingestor.models.TranscriptSegment` | ❌ | Audio transcription model, irrelevant |
| `video_ingestor.IngestionPipeline` | ❌ | Video download/transcription pipeline |
| `video_ingestor.Storage` | ❌ | SQLite job storage |
| `video_ingestor.EmbeddingGenerator` | ❌ | Sentence-transformers, not CLIP |
| `video_ingestor.VectorStore` | ❌ | ChromaDB for text search |
| `video_ingestor.Summarizer` | ❌ | LLM summarization |
| `video_ingestor.config.Settings` | ❌ | Pattern inspiration only |
| `video_ingestor.__init__.py` exports | ❌ | No imports needed |

**Conclusion:** Zero imports from `video_ingestor_summary`. The dependency is a pipeline peer for video ingestion/Q&A, not a functional dependency for visual similarity computation.

## Success Criteria (Overall Project)

- [ ] MVP (Phase 1) ships: frame extraction + SSIM + pHash + JSON report
- [ ] CLIP + heatmaps (Phase 2) ship: all three metrics + PNG heatmaps
- [ ] Polish (Phase 3) ships: batch mode, config, CLI UX, docs
- [ ] Global score is interpretable: 1.0 = identical, 0.0 = completely different
- [ ] Tool works on CPU (no GPU required, GPU optional for CLIP speedup)
- [ ] Compatible with MuJoCo render outputs (PNG frame sequences or MP4)
- [ ] All tests pass