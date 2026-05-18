# Phase 3 Tasks: Web Dashboard UI

[x] **Task 1: Server Setup.**
    - Initialize FastAPI app.
    - Create a `/api/metrics` endpoint that returns the output of `AggregationService`.
    - Add test for endpoint using `TestClient`.

[x] **Task 2: UI Foundation.**
    - Create `index.html` with vanilla CSS/JS in a `static` directory.
    - Implement a premium dark-mode, glassmorphism design (using variables for vibrant accents).
    - Fetch data from `/api/metrics` using fetch API.

[x] **Task 3: Visualizations.**
    - Add dynamic tables for active projects.
    - Add summary cards for "Total Spend", "Success Rate", and "Active Agents".
    - Implement a polling interval (e.g. 5 seconds) to automatically refresh the data.
