# Advantage Player Card Game Simulator Training

## Phase 1: Core Engine + Blackjack Simulator
- [x] Task 1: Project scaffolding
  - What: Create the package directory structure, pyproject.toml, requirements.txt, and __init__.py files. Set up the top-level package `advantage_cardgames` with subpackages `core`, `simulators`, `simulators.poker`, `monte_carlo`, `analysis`, `strategy`, `cli`, `tests`, and `benchmarks`.
  - Files: pyproject.toml, requirements.txt, advantage_cardgames/__init__.py, advantage_cardgames/core/__init__.py, advantage_cardgames/simulators/__init__.py, advantage_cardgames/simulators/poker/__init__.py, advantage_cardgames/monte_carlo/__init__.py, advantage_cardgames/analysis/__init__.py, advantage_cardgames/strategy/__init__.py, advantage_cardgames/cli/__init__.py, advantage_cardgames/tests/__init__.py, advantage_cardgames/benchmarks/__init__.py
  - Done when: `pip install -e .` succeeds from the project root, and `import advantage_cardgames` works with all subpackages importable.

- [x] Task 2: Core game engine — deck, hand, and game base class
  - What: Implement `core/deck.py` (Card, Deck, Shoe classes with shuffle, deal, cut-card shuffle), `core/hand.py` (Hand class with card management, hand evaluation for blackjack — bust, blackjack, soft/hard totals, push, win, loss), and `core/game.py` (abstract Game base class with start_round, get_legal_actions, apply_action, get_outcome, state serialization).
  - Files: advantage_cardgames/core/deck.py, advantage_cardgames/core/hand.py, advantage_cardgames/core/game.py
  - Done when: Deck creates 52 cards, shuffles deterministically with a seed, deals correctly. Hand evaluates blackjack hands correctly (blackjack, bust, push, win, loss). Game base class is abstract with clear interfaces. Unit tests pass for all three modules.

- [x] Task 3: Blackjack basic strategy table
  - What: Implement `strategy/basic_strategy.py` with a precomputed basic strategy table for standard blackjack rules (dealer stands on 17, double after split allowed, surrender allowed, 6 decks). Strategy maps (player_hand, dealer_upcard) → action (hit, stand, double, split, surrender). Load strategy from embedded JSON dict.
  - Files: advantage_cardgames/strategy/basic_strategy.py
  - Done when: Strategy returns correct actions for all standard player-dealer combinations. Actions match known reference tables (e.g., player 16 vs dealer 10 → surrender/hit, player 12 vs dealer 2-3 → hit, player 11 vs dealer 2-10 → double). Strategy can be serialized to and loaded from JSON.

- [x] Task 4: Blackjack simulator
  - What: Implement `simulators/blackjack.py` with configurable rules (number of decks, dealer stands/hits on 17, surrender allowed, double after split, insurance). Simulator runs N hands, applies a strategy (basic or player-determined), tracks outcomes, and computes EV, win/loss/push rates, and standard deviation. Supports both single-hand and multi-hand simulation.
  - Files: advantage_cardgames/simulators/blackjack.py
  - Done when: Simulator runs 100,000 hands in under 30 seconds. EV is within 0.1% of published basic strategy EV (-0.5% for standard rules). All rule variants work correctly. Unit tests cover hand dealing, outcome determination, strategy application, and EV computation.

- [x] Task 5: CLI entry point
  - What: Implement `cli/main.py` with argparse-based CLI. Subcommands: `blackjack` (run simulation with --hands, --strategy, --decks, --dealer-rule options), `ev` (compute EV for a given strategy), `compare` (compare two strategies). Entry via `python -m advantage_cardgames blackjack --hands 100000 --strategy basic`.
  - Files: advantage_cardgames/cli/main.py, advantage_cardgames/__main__.py
  - Done when: `python -m advantage_cardgames blackjack --hands 100000 --strategy basic` runs and prints simulation results (EV, win rate, loss rate, push rate, standard deviation). All CLI options work correctly. Help text is informative.

- [x] Task 6: Phase 1 test suite
  - What: Write comprehensive tests in `tests/test_deck.py`, `tests/test_hand.py`, `tests/test_game.py`, `tests/test_basic_strategy.py`, `tests/test_blackjack.py`, and `tests/test_integration.py`. Test deck creation/shuffling, hand evaluation edge cases, strategy correctness, simulator EV accuracy, and end-to-end CLI invocation.
  - Files: advantage_cardgames/tests/test_deck.py, advantage_cardgames/tests/test_hand.py, advantage_cardgames/tests/test_game.py, advantage_cardgames/tests/test_basic_strategy.py, advantage_cardgames/tests/test_blackjack.py, advantage_cardgames/tests/test_integration.py
  - Done when: All tests pass with `pytest`. Test coverage is comprehensive (deck, hand, strategy, simulator, CLI). Integration test verifies full pipeline: create game → deal → apply strategy → compute EV → CLI invocation.

## Phase 2: Video Poker Simulator + Optimal Strategy Calculator
- [ ] Task 1: Implement simulators/video_poker.py
- [ ] Task 2: Extend core/hand.py with poker hand ranking
- [ ] Task 3: Implement strategy/optimal.py (optimal hold/discard solver)
- [ ] Task 4: Implement analysis/ev_calculator.py
- [ ] Task 5: Create benchmarks/video_poker_paytables.json
- [ ] Task 6: Write tests for Phase 2

## Phase 3: Poker Suite — Texas Hold'em + ICM
- [ ] Task 1: Implement simulators/poker/holdem.py
- [ ] Task 2: Implement simulators/poker/icm.py
- [ ] Task 3: Integrate pokerkit for hand evaluation
- [ ] Task 4: Implement strategy/nash.py (Nash equilibrium solver)
- [ ] Task 5: Implement analysis/variance.py
- [ ] Task 6: Write tests for Phase 3

## Phase 4: Monte Carlo Training Engine
- [ ] Task 1: Implement monte_carlo/engine.py
- [ ] Task 2: Implement monte_carlo/policy.py
- [ ] Task 3: Implement monte_carlo/trainer.py
- [ ] Task 4: Implement monte_carlo/value_net.py (optional)
- [ ] Task 5: Implement analysis/report.py
- [ ] Task 6: Write tests for Phase 4

## Phase 5: Additional Games
- [ ] Task 1: Implement simulators/stud.py (7-card Stud)
- [ ] Task 2: Implement simulators/slots.py (progressive slots)
- [ ] Task 3: Extend analysis/ev_calculator.py for slots
- [ ] Task 4: Write tests for Phase 5

## Phase 6: Unified Dashboard + Advanced Analytics
- [ ] Task 1: Implement cli/dashboard.py
- [ ] Task 2: Implement analysis/bankroll.py
- [ ] Task 3: Implement analysis/comparison.py
- [ ] Task 4: Add export capabilities (CSV/HTML/PDF)
- [ ] Task 5: Write documentation and examples