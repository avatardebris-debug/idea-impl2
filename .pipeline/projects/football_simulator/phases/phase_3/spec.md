## Phase 3: Adversarial Self-Play & Full Evaluation

### Description
Implement adversarial self-play training, comprehensive evaluation against NFL baselines, and visualization/analysis tools. This phase makes the system production-quality with rigorous benchmarks.

### Deliverable
- **Adversarial self-play framework:** Two agents (Offense vs Defense) trained simultaneously, alternating as the "opponent" each episode. Elo-style rating tracking. Support for population-based training (multiple agent variants).
- **Comprehensive evaluation suite:** 
  - Benchmark against 50+ NFL baseline strategies (down/distance/field-position tables).
  - Statistical significance testing (confidence intervals on win rates).
  - Play-type breakdown (run, pass, screen, play-action, etc.).
  - Situational analysis (red zone, 3rd down, 4th down, two-minute drill).
- **Visualization tools:** 
  - Replay viewer (frame-by-frame playback of plays).
  - Decision heatmap (where agents choose to run vs pass).
  - Performance radar charts comparing agents vs NFL baselines.
- **Documentation:** API docs, training guide, and benchmark report.

### Dependencies
- Phase 1 and Phase 2 deliverables
- Multi-processing infrastructure for parallel self-play
- Visualization libraries (Matplotlib, Plotly)

### Success Criteria
- [ ] Self-play training converges — both Offense and Defense improve over time without degenerating to trivial strategies.
- [ ] Best-trained agent outperforms standard NFL play-call baselines in ≥ 60% of evaluated scenarios.
- [ ] Statistical analysis shows performance gains are significant (p < 0.05) across multiple random seeds.
- [ ] Replay viewer renders at least 10 sample plays with correct physics.
- [ ] Full benchmark report documents agent performance vs every NFL baseline strategy.
- [ ] System is reproducible — full training run can be reproduced from config files.

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Physics simulation too slow for RL training (thousands of env steps/sec needed) | High | Use vectorized simulation (batched parallel envs on GPU via JAX or custom CUDA kernels). Start with simplified player models (circle colliders) and add complexity later. |
| RL agents learn degenerate strategies (exploit physics bugs) | Medium | Rigorous physics validation in Phase 1. Adversarial testing — have agents try to break the sim. Regularization on action space. |
| NFL baseline data unavailable or incomplete | Medium | Use publicly available play-calling datasets (e.g., NFL FastR, Pro-Football-Reference). Fall back to heuristic baselines if needed. |
| Reward function design is the bottleneck for convergence | High | Multi-phase reward: start with dense rewards (yards/play), then switch to sparse (win/loss). Use reward shaping with potential functions. |
| Adversarial self-play doesn't converge | Medium | Use population-based training instead of pure self-play. Add exploration bonuses. Monitor Elo 