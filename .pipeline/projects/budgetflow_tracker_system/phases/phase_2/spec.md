## Phase 2 — Cash Flow Forecasting & Visualization
> *"Now that we know where money went, predict where it's going."*

#### Description
Extend the system with forecasting capabilities. Using historical categorized transaction data, the system models income and expense patterns to predict future cash flow. Adds a visualization layer so users can see trends, seasonal patterns, and projections.

#### Deliverables
1. **Time-bucketing engine** — Groups transactions into configurable intervals (daily, weekly, monthly) with proper handling of irregular import dates.
2. **Forecasting models** — Implements Holt-Winters exponential smoothing and linear regression; selects best model per category.
3. **Cash flow projection engine** — Produces forward-looking income/expenses for the next 30/60/90 days with confidence intervals.
4. **Visualization module** — Chart generation (matplotlib/plotly) for spending trends, category breakdowns, and forecast curves.
5. **Forecast CLI report** — Text-based or chart-based output showing projected cash position and key inflection points.
6. **Pattern detection** — Identifies recurring transactions (subscriptions, rent, salary) and flags anomalies (unusual charges).

#### Dependencies
- Phase 1 (transaction data + categorization must exist before forecasting can occur).

#### Success Criteria
- [ ] Forecast model achieves ≤15% error rate on backtested 30-day predictions (compared to actuals).
- [ ] User can generate a cash flow chart for any 90-day window.
- [ ] Recurring transaction detection identifies ≥90% of recurring patterns in 6+ months of data.
- [ ] Anomaly detection flags at least 80% of genuinely unusual transactions.
- [ ] All forecasting computations run locally; no external API calls.

---

#