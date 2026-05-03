# Phase 2 Review — Content Generation & Evaluation Harness

## Verdict: FAIL — Requires Fixes Before Merge

---

## 1. Architecture Overview

Phase 2 delivers a working content generation pipeline with the following components:

| File | Purpose |
|------|---------|
| `sacbot/types.py` | Content type definitions (`ContentType` literal, `ContentSpec` dataclass, `CONTENT_SPECS` dict) |
| `sacbot/generator.py` | Core generation: few-shot selection, prompt building, LLM call, orchestration |
| `sacbot/cli.py` | Click-based CLI entry point |
| `sacbot/eval.py` | Evaluation harness: automated metrics, human eval interface |
| `sacbot/__init__.py` | Package init with `generate()` export |
| `tests/test_generator.py` | 22 tests for generator module |
| `tests/test_types.py` | 7 tests for types module |
| `tests/test_eval.py` | 11 tests for eval module |
| `prompts/style_prompt_template.md` | Style prompt template |
| `corpus.jsonl` | Corpus data for few-shot examples |

---

## 2. Critical Issues (Must Fix)

### 2.1 [CRITICAL] CLI `generate_content` passes incompatible arguments to `generate()`

**File:** `sacbot/cli.py`

The `generate_content` CLI command accepts and forwards these parameters to `generate()`:
- `n_few_shot`
- `model`
- `api_key`
- `temperature`
- `seed`
- `output_format`

But `generate()` in `sacbot/generator.py` only accepts three parameters:
```python
def generate(topic: str, content_type: str, corpus_path: str) -> GenerationResult:
```

**Impact:** Running `sacbot generate-content --topic test` will raise a `TypeError` at runtime. The CLI is completely non-functional.

**Fix:** Either:
- (A) Update `generate()` to accept the extra parameters (`n_few_shot`, `model`, `api_key`, `temperature`, `seed`, `output_format`) and pass them through the pipeline, or
- (B) Remove the extra CLI options and keep `generate()` as-is (simpler, but loses configurability).

### 2.2 [CRITICAL] `call_llm()` ignores `max_tokens` from `CONTENT_SPECS`

**File:** `sacbot/generator.py`

`generate()` looks up `spec.max_tokens` from `CONTENT_SPECS` but never passes it to the LLM call:

```python
spec = CONTENT_SPECS[content_type]
target_length = spec.target_length
# ...
# call_llm() hardcodes model="gpt-4o" and never uses max_tokens
```

The `client.chat.completions.create()` call does not include `max_tokens`, so the LLM can return arbitrarily long output, potentially exceeding the `max_length_chars` constraint in `ContentSpec`.

**Fix:** Pass `max_tokens=spec.max_tokens` to `client.chat.completions.create()`.

### 2.3 [CRITICAL] `test_package.py` is effectively empty

**File:** `tests/test_package.py`

Contains only a docstring — no actual tests. This means the package-level import (`from sacbot import generate`) is never verified by the test suite.

**Fix:** Add at least a smoke test:
```python
def test_package_import():
    from sacbot import generate
    assert callable(generate)
```

---

## 3. Medium Issues (Should Fix)

### 3.1 `build_prompt()` `output_format` parameter is unused

**File:** `sacbot/generator.py`

`build_prompt()` accepts an `output_format` parameter but never uses it in the prompt string. The `CONTENT_SPECS` dict has `output_instruction` fields (e.g., `'Return JSON with keys: "title", "content", "tags"...'`) that should be included in the prompt for the content type being generated.

**Fix:** Include `spec.output_instruction` in the prompt:
```python
prompt += f"Output Format: {spec.output_instruction}\n\n"
```

### 3.2 `call_llm()` hardcodes model name

**File:** `sacbot/generator.py`

`call_llm()` hardcodes `model="gpt-4o"`. The CLI has a `--model` option, but it's never passed through to `generate()` (see issue 2.1). The model should be configurable.

**Fix:** Add `model` parameter to `call_llm()` and `generate()`.

### 3.3 `call_llm()` hardcodes `temperature`

**File:** `sacbot/generator.py`

`call_llm()` hardcodes `temperature=0.7`. The CLI has a `--temperature` option, but it's never passed through.

**Fix:** Add `temperature` parameter to `call_llm()` and `generate()`.

### 3.4 `api_key` is accepted by CLI but never used

**File:** `sacbot/cli.py`

The `--api-key` option is accepted but never set on the OpenAI client. The `OpenAI()` constructor can accept `api_key=...` as a keyword argument.

**Fix:** Pass `api_key=api_key` to `OpenAI()` in `call_llm()`.

### 3.5 `seed` parameter is accepted by CLI but never used

**File:** `sacbot/cli.py` / `sacbot/generator.py`

The `--seed` option is accepted but never passed to the LLM call. OpenAI supports `seed` parameter for reproducibility.

**Fix:** Pass `seed=seed` to `client.chat.completions.create()` if seed is not None.

---

## 4. Minor Issues

### 4.1 `generate_human_eval_prompts()` prints to stdout

**File:** `sacbot/eval.py`

`generate_human_eval_prompts()` uses `print()` instead of returning or using a logger. This is inconsistent with the rest of the codebase which uses dataclasses and return values.

**Fix:** Return the path or suppress the print.

### 4.2 `_compute_style_match()` is a heuristic with no validation

**File:** `sacbot/eval.py`

The style match score is a simple keyword-counting heuristic. The docstring acknowledges this ("A more sophisticated version would use a trained classifier or embedding similarity"), but there's no test coverage for it.

**Fix:** Add tests for `_compute_style_match()` and consider documenting its limitations.

### 4.3 `compute_aggregate_metrics()` returns `per_topic` and `per_content_type` but they're not used

**File:** `sacbot/eval.py`

The `EvaluationReport` dataclass includes `per_topic` and `per_content_type` fields, and `compute_aggregate_metrics()` populates them, but there's no downstream consumer. Consider adding a method to `EvaluationReport` to format/display these.

### 4.4 `test_package.py` should verify `__all__`

**File:** `tests/test_package.py`

The package exports `generate` via `__all__`. The test should verify this contract.

---

## 5. Positive Observations

- **Good test coverage for generator logic:** The few-shot selection, topic overlap, and length similarity functions are well-tested with edge cases (empty inputs, exact matches, partial matches).
- **Clean dataclass design:** `FewShotSample`, `GenerationResult`, `ContentSpec`, `SampleMetrics`, and `EvaluationReport` are all well-structured.
- **Evaluation harness is comprehensive:** Automated metrics (word count, readability, sentiment, ROUGE-L, style match) plus human eval interface provide a solid evaluation foundation.
- **Corpus loading is robust:** `_load_corpus()` gracefully handles invalid JSON lines and empty files.
- **Type hints are consistent:** All public functions have proper type annotations.
- **`CONTENT_SPECS` design is extensible:** Adding a new content type (e.g., `"newsletter"`) is straightforward — just add an entry to the dict.

---

## 6. Summary of Required Changes

| Priority | Issue | File | Lines |
|----------|-------|------|-------|
| **Critical** | CLI passes incompatible args to `generate()` | `cli.py` | 100-110 |
| **Critical** | `max_tokens` not passed to LLM | `generator.py` | 170-180 |
| **Critical** | `test_package.py` is empty | `test_package.py` | 1 |
| **Medium** | `output_format` unused in `build_prompt()` | `generator.py` | 130-140 |
| **Medium** | Model hardcoded in `call_llm()` | `generator.py` | 160-170 |
| **Medium** | Temperature hardcoded in `call_llm()` | `generator.py` | 160-170 |
| **Medium** | `api_key` accepted but not used | `cli.py` | 100-110 |
| **Medium** | `seed` accepted but not used | `cli.py` / `generator.py` | 100-110, 160-170 |

---

## 7. Recommendation

**Do not merge.** The CLI is non-functional due to the parameter mismatch (Issue 2.1), and the LLM call ignores the `max_tokens` constraint (Issue 2.2). These are blocking issues that prevent the tool from working as designed.

The remaining medium and minor issues are fixable in a follow-up PR. The architecture is sound and the test coverage for the core logic is good.
