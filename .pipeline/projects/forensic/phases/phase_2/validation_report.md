# Validation Report — Phase 2
## Summary
- Tests: 50 passed, 8 failed (Phase 2 specific: test_normalization.py, test_compare.py, test_earnings.py)
- Overall: 120 passed, 28 failed (includes non-Phase 2 tests)
- Core files present: normalization.py, compare.py, earnings.py, test_normalization.py, test_compare.py, test_earnings.py, requirements.txt — all PRESENT
## Failures (Phase 2 related)
- test_normalization.py: 7 failures — extract_cogs, extract_net_income, extract_operating_income, extract_capex, extract_cash_flow_ops, normalized_values_are_ratios, multiple_text_parts all return None instead of expected values
- test_earnings.py: 1 failure — test_insufficient_data asserts inf == 0.0 (expected 0.0, got inf)
- test_compare.py: 0 failures — all 20 tests passed
## Verdict: FAIL
