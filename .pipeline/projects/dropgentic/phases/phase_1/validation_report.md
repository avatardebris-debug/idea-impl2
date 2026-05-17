# Validation Report — Phase 1
## Summary
- Tests: 68 passed, 13 failed
- Required files: 14 of 15 present
- Missing file: config/default.yaml
## Verdict: FAIL

## Failure Details

### Test Failures (13)

#### test_margin.py (4 failures)
1. **test_calculate_payment_fee** — assert 3.2 == 3.3 (payment fee calculation off by 0.1)
2. **test_high_margin_product** — assert 0.94 == 0.95 (margin score incorrect)
3. **test_low_margin_product** — assert 0.12 == 0.2 (margin score incorrect)
4. **test_exact_break_even** — assert 'Reject' == 'Review' (break-even action decision wrong)

#### test_order.py (7 failures)
5. **test_default_values** — assert -10.0 == 0.0 (default net_profit incorrect)
6. **test_calculate_fees** — assert 7.0 == 17.0 (fee calculation off by 10.0)
7. **test_calculate_net_profit** — assert -142.0 == 58.0 (net profit calculation wrong)
8. **test_calculate_net_margin** — assert -1.136 == 0.464 (net margin calculation wrong)
9. **test_to_dict** — 'net_profit' key missing from serialized dict
10. **test_string_quantity_raises** — TypeError: '<=' not supported between str and int (no type validation)
11. **test_string_unit_cost_raises** — TypeError: '<' not supported between str and int (no type validation)

#### test_product.py (2 failures)
12. **test_gross_margin_zero** — ValueError raised when retail_price == cost_price (should allow zero-margin products)
13. **test_zero_retail_price_raises** — Regex mismatch: expected 'retail_price.*must be >= cost_price', got 'retail_price must be positive'

### Missing Files
- **config/default.yaml** — Required by Task 4 (configuration and settings module with file-based loading)

## Root Causes
- **MarginCalculator**: Payment fee formula appears incorrect (off by 0.1 in base case); margin scores miscalculated for high/low margin products; break-even action threshold wrong.
- **Order model**: Fee calculations produce wrong totals; net_profit/net_margin formulas are incorrect; to_dict omits net_profit; no type coercion/validation for quantity/unit_cost.
- **Product model**: Validation too strict — rejects retail_price == cost_price (zero-margin case); error message regex doesn't match test expectations.
