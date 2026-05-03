## Phase 2: Prompt-Engineered Content Generator (Quick Validation)

**Description**: Build a content generator using prompt engineering with the style analysis from Phase 1. This validates the approach quickly before investing in fine-tuning.

**Deliverable**:
- A Python package `sacbot` with a `generate()` function that takes a topic and produces Scott Adams-style content
- Support for multiple content types: blog post, tweet thread, LinkedIn post
- CLI tool `sacbot generate --topic "..." --type blog`
- Evaluation harness that compares generated text to ground-truth samples using style metrics

**Dependencies**: Phase 1 (corpus + style analysis)

**Success Criteria**:
- Generated blog posts (300-500 words) achieve ≥ 50% "possibly Scott Adams" in blind human evaluation (10+ raters)
- Generated tweets capture his contrarian humor style (≥ 60% accuracy in blind evaluation)
- Evaluation metrics (perplexity, n-gram overlap, sentiment) correlate with human judgment (r ≥ 0.5)
- CLI tool runs end-to-end in < 30 seconds per generation

**Tasks**:
- [ ] Task 9: Package scaffolding — pyproject.toml, sacbot package structure
- [ ] Task 10: Implement content generator — prompt templates, few-shot selection, generation logic
- [ ] Task 11: Content type support — blog, tweet, LinkedIn templates
- [ ] Task 12: CLI tool — `sacbot generate` command with topic/type/format args
- [ ] Task 13: Evaluation harness — automated metrics + human eval interface
- [ ] Task 14: Iterative prompt refinement — test with real raters, refine few-shot examples
- [ ] Task 15: Write documentation — usage, style guide, limitations

---

