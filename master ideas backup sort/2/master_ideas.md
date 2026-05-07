# Master Ideas List

Ideas are processed top-to-bottom. The pipeline picks the first unchecked `[ ]` item.

## Format
`- [ ] **Title** — Description of what to build`

- [ ] **[Football simulator]** — [lock] --nfl/highschool/college regulation field size physics engine. reinforcement learning to optimize success rate vs standard NFL play calls and adversarial self play.
- [ ] **[player attribute library]** — [Integration for the Football tool above with ability to match with player attributes. requires:football_simulator]
- [ ] **[FFO]** — [Football Financial Optimizer. Integration with the above with financial model for valuing players vs salary cap including pool of available free agents. Ability to adjust strategy given additions/subtractions and determine dynamic value to optimize decision making. requires:football_simulator, player_attribute_library]
- [ ] **[Football NFL draft and recruit optimizer]** — [Integration with the above for NFL draft for same purposes and integration with both free agency and the draft. (or for recruiting) requires:football_simulator, ffo]