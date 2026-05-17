"""VAST.ai instance runner.

Orchestrates the launch of VAST.ai instances using preset configurations.
"""

import json
import threading
from pathlib import Path
from typing import Any

from .presets import load_preset
from .api import create_instance
from .status import poll_instance_status
from .session import log_session


# Thread-safe seeded set
_seeded_lock = threading.Lock()
_seeded_this_session: set[str] = set()


def seed_from_master_list(bus: Any) -> bool:
    """Seed the pipeline with ideas from the master ideas file.

    Args:
        bus: The message bus to send seed messages to.

    Returns:
        True if at least one idea was seeded, False otherwise.
    """
    master_ideas_path = Path.home() / ".vastai-init" / "master_ideas.md"
    if not master_ideas_path.exists():
        return False

    try:
        content = master_ideas_path.read_text()
    except Exception:
        return False

    # Parse master ideas
    import re
    pattern = r"- \[ \] \*\*(.+?)\*\* — \[(.+?)(?:\. requires: (.+))?\]"
    matches = re.findall(pattern, content)

    seeded = False
    with _seeded_lock:
        for match in matches:
            title = match[0]
            description = match[1]
            requires = match[2] if match[2] else None

            # Check dependencies
            if requires:
                deps = [dep.strip() for dep in requires.split(",")]
                if not all(dep in _seeded_this_session for dep in deps):
                    continue

            # Create message
            msg = {
                "title": title,
                "description": description,
                "requires": requires,
            }

            # Send message to bus
            try:
                bus.send(msg)
                _seeded_this_session.add(title)
                seeded = True
            except Exception:
                pass

    return seeded


def run_instance(preset_name: str | Path | None = None, preset_path: str | Path | None = None) -> dict[str, Any]:
    """Run a VAST.ai instance using a preset.

    Args:
        preset_name: Name of a built-in preset.
        preset_path: Path to a preset YAML file.

    Returns:
        Dictionary with instance details.

    Raises:
        ValueError: If neither preset_name nor preset_path is provided.
        FileNotFoundError: If the preset file does not exist.
    """
    if not preset_name and not preset_path:
        raise ValueError("Please provide either preset_name or preset_path.")

    # Load preset
    if preset_name:
        preset = load_preset(preset_name)
    else:
        preset = load_preset(preset_path)

    # Create instance
    instance_id = create_instance(preset)
    if not instance_id:
        raise RuntimeError("Failed to create instance.")

    # Poll for status
    final_status = poll_instance_status(instance_id, preset)

    # Log session
    log_session(preset, instance_id)

    return {
        "instance_id": instance_id,
        "preset": preset,
        "status": final_status,
    }


def clear_seeded_session() -> None:
    """Clear the seeded set for a new session."""
    with _seeded_lock:
        _seeded_this_session.clear()
