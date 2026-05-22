"""API Server for drop_servicing_tool — FastAPI-based REST API.

Provides REST endpoints for SOP management, execution, bulk processing,
and template management.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .sop_store import create_sop, get_sop, list_sops, delete_sop
from .sop_schema import SOP
from .results_store import ResultsStore
from .task_queue import TaskQueue
from .template_library import TemplateLibrary


# ====== Pydantic Models ======

class CreateSOPRequest(BaseModel):
    """Request body for creating an SOP."""
    name: str
    description: str
    inputs: List[Dict[str, Any]]
    steps: List[Dict[str, Any]]
    output_format: Optional[str] = None


class RunSOPRequest(BaseModel):
    """Request body for running an SOP."""
    input_data: Dict[str, Any]


class CreateBulkQueueRequest(BaseModel):
    """Request body for creating a bulk queue."""
    sop_name: str
    inputs: List[Dict[str, Any]]
    max_retries: int = 3


class BulkStatusResponse(BaseModel):
    """Response body for bulk queue status."""
    queue_id: str
    sop_name: str
    total_tasks: int
    completed: int
    failed: int
    pending: int


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str


# ====== API App ======

app = FastAPI(
    title="Drop Servicing Tool API",
    description="REST API for SOP management, execution, and bulk processing.",
    version="1.0.0",
)

# Initialize shared services (overridden in tests via monkeypatch)
_results_store: ResultsStore | None = None
_task_queue: TaskQueue | None = None
_template_library: TemplateLibrary | None = None


def _get_results_store() -> ResultsStore:
    """Lazy-load or return the shared ResultsStore."""
    global _results_store
    if _results_store is None:
        _results_store = ResultsStore()
    return _results_store


def _get_task_queue() -> TaskQueue:
    """Lazy-load or return the shared TaskQueue."""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue


def _get_template_library() -> TemplateLibrary:
    """Lazy-load or return the shared TemplateLibrary."""
    global _template_library
    if _template_library is None:
        _template_library = TemplateLibrary()
    return _template_library


# ====== Health Check ======

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


# ====== SOP Endpoints ======

@app.get("/sops")
async def list_sops_api() -> List[str]:
    """List all available SOPs."""
    try:
        return list_sops()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/sops/{sop_name}")
async def get_sop_api(sop_name: str) -> Dict[str, Any]:
    """Get SOP details by name."""
    try:
        sop = get_sop(sop_name)
        return {
            "name": sop.name,
            "description": sop.description,
            "inputs": sop.inputs,
            "steps": [
                {
                    "name": s.name,
                    "description": s.description,
                    "prompt_template": s.prompt_template,
                    "llm_required": s.llm_required,
                }
                for s in sop.steps
            ],
            "output_format": sop.output_format,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"SOP '{sop_name}' not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/sops")
async def create_sop_api(request: CreateSOPRequest) -> Dict[str, Any]:
    """Create a new SOP."""
    try:
        sop_data = {
            "name": request.name,
            "description": request.description,
            "inputs": request.inputs,
            "steps": request.steps,
            "output_format": request.output_format,
        }
        path = create_sop(request.name, sop_data)
        return {
            "name": request.name,
            "message": f"SOP '{request.name}' created successfully",
            "path": str(path),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.delete("/sops/{sop_name}")
async def delete_sop_api(sop_name: str) -> Dict[str, Any]:
    """Delete an SOP."""
    try:
        success = delete_sop(sop_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"SOP '{sop_name}' not found")
        return {
            "name": sop_name,
            "message": f"SOP '{sop_name}' deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ====== SOP Execution Endpoint ======

@app.post("/sops/{sop_name}/run")
async def run_sop_api(sop_name: str, request: RunSOPRequest) -> Dict[str, Any]:
    """Run an SOP with the given input data."""
    from .executor import SOPExecutor, MockLLMClient

    try:
        sop = get_sop(sop_name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"SOP '{sop_name}' not found")

    llm_client = MockLLMClient()
    executor = SOPExecutor(sop, llm_client)

    try:
        result = executor.run(request.input_data)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ====== Bulk Queue Endpoints ======

@app.post("/bulk/queues")
async def create_bulk_queue_api(request: CreateBulkQueueRequest) -> Dict[str, Any]:
    """Create a new bulk execution queue."""
    try:
        tq = _get_task_queue()
        queue_id = tq.create_queue(request.sop_name, request.inputs, max_retries=request.max_retries)
        return {
            "queue_id": queue_id,
            "sop_name": request.sop_name,
            "total_tasks": len(request.inputs),
            "message": f"Queue '{queue_id}' created",
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/bulk/queues")
async def list_bulk_queues_api() -> List[Dict[str, Any]]:
    """List all bulk queues."""
    try:
        tq = _get_task_queue()
        queue_dir = tq._base
        meta_files = sorted(queue_dir.glob("*_metadata.json"))

        if not meta_files:
            return []

        result = []
        for mf in meta_files:
            meta = json.loads(mf.read_text(encoding="utf-8"))
            qid = meta["queue_id"]
            counts = tq.get_task_count_by_status(qid)
            result.append({
                "queue_id": qid,
                "sop_name": meta["sop_name"],
                "total_tasks": meta["total_tasks"],
                "created_at": meta.get("created_at", "unknown"),
                "status": counts,
            })
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/bulk/queues/{queue_id}/status")
async def get_bulk_queue_status_api(queue_id: str) -> BulkStatusResponse:
    """Get the status of a bulk queue."""
    try:
        tq = _get_task_queue()
        rs = _get_results_store()

        try:
            queue = tq.get_queue(queue_id)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"Queue '{queue_id}' not found")

        counts = tq.get_task_count_by_status(queue_id)
        completed = counts.get("completed", 0)
        failed = counts.get("failed", 0)
        pending = counts.get("pending", 0)

        return BulkStatusResponse(
            queue_id=queue_id,
            sop_name=queue["sop_name"],
            total_tasks=queue["total_tasks"],
            completed=completed,
            failed=failed,
            pending=pending,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/bulk/queues/{queue_id}")
async def delete_bulk_queue_api(queue_id: str) -> Dict[str, Any]:
    """Delete a bulk queue and its results."""
    try:
        tq = _get_task_queue()
        rs = _get_results_store()

        tq_deleted = tq.delete_queue(queue_id)
        rs_deleted = rs.delete_queue_results(queue_id)

        if not tq_deleted and not rs_deleted:
            raise HTTPException(status_code=404, detail=f"Queue '{queue_id}' not found")

        return {
            "queue_id": queue_id,
            "message": f"Queue '{queue_id}' deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ====== Bulk Results Endpoints ======

@app.get("/bulk/queues/{queue_id}/results")
async def get_bulk_results_api(queue_id: str) -> List[Dict[str, Any]]:
    """Get all results for a bulk queue."""
    try:
        rs = _get_results_store()
        # Return empty list if queue has no results file
        try:
            results = rs.get_all_results(queue_id)
        except FileNotFoundError:
            return []

        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/bulk/queues/{queue_id}/summary")
async def get_bulk_summary_api(queue_id: str) -> Dict[str, Any]:
    """Get summary of bulk execution results."""
    try:
        rs = _get_results_store()
        # Return empty summary if queue has no results
        try:
            summary = rs.get_summary(queue_id)
        except FileNotFoundError:
            summary = {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "total_tokens": 0,
                "total_duration": 0.0,
            }
        return {"queue_id": queue_id, "summary": summary}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ====== Template Endpoints ======

@app.get("/templates")
async def list_templates_api(category: Optional[str] = None) -> List[str]:
    """List all available templates."""
    try:
        lib = _get_template_library()
        if category:
            return lib.list_templates(category=category)
        return lib.list_templates()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/templates/{template_name}")
async def get_template_api(template_name: str) -> Dict[str, Any]:
    """Get template content by name."""
    try:
        lib = _get_template_library()
        content = lib.get_template(template_name)
        return {"name": template_name, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/templates")
async def create_template_api(
    name: str = Query(..., description="Template name"),
    content: str = Query(..., description="Template content"),
    category: Optional[str] = Query(None, description="Template category"),
) -> Dict[str, Any]:
    """Create a new template."""
    try:
        lib = _get_template_library()
        lib.register_template(name, content, category=category)
        return {
            "name": name,
            "message": f"Template '{name}' created successfully",
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.delete("/templates/{template_name}")
async def delete_template_api(template_name: str) -> Dict[str, Any]:
    """Delete a template."""
    try:
        lib = _get_template_library()
        success = lib.delete_template(template_name)
        if not success:
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
        return {
            "name": template_name,
            "message": f"Template '{template_name}' deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ====== Agent Endpoints ======

@app.get("/agents")
async def list_agents_api() -> List[str]:
    """List all registered agents."""
    from .agent_registry import AgentRegistry
    registry = AgentRegistry()
    return registry.list_agents()


@app.get("/agents/{agent_name}")
async def get_agent_api(agent_name: str) -> Dict[str, Any]:
    """Get agent details by name."""
    from .agent_registry import AgentRegistry
    registry = AgentRegistry()
    try:
        agent = registry.get_agent(agent_name)
        return {
            "name": agent_name,
            "message": f"Agent '{agent_name}' found",
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")


# ====== Config Endpoints ======

@app.get("/config/presets")
async def get_presets_api() -> Dict[str, Any]:
    """Get all agent mode presets."""
    from .agent_config import AgentMode, get_preset
    presets = {}
    for mode in AgentMode:
        presets[mode.value] = get_preset(mode)
    return presets


@app.get("/config/presets/{mode}")
async def get_preset_api(mode: str) -> Dict[str, Any]:
    """Get a specific agent mode preset."""
    from .agent_config import AgentMode, get_preset
    try:
        agent_mode = AgentMode(mode)
        preset = get_preset(agent_mode)
        return {
            "mode": mode,
            "preset": preset,
        }
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Mode '{mode}' not found")
