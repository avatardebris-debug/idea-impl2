# Phase 1 Tasks

- [x] Task 1: Project scaffolding and data schema
  - What: Create the project directory structure, requirements file, and define the JSONL data schema for corpus samples. Set up the base layout for all Phase 1 code.
  - Files:
    - `workspace/requirements.txt` — Python dependencies (requests, beautifulsoup4, nltk, pandas, collections)
    - `workspace/schema.json` — JSON schema defining the corpus sample structure: {id, text, source_type (blog|tweet|book|interview), source_url, date, author, raw_html (optional)}
    - `workspace/corpus/` — directory for all corpus data
    - `workspace/corpus/raw/` — raw scraped content
    - `workspace/corpus/processed/` — cleaned JSONL output
    - `workspace/analysis/` — directory for analysis outputs
    - `workspace/analysis/style_report.md` — final style analysis report
    - `workspace/prompts/` — directory for prompt templates
  - Done when: All directories exist, requirements.txt lists the needed packages, schema.json defines the corpus sample format with all required fields, and `pip install -r requirements.txt` succeeds.

- [x] Task 2: Corpus scraper and deduplication pipeline
  - What: Build a scraper that collects writing samples from scottadamsslog.com (blog posts), Twitter/X archives, and book excerpts (fair use), then cleans and deduplicates the results into a structured JSONL corpus of 500-1000 samples.
  - Files:
    - `workspace/scraper/scott_adams_blog.py` — scraper for scottadamsslog.com blog posts (fetches article pages, extracts title, date, body text)
    - `workspace/scraper/twitter_archives.py` — scraper for Twitter/X content (reads from archived CSV/JSON files or uses a public archive API)
    - `workspace/scraper/book_excerpts.py` — module for ingesting book excerpts from fair-use sources (reads from a provided text directory)
    - `workspace/scraper/cleaner.py` — removes boilerplate, ads, navigation, comments; normalizes whitespace; deduplicates by text similarity (minhash or simple hash-based dedup)
    - `workspace/scraper/main.py` — orchestrator that runs all scrapers, applies cleaning, and writes the final corpus to `workspace/corpus/processed/corpus.jsonl`
  - Done when: `python workspace/scraper/main.py` runs end-to-end, produces `corpus.jsonl` with ≥500 unique samples spanning at least 3 years and at least 2 source types, and each sample conforms to the schema defined in Task 1.

- [x] Task 3: Quantitative and qualitative style analysis
  - What: Analyze the corpus for stylistic features — sentence length distributions, word frequency, rhetorical devices, humor markers, recurring themes, contrarian patterns, and "Stack of Luck" framing — and produce a comprehensive style report.
  - Files:
    - `workspace/analysis/quantitative.py` — computes: average/median sentence length, paragraph length distribution, top-100 word frequencies (with stop-word filtering), part-of-speech ratios, exclamation/question mark frequency, contrarian keyword frequency (e.g., "most people," "actually," "the truth is"), humor marker frequency (punchline patterns, irony markers)
    - `workspace/analysis/qualitative.py` — identifies recurring themes (e.g., management, luck, probability, common sense, systems vs. goals), categorizes contrarian framing patterns, detects "Stack of Luck" references, and flags tone (humorous, serious, motivational, cynical) per sample
    - `workspace/analysis/style_report.md` — writes the full style analysis report with: (a) corpus statistics (sample counts by type/year), (b) ≥10 distinct stylistic features with quantitative measurements, (c) qualitative findings (recurring themes, contrarian patterns, tone distribution), (d) key takeaways for prompt engineering
  - Done when: `python workspace/analysis/quantitative.py` and `python workspace/analysis/qualitative.py` run without errors, the style report documents at least 10 distinct stylistic features with numbers, and covers all required categories (sentence length, paragraph structure, humor patterns, recurring themes, rhetorical devices, tone distribution).

- [x] Task 4: Style prompt template with few-shot examples
  - What: Draft a reusable style prompt template that captures the key stylistic features identified in the analysis, including 5 few-shot examples from the corpus.
  - Files:
    - `workspace/prompts/style_prompt_template.md` — a prompt template containing: (a) a system instruction describing Scott Adams' writing style based on the analysis (tone, sentence structure, humor approach, thematic focus, contrarian framing), (b) 5 carefully selected few-shot examples from the corpus (spanning blog, tweet, and book types), (c) a placeholder for the user's topic input
    - `workspace/prompts/README.md` — brief instructions on how to use the template (which LLMs it was tested with, tips for adjusting tone, how to swap few-shot examples)
  - Done when: The prompt template is a complete, self-contained prompt that can be pasted into any LLM, includes exactly 5 diverse few-shot examples from the corpus, and the README documents usage instructions. The template is ready for evaluation in Phase 2.