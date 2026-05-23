## Phase 3: Poker Suite — Texas Hold'em + ICM

**Description:** Implement Texas Hold'em simulator (cash game and tournament modes) with ICM (Independent Chip Model) for tournament payouts. Leverage `pokerkit` for hand evaluation and study `poker-mtt-icM-master` for ICM implementation.

**Deliverable:**
- `simulators/poker/holdem.py` — Texas Hold'em simulator (cash + tournament)
- `simulators/poker/icm.py` — ICM payout calculator
- `pokerkit` integration for hand evaluation
- `strategy/nash.py` — simplified Nash equilibrium solver for heads-up
- `analysis/variance.py` — tournament variance and ROI analysis

**Dependencies:** Phase 1 (core engine), Phase 2 (hand evaluation)

**Success Criteria:**
- [ ] Cash game Hold'em simulates complete hands (pre-flop through river)
- [ ] Tournament mode supports multi-table scenarios with ICM payouts
- [ ] ICM payouts match known reference calculations (±0.5%)
- [ ] Heads-up Nash equilibrium solver produces reasonable strategy
- [ ] Simulates 10,000 tournament hands in under 60 seconds
- [ ] CLI: `python -m advantage_cardgames poker --mode tournament --players 9 --icm`

---

