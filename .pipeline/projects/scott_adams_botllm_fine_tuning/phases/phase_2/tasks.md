# Phase 2 Tasks

- [ ] Task 1: Package scaffolding — pyproject.toml, sacbot package structure
  - What: Create the `sacbot` Python package with proper project layout, dependencies, and entry points. This is the foundation for all Phase 2 code.
  - Files:
    - `workspace/pyproject.toml` — project metadata (name=sacbot, version=0.1.0), dependencies (openai>=1.0.0, tiktoken>=0.5.0, click>=8.1.0, pytest>=7.0.0, pandas>=2.0.0, textstat>=0.7.0, nltk>=3.8.0), CLI entry point `sacbot=sacbot.cli:main`
    - `workspace/sacbot/__init__.py` — package init, exports `generate()` at the top level
    - `workspace/sacbot/cli.py` — empty stub (filled in Task 4)
    - `workspace/sacbot/generator.py` — empty stub (filled in Task 2)
    - `workspace/sacbot/types.py` — empty stub (filled in Task 3)
    - `workspace/sacbot/eval.py` — empty stub (filled in Task 5)
    - `workspace/tests/` — test directory
    - `workspace/tests/test_package.py` — smoke test: `import sacbot` succeeds, `sacbot.generate()` raises a clear "LLM API key not configured" error
  - Done when: `pip install -e .` succeeds from the workspace root, `import sacbot` works, and the smoke test passes with `pytest tests/`.

- [ ] Task 2: Content generator core — prompt assembly, few-shot selection, LLM call
  - What: Implement the core `generate()` function in `sacbot/generator.py` that assembles a prompt from the Phase 1 style template, selects few-shot examples from the corpus, calls an LLM API, and returns generated text.
  - Files:
    - `workspace/sacbot/generator.py` — `generate(topic: str, content_type: str = "blog", model: str = "gpt-4o", api_key: str | None = None) -> str` that:
      1. Loads the style prompt template from `prompts/style_prompt_template.md`
      2. Loads 5 diverse few-shot examples from `corpus/processed/corpus.jsonl` (stratified by source_type: at least 1 blog, 1 tweet, 1 book)
      3. Assembles the full prompt: system instruction + few-shot examples + topic-specific task description
      4. Calls the LLM API (OpenAI client) with appropriate temperature (0.7-0.9 for creativity)
      5. Returns the generated text
    - `workspace/sacbot/few_shot.py` — `select_few_shot(corpus_path: str, n: int = 5) -> list[dict]` that picks diverse examples: filters out samples < 50 chars, stratifies by source_type, picks the first N from each stratum (round-robin), returns list of {text, source_type} dicts
    - `workspace/sacbot/prompts.py` — `build_prompt(topic: str, content_type: str, few_shot_examples: list[dict]) -> dict[str, str]` that returns `{"system": ..., "user": ...}` message dicts. The system message encodes the style guidelines from the Phase 1 analysis. The user message includes the few-shot examples and the topic task.
  - Done when: `sacbot.generate("why systems beat goals", "blog")` returns a 300-500 word text string without errors (given a valid API key), the few-shot selector returns exactly 5 examples spanning at least 2 source types, and the prompt builder produces valid OpenAI-format messages.

- [ ] Task 3: Content type support — blog, tweet, LinkedIn templates and constraints
  - What: Add content-type-specific prompt assembly and output constraints so the generator produces appropriately formatted content for each type.
  - Files:
    - `workspace/sacbot/types.py` — define `ContentType = Literal["blog", "tweet", "linkedin"]` and a `CONTENT_SPECS` dict mapping each type to:
      - `name`: display name
      - `min_words`: minimum word count (blog=300, tweet=280 chars, linkedin=200)
      - `max_words`: maximum word count (blog=500, tweet=280 chars, linkedin=1000)
      - `format_instructions`: type-specific formatting notes (e.g., tweets need line breaks between threads, LinkedIn needs professional tone)
      - `prompt_suffix`: a content-type-specific instruction appended to the task description
    - `workspace/sacbot/generator.py` — extend `generate()` to accept `content_type`, validate against `CONTENT_SPECS`, and append type-specific formatting instructions to the prompt
    - `workspace/sacbot/formatters.py` — post-processing functions: `format_tweet_thread(text: str) -> str` (splits long output into 280-char chunks with thread markers), `format_blog_post(text: str) -> str` (ensures paragraph breaks, short paragraphs), `format_linkedin_post(text: str) -> str` (ensures professional tone, appropriate length)
  - Done when: `generate("topic", "blog")` returns 300-500 words, `generate("topic", "tweet")` returns text under 280 chars (or a properly threaded list), `generate("topic", "linkedin")` returns 200-1000 words, and all three types produce text with appropriate formatting (paragraph breaks for blog, thread markers for tweets, professional tone for LinkedIn).

- [ ] Task 4: CLI tool — `sacbot generate` command
  - What: Build a Click-based CLI that exposes the generator as a command-line tool with topic, type, model, and output format arguments.
  - Files:
    - `workspace/sacbot/cli.py` — Click CLI with:
      - `sacbot generate --topic TEXT --type [blog|tweet|linkedin] [--model MODEL] [--output json|text] [--api-key KEY]`
      - `sacbot evaluate --samples PATH --ground-truth PATH` (placeholder for eval harness)
      - Proper help text, validation (topic required, type must be valid), and error handling
    - `workspace/pyproject.toml` — ensure `[project.scripts]` entry maps `sacbot` to `sacbot.cli:main`
  - Done when: `sacbot generate --topic "systems over goals" --type blog` prints Scott Adams-style blog post text to stdout, `sacbot generate --topic "morning routine" --type tweet` prints a tweet, `sacbot generate --topic "test" --type linkedin --output json` prints JSON with `{"text": "...", "type": "linkedin"}`, and all three commands complete in < 30 seconds.

- [ ] Task 5: Evaluation harness — automated metrics + human eval interface
  - What: Build an evaluation module that compares generated text against ground-truth corpus samples using automated style metrics, and provides a human evaluation interface.
  - Files:
    - `workspace/sacbot/eval.py` — evaluation functions:
      - `style_similarity_score(gen_text: str, corpus_samples: list[str]) -> dict` — computes: (a) n-gram overlap (BLEU-1/2, ROUGE-L) against corpus samples, (b) sentiment similarity (VADER) vs corpus average, (c) sentence length distribution KL-divergence, (d) keyword frequency similarity (top 20 corpus words), (e) contrarian framing ratio (ratio of "most people"/"actually"/"the truth is" phrases), (f) probability framing ratio (ratio of "probability"/"likely"/"chances" phrases)
      - `human_eval_template(corpus_samples: list[str], generated_samples: list[str]) -> str` — generates a blind evaluation form: presents corpus samples and generated samples in random order, asks raters to identify which are "possibly Scott Adams"
      - `compute_correlation(human_scores: list[float], automated_scores: list[float]) -> float` — Pearson correlation between human and automated scores
    - `workspace/tests/test_eval.py` — tests that style_similarity_score returns a dict with all expected keys, human_eval_template produces valid output, and compute_correlation works on sample data
    - `workspace/eval_data/` — directory for evaluation results (ground truth samples, generated samples, scores)
  - Done when: `style_similarity_score()` computes all 6 metrics without errors on sample data, `human_eval_template()` produces a readable evaluation form, and the correlation function returns a valid Pearson r value. Automated metrics must be documented as approximations (not ground truth).

- [ ] Task 6: Integration testing, prompt refinement, and documentation
  - What: Run end-to-end tests, refine few-shot examples based on output quality, and write comprehensive documentation.
  - Files:
    - `workspace/tests/test_integration.py` — integration tests:
      - `test_generate_blog()` — generates blog post, checks word count 300-500, checks for Scott Adams style markers (probability words, direct address)
      - `test_generate_tweet()` — generates tweet, checks char count < 280
      - `test_generate_linkedin()` — generates LinkedIn post, checks word count 200-1000
      - `test_cli_runs()` — runs `sacbot generate --topic "test" --type blog` via subprocess, checks exit code 0 and output is non-empty
      - `test_few_shot_diversity()` — verifies few-shot selection includes multiple source types
    - `workspace/prompts/style_prompt_template.md` — update with refined few-shot examples based on evaluation results (select the 5 examples that produce the best generation quality)
    - `workspace/README.md` — update with Phase 2 section: sacbot package usage, CLI commands, evaluation instructions, known limitations
    - `workspace/docs/usage.md` — detailed usage guide: installation, quick start, CLI reference, programmatic API, evaluation guide, prompt engineering tips, limitations (API key required, style matching is approximate, copyright considerations)
  - Done when: All integration tests pass, the README documents Phase 2 features, `docs/usage.md` covers all CLI commands and the programmatic API, and the few-shot examples in the prompt template are the top 5 by generation quality (verified by running `generate()` on 10 diverse topics and reviewing output).