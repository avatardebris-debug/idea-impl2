"""VAST.ai instance launcher CLI.

Command-line interface for launching and managing VAST.ai instances.
"""

import argparse
import json
import sys
from pathlib import Path

from .presets import load_preset
from .api import create_instance
from .status import poll_instance_status
from .session import log_session


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the VAST.ai instance launcher CLI.

    Args:
        argv: Command-line arguments. Defaults to sys.argv[1:].

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Launch a VAST.ai instance using a preset configuration."
    )
    parser.add_argument(
        "--preset",
        type=str,
        help="Path to the preset YAML file (alias for --preset-file).",
    )
    parser.add_argument(
        "--preset-file",
        type=str,
        help="Path to the preset YAML file.",
    )
    parser.add_argument(
        "--preset-name",
        type=str,
        help="Name of a built-in preset (e.g., 'default', 'training-gpu').",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to save the instance details as JSON.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the preset without launching the instance.",
    )

    args = parser.parse_args(argv)

    # Determine preset source
    preset_path = args.preset or args.preset_file
    preset_name = args.preset_name

    if not preset_path and not preset_name:
        print("Error: Please provide --preset-file or --preset-name.", file=sys.stderr)
        return 1

    # Load preset
    try:
        if preset_name:
            preset = load_preset(preset_name)
        else:
            preset = load_preset(preset_path)
    except Exception as e:
        print(f"Error loading preset: {e}", file=sys.stderr)
        return 1

    # Dry run validation
    if args.dry_run:
        print("Preset validation passed.")
        print(json.dumps(preset, indent=2))
        return 0

    # Launch instance
    try:
        instance_id = create_instance(preset)
        if not instance_id:
            print("Error: Failed to create instance.", file=sys.stderr)
            return 1

        print(f"Instance created with ID: {instance_id}")

        # Poll for status
        try:
            final_status = poll_instance_status(instance_id, preset)
            print(f"Instance status: {final_status}")
        except TimeoutError as e:
            print(f"Warning: {e}", file=sys.stderr)

        # Save instance details
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            instance_details = {
                "instance_id": instance_id,
                "preset": preset,
                "status": final_status if 'final_status' in locals() else "unknown",
            }
            with open(output_path, "w") as f:
                json.dump(instance_details, f, indent=2)
            print(f"Instance details saved to {output_path}")

        # Log session
        log_session(preset, instance_id)

        return 0

    except Exception as e:
        print(f"Error launching instance: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
