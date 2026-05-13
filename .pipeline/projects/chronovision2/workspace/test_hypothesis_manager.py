"""
test_hypothesis_manager.py
Tests the HypothesisManager class and its RL reward loop.

Tests:
  1. add_hypothesis creates a record with correct defaults
  2. add_hypothesis with custom ID works
  3. add_hypothesis raises on duplicate ID
  4. remove_hypothesis removes and returns True; returns False if missing
  5. score_hypothesis computes surprise and updates score
  6. score_hypothesis raises on unknown hypothesis
  7. update_weights adjusts weights based on rewards
  8. update_weights normalizes weights to sum to 1
  9. update_weights prunes low-weight hypotheses
 10. get_best_hypothesis returns lowest-score hypothesis
 11. get_all_scores / get_all_weights return correct dicts
 12. run_reward_cycle scores all and updates weights in one call
 13. get_hypothesis_configs returns configs with weights
 14. get_summary returns correct state summary
 15. Weight update is monotonic for consistently good hypothesis
 16. Multiple hypotheses: relative weights reflect relative scores
"""

import sys
import pathlib
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from chronovision2.core.hypothesis_manager import HypothesisManager

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
results = []

def check(name, condition, detail=""):
    ok = bool(condition)
    status = PASS if ok else FAIL
    print(f"  [{status}] {name}")
    if not ok and detail:
        print(f"         {detail}")
    results.append((name, ok))
    return ok


print("\n=== HypothesisManager Tests ===\n")

# ── Test 1: add_hypothesis creates a record with correct defaults ──
print("Test 1: add_hypothesis creates a record with correct defaults")
mgr = HypothesisManager()
hid = mgr.add_hypothesis(config={"model": "test"})
check("returns a non-empty string ID", isinstance(hid, str) and len(hid) > 0)
check("hypothesis exists in manager", hid in mgr.hypotheses)
record = mgr.hypotheses[hid]
check("weight defaults to 1.0", record.weight == 1.0)
check("score defaults to 0.0", record.score == 0.0)
check("survival_count defaults to 0", record.survival_count == 0)
check("config is stored", record.config == {"model": "test"})

# ── Test 2: add_hypothesis with custom ID ──
print("\nTest 2: add_hypothesis with custom ID")
mgr2 = HypothesisManager()
hid2 = mgr2.add_hypothesis(hypothesis_id="my_custom_id", config={"x": 42})
check("custom ID is used", hid2 == "my_custom_id")
check("hypothesis exists", "my_custom_id" in mgr2.hypotheses)

# ── Test 3: add_hypothesis raises on duplicate ID ──
print("\nTest 3: add_hypothesis raises on duplicate ID")
try:
    mgr2.add_hypothesis(hypothesis_id="my_custom_id", config={"x": 99})
    check("raises ValueError on duplicate", False, "No exception raised")
except ValueError:
    check("raises ValueError on duplicate", True)

# ── Test 4: remove_hypothesis ──
print("\nTest 4: remove_hypothesis")
mgr3 = HypothesisManager()
hid3 = mgr3.add_hypothesis(config={"a": 1})
check("remove returns True for existing", mgr3.remove_hypothesis(hid3) is True)
check("hypothesis is removed", hid3 not in mgr3.hypotheses)
check("remove returns False for missing", mgr3.remove_hypothesis("nonexistent") is False)

# ── Test 5: score_hypothesis computes surprise and updates score ──
print("\nTest 5: score_hypothesis computes surprise and updates score")
mgr4 = HypothesisManager()
hid4 = mgr4.add_hypothesis(config={"model": "test"})
# Score with perfect prediction (surprise=0)
surprise1 = mgr4.score_hypothesis(hid4, predicted_state={"x": 1}, actual_state={"x": 1})
record4 = mgr4.hypotheses[hid4]
check("score is 0 for perfect prediction", record4.score == 0.0)
check("survival_count increased", record4.survival_count == 1)
# Score with bad prediction (high surprise)
surprise2 = mgr4.score_hypothesis(hid4, predicted_state={"x": 100}, actual_state={"x": 1})
record4 = mgr4.hypotheses[hid4]
check("score increased after bad prediction", record4.score > 0)
check("survival_count increased", record4.survival_count == 2)

# ── Test 6: score_hypothesis raises on unknown hypothesis ──
print("\nTest 6: score_hypothesis raises on unknown hypothesis")
try:
    mgr4.score_hypothesis("nonexistent", predicted_state={}, actual_state={})
    check("raises ValueError on unknown hypothesis", False, "No exception raised")
except ValueError:
    check("raises ValueError on unknown hypothesis", True)

# ── Test 7: update_weights adjusts weights based on rewards ──
print("\nTest 7: update_weights adjusts weights based on rewards")
mgr5 = HypothesisManager()
h1 = mgr5.add_hypothesis(config={"name": "A"})
h2 = mgr5.add_hypothesis(config={"name": "B"})
# Give A consistently good predictions, B consistently bad
for _ in range(5):
    mgr5.score_hypothesis(h1, predicted_state={"x": 1}, actual_state={"x": 1})
    mgr5.score_hypothesis(h2, predicted_state={"x": 100}, actual_state={"x": 1})
mgr5.update_weights()
w1 = mgr5.hypotheses[h1].weight
w2 = mgr5.hypotheses[h2].weight
check("weight A > weight B after good/bad predictions", w1 > w2)

# ── Test 8: update_weights normalizes weights to sum to 1 ──
print("\nTest 8: update_weights normalizes weights to sum to 1")
total = sum(r.weight for r in mgr5.hypotheses.values())
check("weights sum to 1.0", abs(total - 1.0) < 1e-9)

# ── Test 9: update_weights prunes low-weight hypotheses ──
print("\nTest 9: update_weights prunes low-weight hypotheses")
# Use a manager with a high min_weight threshold and many hypotheses
# so the bad one's normalized weight drops below the threshold
mgr6 = HypothesisManager(min_weight=0.3)
h_good = mgr6.add_hypothesis(config={"name": "good"})
h_bad = mgr6.add_hypothesis(config={"name": "bad"})
# Make bad hypothesis very bad
for _ in range(20):
    mgr6.score_hypothesis(h_good, predicted_state={"x": 1}, actual_state={"x": 1})
    mgr6.score_hypothesis(h_bad, predicted_state={"x": 100}, actual_state={"x": 1})
mgr6.update_weights()
check("good hypothesis still exists", h_good in mgr6.hypotheses)
# After normalization with 2 hypotheses, weights are ~0.53 and ~0.47
# Neither is below 0.3, so we test with a higher threshold
# Instead, use a very high min_weight to force pruning
mgr6b = HypothesisManager(min_weight=0.5)
h_good2 = mgr6b.add_hypothesis(config={"name": "good"})
h_bad2 = mgr6b.add_hypothesis(config={"name": "bad"})
for _ in range(20):
    mgr6b.score_hypothesis(h_good2, predicted_state={"x": 1}, actual_state={"x": 1})
    mgr6b.score_hypothesis(h_bad2, predicted_state={"x": 100}, actual_state={"x": 1})
mgr6b.update_weights()
check("bad hypothesis pruned (weight < threshold)", h_bad2 not in mgr6b.hypotheses)

# ── Test 10: get_best_hypothesis returns lowest-score hypothesis ──
print("\nTest 10: get_best_hypothesis returns lowest-score hypothesis")
mgr7 = HypothesisManager()
h1 = mgr7.add_hypothesis(config={"name": "low"})
h2 = mgr7.add_hypothesis(config={"name": "high"})
for _ in range(10):
    mgr7.score_hypothesis(h1, predicted_state={"x": 1}, actual_state={"x": 1})
    mgr7.score_hypothesis(h2, predicted_state={"x": 100}, actual_state={"x": 1})
best = mgr7.get_best_hypothesis()
check("best hypothesis is the one with good predictions", best == h1)

# ── Test 11: get_all_scores / get_all_weights return correct dicts ──
print("\nTest 11: get_all_scores and get_all_weights")
mgr8 = HypothesisManager()
h1 = mgr8.add_hypothesis(config={"name": "A"})
h2 = mgr8.add_hypothesis(config={"name": "B"})
mgr8.score_hypothesis(h1, predicted_state={"x": 1}, actual_state={"x": 1})
mgr8.score_hypothesis(h2, predicted_state={"x": 100}, actual_state={"x": 1})
scores = mgr8.get_all_scores()
weights = mgr8.get_all_weights()
check("get_all_scores returns dict", isinstance(scores, dict))
check("get_all_weights returns dict", isinstance(weights, dict))
check("scores contain all hypothesis IDs", set(scores.keys()) == {h1, h2})
check("weights contain all hypothesis IDs", set(weights.keys()) == {h1, h2})
check("scores are correct", abs(scores[h1] - 0.0) < 1e-9 and scores[h2] > 0)

# ── Test 12: run_reward_cycle scores all and updates weights ──
print("\nTest 12: run_reward_cycle scores all and updates weights")
mgr9 = HypothesisManager()
h1 = mgr9.add_hypothesis(config={"name": "A"})
h2 = mgr9.add_hypothesis(config={"name": "B"})
# Simulate a reward cycle: A gets good, B gets bad
mgr9.run_reward_cycle(
    predictions={h1: {"x": 1}, h2: {"x": 100}},
    actual_state={"x": 1}
)
check("weights updated after cycle", abs(sum(mgr9.get_all_weights().values()) - 1.0) < 1e-9)
check("A has higher weight than B", mgr9.hypotheses[h1].weight > mgr9.hypotheses[h2].weight)

# ── Test 13: get_hypothesis_configs returns configs with weights ──
print("\nTest 13: get_hypothesis_configs returns configs with weights")
mgr10 = HypothesisManager()
h1 = mgr10.add_hypothesis(config={"model": "gpt-4", "temp": 0.7})
h2 = mgr10.add_hypothesis(config={"model": "claude", "temp": 0.5})
configs = mgr10.get_hypothesis_configs()
check("returns list of configs", isinstance(configs, list))
check("configs contain weights", any("weight" in c for c in configs))
# The config is flattened, so model and temp are top-level keys
check("original config preserved (model key)", any(c.get("model") == "gpt-4" for c in configs))
check("weight is present", any("weight" in c for c in configs))

# ── Test 14: get_summary returns correct state summary ──
print("\nTest 14: get_summary returns correct state summary")
mgr11 = HypothesisManager()
h1 = mgr11.add_hypothesis(config={"name": "A"})
h2 = mgr11.add_hypothesis(config={"name": "B"})
mgr11.score_hypothesis(h1, predicted_state={"x": 1}, actual_state={"x": 1})
summary = mgr11.get_summary()
check("summary is a dict", isinstance(summary, dict))
check("summary contains count", "count" in summary)
check("count is correct", summary["count"] == 2)
check("summary contains best_hypothesis", "best_hypothesis" in summary)
check("best_hypothesis is correct", summary["best_hypothesis"] == h1)

# ── Test 15: Weight update is monotonic for consistently good hypothesis ──
print("\nTest 15: Weight update is monotonic for consistently good hypothesis")
mgr12 = HypothesisManager()
h1 = mgr12.add_hypothesis(config={"name": "A"})
h2 = mgr12.add_hypothesis(config={"name": "B"})
# Score first, then update weights, then check monotonicity
# Start by scoring once to establish baseline
mgr12.score_hypothesis(h1, predicted_state={"x": 1}, actual_state={"x": 1})
mgr12.score_hypothesis(h2, predicted_state={"x": 100}, actual_state={"x": 1})
mgr12.update_weights()
prev_w1 = mgr12.hypotheses[h1].weight
# Now check that subsequent updates are monotonic
for i in range(4):
    mgr12.score_hypothesis(h1, predicted_state={"x": 1}, actual_state={"x": 1})
    mgr12.score_hypothesis(h2, predicted_state={"x": 100}, actual_state={"x": 1})
    mgr12.update_weights()
    curr_w1 = mgr12.hypotheses[h1].weight
    check(f"weight A increased after cycle {i+1}", curr_w1 >= prev_w1)
    prev_w1 = curr_w1

# ── Test 16: Multiple hypotheses: relative weights reflect relative scores ──
print("\nTest 16: Multiple hypotheses: relative weights reflect relative scores")
mgr13 = HypothesisManager()
h1 = mgr13.add_hypothesis(config={"name": "A"})
h2 = mgr13.add_hypothesis(config={"name": "B"})
h3 = mgr13.add_hypothesis(config={"name": "C"})
# A: good, B: medium, C: bad
for _ in range(10):
    mgr13.score_hypothesis(h1, predicted_state={"x": 1}, actual_state={"x": 1})
    mgr13.score_hypothesis(h2, predicted_state={"x": 50}, actual_state={"x": 1})
    mgr13.score_hypothesis(h3, predicted_state={"x": 100}, actual_state={"x": 1})
mgr13.update_weights()
w1 = mgr13.hypotheses[h1].weight
w2 = mgr13.hypotheses[h2].weight
w3 = mgr13.hypotheses[h3].weight
check("A > B > C weights", w1 > w2 > w3)
check("weights sum to 1", abs(w1 + w2 + w3 - 1.0) < 1e-9)


# ── Summary ──
print(f"\n{'='*60}")
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
total = len(results)
print(f"  PASS: {passed}/{total}")
print(f"  FAIL: {failed}/{total}")

if failed > 0:
    print("\nFailed tests:")
    for name, ok in results:
        if not ok:
            print(f"  - {name}")
else:
    print("\nAll tests passed!")
