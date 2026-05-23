## Phase 2: Video Poker Simulator + Optimal Strategy Calculator

**Description:** Implement video poker simulator supporting multiple variants (Jacks or Better, Deuces Wild, Bonus Poker, etc.) with a hand-evaluation engine and optimal strategy calculator using Monte Carlo or exhaustive enumeration.

**Deliverable:**
- `simulators/video_poker.py` — video poker simulator with multiple paytable variants
- `core/hand.py` extended with poker hand ranking (pairs, flushes, straights, full houses, etc.)
- `strategy/optimal.py` — optimal hold/discard strategy solver
- `analysis/ev_calculator.py` — EV per paytable variant
- `benchmarks/video_poker_paytables.json` — reference paytables and known EVs

**Dependencies:** Phase 1 (core engine, deck, hand evaluation)

**Success Criteria:**
- [ ] Supports Jacks or Better, Deuces Wild, Bonus Poker, Aces and Faces
- [ ] Hand evaluation matches standard poker hand rankings
- [ ] Optimal strategy matches published strategy charts within 0.01% EV
- [ ] Paytable configuration is flexible (user-defined paytables)
- [ ] EV for full-pay Jacks or Better (9/6) matches known value (~99.54%)
- [ ] CLI: `python -m advantage_cardgames video_poker --variant jacks_or_better --paytable 9_6 --hands 100000`

---

