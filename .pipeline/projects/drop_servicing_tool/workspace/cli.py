"""CLI for drop_servicing_tool — Typer-based command-line interface."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Optional

import typer

from .config import OUTPUT_DIR
from .executor import MockLLMClient, SOPExecutor
from .sop_store import create_sop, get_sop
from .sop_store import list_sops as _list_sops

app = typer.Typer(
    name="sop",
    help="Drop Servicing Tool — define and execute SOP workflows.",
)
app.name = "sop"

# -----------------------------------------------------------------------
# Helper: default blog_post scaffold
# ----------------------------------------------------------------------

_DEFAULT_SOP = {
    "name": "blog_post",
    "description": "Generate a complete blog post from a topic",
    "inputs": [
        {"name": "topic", "type": "string", "required": True, "description": "The main topic of the blog post"}
    ],
    "steps": [
        {
            "name": "research",
            "description": "Research the topic and identify key points, angles, and supporting facts.",
            "prompt_template": "default_step",
            "llm_required": True,
        },
        {
            "name": "outline",
            "description": "Create a structured outline from the research with section headings.",
            "prompt_template": "default_step",
            "llm_required": True,
        },
        {
            "name": "draft",
            "description": "Write the full blog post draft based on the outline.",
            "prompt_template": "default_step",
            "llm_required": True,
        },
        {
            "name": "title_options",
            "description": "Generate 5 compelling title options for the post.",
            "prompt_template": "default_step",
            "llm_required": True,
        },
    ],
    "output_format": "A complete blog post with title, outline, and full draft",
}

# -----------------------------------------------------------------------
# Bulk subcommands
# ----------------------------------------------------------------------

bulk_app = typer.Typer(
    name="bulk",
    help="Bulk SOP execution — process many inputs in parallel.",
)


def _parse_inputs(inputs_str: str) -> list[dict]:
    """Parse input strings from CSV or JSONL format."""
    if inputs_str.startswith("@"):
        input_path = Path(inputs_str[1:])
        if not input_path.exists():
            typer.echo(f"Error: input file not found: {input_path}", err=True)
            raise typer.Exit(1)
        raw = input_path.read_text(encoding="utf-8")
    else:
        raw = inputs_str

    lines = [line.strip() for line in raw.strip().splitlines() if line.strip()]

    # Try JSONL first
    try:
        return [json.loads(line) for line in lines]
    except json.JSONDecodeError:
        pass

    # Try CSV
    try:
        reader = csv.DictReader(io.StringIO(raw))
        return [dict(row) for row in reader]
    except Exception:
        typer.echo("Error: inputs must be valid JSONL or CSV.", err=True)
        raise typer.Exit(1)


@bulk_app.command(name="create")
def bulk_create(
    sop_name: str = typer.Argument(..., help="Name of the SOP to execute."),
    inputs: str = typer.Argument(..., help="JSONL/CSV inputs or @file path."),
    max_retries: int = typer.Option(3, "--max-retries", "-r", help="Max retries per task."),
) -> None:
    """Create a new bulk execution queue."""
    from .task_queue import TaskQueue

    input_list = _parse_inputs(inputs)
    tq = TaskQueue()
    queue_id = tq.create_queue(sop_name, input_list, max_retries=max_retries)
    typer.echo(f"Queue '{queue_id}' created with {len(input_list)} tasks for SOP '{sop_name}'.")


@bulk_app.command(name="run")
def bulk_run(
    queue_id: str = typer.Argument(..., help="Queue ID to execute."),
    max_workers: int = typer.Option(4, "--max-workers", "-w", help="Number of parallel workers."),
    rate_limit: float = typer.Option(0.0, "--rate-limit", "-R", help="Max requests per second (0 = no limit)."),
    token_budget: Optional[int] = typer.Option(None, "--token-budget", "-T", help="Total token budget."),
    mock: bool = typer.Option(False, "--mock", "-m", help="Use mock LLM for all tasks."),
) -> None:
    """Execute a bulk queue."""
    from .task_queue import TaskQueue
    from .bulk_runner import BulkRunner

    tq = TaskQueue()
    queue = tq.get_queue(queue_id)
    sop_name = queue["sop_name"]

    typer.echo(f"Executing bulk queue '{queue_id}' ({queue['total_tasks']} tasks) for SOP '{sop_name}'...")
    typer.echo(f"  Workers: {max_workers}, Rate limit: {rate_limit}/s, Mock: {mock}")

    runner = BulkRunner(
        sop_name=sop_name,
        queue_id=queue_id,
        max_workers=max_workers,
        rate_limit_per_second=rate_limit,
        token_budget=token_budget,
        use_mock_llm=mock,
    )

    summary = runner.run()

    typer.echo(f"\nBulk execution complete:")
    typer.echo(f"  Completed: {summary['completed_tasks']}")
    typer.echo(f"  Failed:    {summary['failed_tasks']}")
    typer.echo(f"  Tokens:    {summary['total_tokens']}")
    typer.echo(f"  Duration:  {summary['total_duration']}s")

    # Print final status
    statuses = tq.get_all_task_statuses(queue_id)
    completed = sum(1 for status in statuses.values() if status == "completed")
    failed = sum(1 for status in statuses.values() if status == "failed")
    typer.echo(f"  Final:     {completed} completed, {failed} failed")


@bulk_app.command(name="status")
def bulk_status(queue_id: str) -> None:
    """Show the status of a bulk queue."""
    from .task_queue import TaskQueue
    from .results_store import ResultsStore

    tq = TaskQueue()
    rs = ResultsStore()

    try:
        queue = tq.get_queue(queue_id)
    except FileNotFoundError:
        typer.echo(f"Error: queue '{queue_id}' not found.", err=True)
        raise typer.Exit(1)

    typer.echo(f"Queue: {queue_id} | SOP: {queue['sop_name']} | Tasks: {queue['total_tasks']}")
    typer.echo(f"Created: {queue.get('created_at', 'unknown')}")

    # Task statuses
    statuses = tq.get_all_task_statuses(queue_id)
    counts = tq.get_task_count_by_status(queue_id)
    typer.echo(f"Statuses: {counts}")

    # Results summary
    summary = rs.get_summary(queue_id)
    typer.echo(f"Results: {summary}")


@bulk_app.command(name="list")
def bulk_list() -> None:
    """List all bulk queues."""
    from .task_queue import TaskQueue

    tq = TaskQueue()
    queue_dir = tq._base
    meta_files = sorted(queue_dir.glob("*_metadata.json"))

    if not meta_files:
        typer.echo("No bulk queues found.")
        return

    typer.echo(f"Bulk queues ({len(meta_files)}):")
    for mf in meta_files:
        meta = json.loads(mf.read_text(encoding="utf-8"))
        qid = meta["queue_id"]
        counts = tq.get_task_count_by_status(qid)
        typer.echo(f"  {qid}: {meta['sop_name']} — {meta['total_tasks']} tasks — {counts}")


@bulk_app.command(name="delete")
def bulk_delete(queue_id: str) -> None:
    """Delete a bulk queue and all its results."""
    from .task_queue import TaskQueue
    from .results_store import ResultsStore

    tq = TaskQueue()
    rs = ResultsStore()
    tq_deleted = tq.delete_queue(queue_id)
    rs_deleted = rs.delete_queue_results(queue_id)
    if tq_deleted or rs_deleted:
        typer.echo(f"Queue '{queue_id}' deleted.")
    else:
        typer.echo(f"Queue '{queue_id}' not found.", err=True)
        raise typer.Exit(1)


# -----------------------------------------------------------------------
# Export subcommands
# ----------------------------------------------------------------------

export_app = typer.Typer(
    name="export",
    help="Export bulk execution results to CSV or JSONL.",
)


@export_app.command(name="csv")
def export_csv(
    queue_id: str = typer.Argument(..., help="Queue ID to export results from."),
    output: str = typer.Option(..., "--output", "-o", help="Output CSV file path."),
) -> None:
    """Export bulk results as CSV."""
    from .results_store import ResultsStore
    from .task_queue import TaskQueue

    tq = TaskQueue()
    rs = ResultsStore()

    try:
        queue = tq.get_queue(queue_id)
    except FileNotFoundError:
        typer.echo(f"Error: queue '{queue_id}' not found.", err=True)
        raise typer.Exit(1)

    results = rs.get_all_results(queue_id)
    if not results:
        typer.echo(f"No results to export for queue '{queue_id}'.")
        return

    # Collect all unique keys across all results
    all_keys: list[str] = []
    seen: set[str] = set()
    for r in results:
        for key in r.keys():
            if key not in seen:
                all_keys.append(key)
                seen.add(key)

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    typer.echo(f"Exported {len(results)} results to {out_path}")


@export_app.command(name="jsonl")
def export_jsonl(
    queue_id: str = typer.Argument(..., help="Queue ID to export results from."),
    output: str = typer.Option(..., "--output", "-o", help="Output JSONL file path."),
) -> None:
    """Export bulk results as JSONL."""
    from .results_store import ResultsStore
    from .task_queue import TaskQueue

    tq = TaskQueue()
    rs = ResultsStore()

    try:
        queue = tq.get_queue(queue_id)
    except FileNotFoundError:
        typer.echo(f"Error: queue '{queue_id}' not found.", err=True)
        raise typer.Exit(1)

    results = rs.get_all_results(queue_id)
    if not results:
        typer.echo(f"No results to export for queue '{queue_id}'.")
        return

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    typer.echo(f"Exported {len(results)} results to {out_path}")


# Register export app as a group
app.add_typer(export_app, name="export")

# Register bulk app as a group
app.add_typer(bulk_app, name="bulk")

# -----------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------

@app.command(name="list")
def list_sops() -> None:
    """List all available SOPs."""
    names = _list_sops()
    if not names:
        typer.echo("No SOPs found.")
    else:
        typer.echo(f"Available SOPs ({len(names)}):")
        for name in names:
            typer.echo(f"  - {name}")


@app.command(name="create")
def create(name: str) -> None:
    """Create a new SOP scaffold (blog_post template) in the sops/ directory."""
    path = create_sop(name, _DEFAULT_SOP)
    typer.echo(f"SOP '{name}' created at {path}")


@app.command(name="run")
def run(
    name: str,
    input: str = typer.Option(..., "--input", "-i", help="JSON string or @file.json for input data."),
    mock: bool = typer.Option(False, "--mock", "-m", help="Use mock LLM instead of real calls."),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o", help="Directory to save execution results."),
    agent_mode: Optional[str] = typer.Option(
        None,
        "--agent-mode",
        "-a",
        help="Agent mode for multi-agent execution (fast, balanced, quality).",
    ),
) -> None:
    """Run an SOP by name with the given input data."""
    # Resolve input
    if input.startswith("@"):
        input_path = Path(input[1:])
        if not input_path.exists():
            typer.echo(f"Error: input file not found: {input_path}", err=True)
            raise typer.Exit(1)
        raw = input_path.read_text(encoding="utf-8")
    else:
        raw = input

    try:
        input_data = json.loads(raw)
    except json.JSONDecodeError as exc:
        typer.echo(f"Error: invalid JSON input: {exc}", err=True)
        raise typer.Exit(1)

    # Load SOP
    try:
        sop = get_sop(name)
    except FileNotFoundError:
        typer.echo(f"Error: SOP '{name}' not found.", err=True)
        raise typer.Exit(1)
    except Exception as exc:
        typer.echo(f"Error loading SOP '{name}': {exc}", err=True)
        raise typer.Exit(1)

    # Execute
    if agent_mode:
        # Multi-agent execution path
        _run_with_agent_mode(name, input_data, agent_mode, output_dir)
    else:
        llm_client = MockLLMClient() if mock else None
        executor = SOPExecutor(sop, llm_client)

        try:
            result = executor.run(input_data)
        except ValueError as exc:
            typer.echo(f"Execution error: {exc}", err=True)
            raise typer.Exit(1)

        # Print result
        typer.echo(json.dumps(result, indent=2, ensure_ascii=False))

        # Save to output directory if requested
        if output_dir:
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            (out / f"{name}_output.json").write_text(
                json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            log_data = [
                {"step": entry.step_name, "duration": entry.duration_seconds, "error": entry.error}
                for entry in executor.get_execution_log()
            ]
            (out / f"{name}_log.json").write_text(
                json.dumps(log_data, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            typer.echo(f"Results saved to {out}")


def _run_with_agent_mode(
    sop_name: str,
    input_data: dict,
    mode: str,
    output_dir: Optional[str],
) -> None:
    """Run SOP using multi-agent execution with the given agent mode."""
    from .agent_config import AgentConfigList, AgentMode, get_preset
    from .agent_registry import AgentRegistry
    from .multi_agent import MultiAgentSOPExecutor

    # Validate mode
    try:
        agent_mode = AgentMode(mode)
    except ValueError:
        typer.echo(f"Error: invalid agent mode '{mode}'. Choose from: fast, balanced, quality.", err=True)
        raise typer.Exit(1)

    # Build agent config from preset
    preset = get_preset(agent_mode)
    acl = AgentConfigList()
    acl.add_config(0, type(acl.get_config(0)).from_dict(preset) if acl.get_config(0) else None)

    # For now, create a simple config
    from .agent_config import AgentConfig
    config = AgentConfig(
        provider=preset["provider"],
        model=preset["model"],
        temperature=preset["temperature"],
        max_tokens=preset.get("max_tokens"),
    )
    acl.add_config(0, config)

    # Create registry and router
    registry = AgentRegistry()
    router = registry.get_router()

    # Create executor
    base_dir = Path(output_dir) if output_dir else Path(".")
    executor = MultiAgentSOPExecutor(
        sop_name=sop_name,
        agent_config_list=acl,
        router=router,
        base_dir=base_dir,
    )

    try:
        result = executor.run(input_data)
    except RuntimeError as exc:
        typer.echo(f"Multi-agent execution error: {exc}", err=True)
        raise typer.Exit(1)

    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))

    # Save to output directory if requested
    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{sop_name}_output.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        typer.echo(f"Results saved to {out}")


# -----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

if __name__ == "__main__":
    app()


# ====== API Server Subcommand ======

api_app = typer.Typer(
    name="api",
    help="Start the Drop Servicing Tool API server.",
)


@api_app.command(name="start")
def api_start(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Host to bind to."),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to."),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload for development."),
) -> None:
    """Start the API server using uvicorn."""
    typer.echo(f"Starting API server on {host}:{port}...")
    typer.echo("Press Ctrl+C to stop.")

    import uvicorn
    uvicorn.run(
        "drop_servicing_tool.api_server:app",
        host=host,
        port=port,
        reload=reload,
    )


# Register api app as a group
app.add_typer(api_app, name="api")
