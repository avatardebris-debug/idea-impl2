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


@app.callback()
def callback() -> None:
    """VAST.ai Instance Initializer — launch instances from preset files."""
    pass


def main() -> None:
    """Entry point for the vastai-init CLI."""
    app()


if __name__ == "__main__":
    main()
