## Phase 4 — Dashboard + Web Interface (Optional)

**Goal**: Provide a lightweight web dashboard for interactive exploration.

### Deliverable

- Flask/FastAPI-based web app that:
  1. Serves the SQLite database via REST API.
  2. Renders interactive charts (capital flows, fraud scores over time).
  3. Allows filtering by ticker, date range, and risk level.

### Dependencies

- `flask` or `fastapi` + `uvicorn`
- `plotly` or `matplotlib` for charting

### File Structure (Phase 4 additions)

```
forensic/
├── src/
│   └── forensic/
│       ├── api.py               # REST API endpoints
│       └── web/
│           ├── app.py           # Web app entry point
│           └── templates/       # HTML templates
└── ...
```

### Success Criteria

- [ ] Web app starts and serves data without errors.
- [ ] Charts render correctly in a browser.

---

