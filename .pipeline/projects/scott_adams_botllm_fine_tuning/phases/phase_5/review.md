# Code Review — Phase 5

## Files Reviewed
- `sacbot/review.py` — Content review system (style checks, quality filters, hallucination detection)

## Blocking Bugs
- **None** — The review file was previously missing (placeholder content only). This review has now been generated.

## Non-Blocking Notes

### 1. Code Duplication: `_compute_style_match` (Medium)
`_compute_style_match` in `review.py` is an exact duplicate of the same function in `sacbot/eval.py`. Both implement identical regex-based style matching with the same markers and weights. This creates a maintenance burden — any change to the style markers must be applied in two places.

**Recommendation**: Import `_compute_style_match` from `sacbot.eval` in `review.py` rather than duplicating it.

### 2. Overly Broad Named Entity Detection in `_check_hallucination_risk` (Low)
The named entity pattern `\b[A-Z][a-z]+ [A-Z][a-z]+\b` matches any two consecutive capitalized words, not just named entities. This would produce false positives on phrases like "Success Habits" or "Management Systems" that are not proper nouns.

**Recommendation**: Use a more specific pattern or a proper NER library (e.g., spaCy) for named entity detection. Alternatively, maintain a whitelist of known entities.

### 3. Coherence Score Formula vs. Comment Mismatch (Low)
The comment in `check_quality` states "Good coherence: 3-20 sentences, avg length 5-30 words" but the formula gives:
- `sentence_score = min(1.0, sentence_count / 10.0)` — caps at 1.0 for 10+ sentences (not 20)
- `length_score = min(1.0, avg_length / 15.0)` — caps at 1.0 for avg_length > 15 (not 30)

The thresholds in the formula are stricter than the comment suggests. This is not a bug per se, but the comment is misleading.

**Recommendation**: Either update the comment to match the formula, or adjust the formula to match the stated thresholds.

### 4. Hallucination Risk Stat Patterns Are Narrow (Low)
The stat_patterns in `_check_hallucination_risk` only match formats like "1.5b", "1.5m", "1.5t" — they miss common formats like "1.5 billion", "1500000000", or "1.5 percent". This means content with explicit number words won't be flagged.

**Recommendation**: Add patterns for spelled-out numbers (e.g., `\b\d+\s*(billion|million|trillion)\b`).

### 5. `check_quality` Does Not Use `content_type` for Coherence (Info)
The `content_type` parameter is only used for the length threshold, not for coherence scoring. A tweet's coherence expectations might differ from a blog post's. This is a minor design observation.

## Verdict
PASS — review file generated. No blocking bugs found in the review.py source code. The code is functionally correct with minor code quality observations noted above.
