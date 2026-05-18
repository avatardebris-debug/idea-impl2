"""FastAPI Server for Pipeline Observability Dashboard."""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from pipeline_observability_dashboard.aggregator import AggregationService

# Try to find pipeline root
# Typically this runs from within workspace, so we go up 4 levels
_current_dir = Path(__file__).resolve().parent
_possible_pipeline_root = _current_dir.parent.parent.parent.parent
# Ensure we actually have the .pipeline/projects directory
if not (_possible_pipeline_root / "projects").exists():
    # Fallback to local test dir if running in tests
    _possible_pipeline_root = Path(os.getenv("PIPELINE_ROOT", _current_dir.parent / "tests" / "mock_pipeline"))

app = FastAPI(title="Pipeline Observability Dashboard")

# Mount static files
static_dir = _current_dir / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    """Serve the dashboard UI."""
    index_path = static_dir / "index.html"
    if not index_path.exists():
        return "<h1>Dashboard UI not found</h1>"
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/metrics")
async def get_metrics():
    """Returns the full aggregated pipeline metrics."""
    service = AggregationService(_possible_pipeline_root)
    
    return {
        "global": service.get_global_metrics().model_dump(),
        "projects": [p.model_dump() for p in service.get_all_projects_status()]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
