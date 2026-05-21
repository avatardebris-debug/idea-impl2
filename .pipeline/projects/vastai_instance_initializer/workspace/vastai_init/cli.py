"""CLI entry point for the VAST.ai Instance Initializer.

Provides the `vastai-init` command-line interface with a `launch` subcommand
that loads a preset file, validates it, and initiates instance creation.
"""

import sys
from pathlib import Path

import typer

from vastai_init.presets.validator import PresetValidationError, load_preset

app = typer.Typer(
    name="vastai-init",
    help="VAST.ai Instance Initializer — launch instances from preset files.",
    add_completion=False,
)


@app.command("launch")
def launch(
    preset_path: str = typer.Argument(
        ...,
        help="Path to the YAML preset file to use for the instance launch.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Validate the preset and show the configuration without launching.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output during execution.",
    ),
) -> None:
    """Launch a VAST.ai instance using a preset file.

    Reads the preset, validates it, and initiates the instance creation process.
    """
    preset_file = Path(preset_path)

    # Validate preset file exists
    if not preset_file.exists():
        typer.echo(f"Error: Preset file not found: {preset_file}", err=True)
        raise typer.Exit(code=1)

    # Load and validate the preset
    try:
        preset = load_preset(preset_file)
    except PresetValidationError as e:
        typer.echo(f"Error: Invalid preset: {e}", err=True)
        raise typer.Exit(code=1)
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    if verbose:
        typer.echo(f"Loaded preset from: {preset_file.resolve()}")
        typer.echo(f"Preset name: {preset.get('name', 'unnamed')}")
        typer.echo(f"GPU type: {preset.get('gpu_type', 'unknown')}")
        typer.echo(f"Price cap: {preset.get('price_cap', 'N/A')}")
        typer.echo(f"Storage: {preset.get('storage', 'N/A')}")
        typer.echo(f"Image: {preset.get('image', 'N/A')}")

    if dry_run:
        typer.echo("\n[Dry run] Preset is valid. No instance will be launched.")
        typer.echo("Run without --dry-run to launch the instance.")
        return

    # Import and use the adapter to launch the instance
    try:
        from vastai_init.api.adapter import create_instance
        from vastai_init.monitor.status import poll_instance_status
        from vastai_init.launcher.session import log_session

        # Create the instance
        typer.echo("Authenticating with VAST.ai API...")
        instance_id = create_instance(preset)

        if instance_id:
            typer.echo(f"Instance created with ID: {instance_id}")
            typer.echo("Polling instance status...")

            # Poll until running or terminal state
            status = poll_instance_status(instance_id, preset)

            if status == "running":
                typer.echo(f"Instance {instance_id} is now running!")
                log_session(preset, instance_id, status)
            else:
                typer.echo(
                    f"Instance {instance_id} reached terminal state: {status}",
                    err=True,
                )
                log_session(preset, instance_id, status)
                raise typer.Exit(code=1)
        else:
            typer.echo("Error: Failed to create instance.", err=True)
            raise typer.Exit(code=1)

    except ImportError as e:
        typer.echo(f"Error: Missing dependency: {e}", err=True)
        typer.echo("Install required packages: pip install requests pyyaml typer")
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Error during launch: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("validate")
def validate(
    preset_path: str = typer.Argument(
        ...,
        help="Path to the YAML preset file to validate.",
    ),
) -> None:
    """Validate a preset file without launching an instance."""
    preset_file = Path(preset_path)

    if not preset_file.exists():
        typer.echo(f"Error: Preset file not found: {preset_file}", err=True)
        raise typer.Exit(code=1)

    try:
        preset = load_preset(preset_file)
        typer.echo(f"Preset '{preset.get('name', 'unnamed')}' is valid.")
        typer.echo(f"  GPU type: {preset.get('gpu_type', 'N/A')}")
        typer.echo(f"  Price cap: {preset.get('price_cap', 'N/A')}")
        typer.echo(f"  Storage: {preset.get('storage', 'N/A')}")
        typer.echo(f"  Image: {preset.get('image', 'N/A')}")
    except PresetValidationError as e:
        typer.echo(f"Validation failed: {e}", err=True)
        raise typer.Exit(code=1)


# ── batch command group ────────────────────────────────────────

batch_app = typer.Typer(
    name="batch",
    help="Batch launch commands for VAST.ai instances.",
    add_completion=False,
)


@batch_app.command("launch")
def batch_launch(
    batch_config: str = typer.Argument(
        ...,
        help="Path to the YAML batch config file.",
    ),
    delay: int = typer.Option(
        0,
        "--delay",
        "-d",
        help="Override the delay (seconds) between instance launches.",
    ),
    concurrency: int = typer.Option(
        1,
        "--concurrency",
        "-c",
        help="Override the maximum number of parallel launches.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Expand tasks and print them without launching.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed output during execution.",
    ),
    resume_from: str = typer.Option(
        None,
        "--resume-from",
        "-r",
        help="Path to a saved batch state file to resume from.",
    ),
) -> None:
    """Launch a batch of VAST.ai instances from a batch config file.

    Reads the batch config, expands it into individual launch tasks,
    and launches them respecting timing and concurrency constraints.
    """
    from vastai_init.batch.config import load_batch_config
    from vastai_init.batch.validator import validate_batch_config
    from vastai_init.batch.orchestrator import BatchOrchestrator
    from vastai_init.batch.progress import BatchProgressView
    from vastai_init.batch.report import BatchReport
    from vastai_init.batch.state import load_batch_state
    from pathlib import Path

    batch_file = Path(batch_config)
    if not batch_file.exists():
        typer.echo(f"Error: Batch config file not found: {batch_file}", err=True)
        raise typer.Exit(code=1)

    # Load and validate
    try:
        config = load_batch_config(batch_file)
    except Exception as e:
        typer.echo(f"Error loading batch config: {e}", err=True)
        raise typer.Exit(code=1)

    try:
        validate_batch_config(config)
    except Exception as e:
        typer.echo(f"Validation error: {e}", err=True)
        raise typer.Exit(code=1)

    if verbose:
        typer.echo(f"Loaded batch config: {batch_file.resolve()}")
        typer.echo(f"Batch name: {config.name}")
        typer.echo(f"Preset references: {len(config.presets)}")
        for ref in config.presets:
            typer.echo(f"  - {ref.preset_path} (count={ref.count})")
        typer.echo(f"Timing: delay={config.timing.delay_seconds}s, stagger={config.timing.stagger_percent}%")
        typer.echo(f"Concurrency: {config.concurrency}")

    # Override timing/concurrency if flags provided
    if delay is not None and delay >= 0:
        config.timing.delay_seconds = delay
    if concurrency is not None and concurrency >= 1:
        config.concurrency = concurrency

    # Create orchestrator
    orchestrator = BatchOrchestrator(config)

    # Expand tasks
    tasks = orchestrator.expand()
    if verbose:
        typer.echo(f"\nExpanded {len(tasks)} launch tasks:")
        for t in tasks:
            typer.echo(f"  [{t.instance_id}] {t.preset_ref.preset_path} (count={t.preset_ref.count})")

    if dry_run:
        typer.echo("\n[Dry run] Tasks expanded successfully. No instances will be launched.")
        return

    # Resume from saved state if requested
    if resume_from:
        resume_path = Path(resume_from)
        if not resume_path.exists():
            typer.echo(f"Error: Resume state file not found: {resume_path}", err=True)
            raise typer.Exit(code=1)
        try:
            saved_state = load_batch_state(resume_path)
            orchestrator.batch_state = saved_state
            if verbose:
                typer.echo(f"\nResumed from state: {resume_path}")
        except Exception as e:
            typer.echo(f"Error loading resume state: {e}", err=True)
            raise typer.Exit(code=1)

    # Start progress view
    progress = BatchProgressView(orchestrator.batch_state)
    progress.start()

    # Run the batch
    try:
        result = orchestrator.start(progress_view=progress)
    except KeyboardInterrupt:
        typer.echo("\nBatch interrupted by user.")
        progress.stop()
        raise typer.Exit(code=130)
    finally:
        progress.stop()

    # Print report
    report = BatchReport(orchestrator.batch_state, result.total_elapsed)
    typer.echo(report.render())


@batch_app.command("list")
def batch_list(
    config_dir: str = typer.Option(
        "presets/batch",
        "--config-dir",
        "-d",
        help="Directory to search for batch config files.",
    ),
) -> None:
    """List available batch configuration files."""
    from vastai_init.batch.config import find_batch_configs
    from pathlib import Path

    batch_dir = Path(config_dir)
    if not batch_dir.exists():
        typer.echo(f"Batch config directory not found: {batch_dir}")
        typer.echo("Create the directory and add .yaml batch config files.")
        raise typer.Exit(code=1)

    configs = find_batch_configs(batch_dir)
    if not configs:
        typer.echo(f"No batch config files found in: {batch_dir}")
        return

    typer.echo(f"Available batch configs in {batch_dir}:")
    for cfg in configs:
        typer.echo(f"  - {cfg.name}: {cfg.preset_count} preset(s), {cfg.total_instances} instance(s)")


@app.callback()
def callback() -> None:
    """VAST.ai Instance Initializer — launch instances from preset files."""
    pass


def main() -> None:
    """Entry point for the vastai-init CLI."""
    app()


if __name__ == "__main__":
    main()
