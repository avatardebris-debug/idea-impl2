"""Session logging module.

After a successful launch, outputs SSH connection details and persists
the full session metadata to a local JSON session log file.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def log_session(
    preset: dict,
    instance_id: str,
    status: str,
    ssh_command: str | None = None,
    instance_ip: str | None = None,
) -> Path:
    """Log the session metadata to a local JSON file.

    Args:
        preset: The preset configuration used for the launch.
        instance_id: The ID of the launched instance.
        status: The final status of the instance.
        ssh_command: The SSH connection command (if available).
        instance_ip: The instance IP address (if available).

    Returns:
        The path to the session log file.
    """
    session_dir = Path.home() / ".vastai-init" / "sessions"
    session_dir.mkdir(parents=True, exist_ok=True)

    session_log = session_dir / "sessions.json"

    session_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "preset_name": preset.get("name", "unnamed"),
        "preset_path": str(preset.get("_source_path", "unknown")),
        "instance_id": instance_id,
        "status": status,
        "gpu_type": preset.get("gpu_type", "unknown"),
        "price_cap": preset.get("price_cap", "N/A"),
        "storage": preset.get("storage", "N/A"),
        "image": preset.get("image", "N/A"),
        "ssh_command": ssh_command,
        "instance_ip": instance_ip,
    }

    # Append to existing session log
    sessions = []
    if session_log.exists():
        try:
            with open(session_log, "r") as f:
                sessions = json.load(f)
        except (json.JSONDecodeError, IOError):
            sessions = []

    sessions.append(session_entry)

    with open(session_log, "w") as f:
        json.dump(sessions, f, indent=2)

    # Output SSH connection details
    if ssh_command:
        print(f"\n🔗 SSH Connection Details:")
        print(f"   Instance ID: {instance_id}")
        print(f"   IP: {instance_ip or 'N/A'}")
        print(f"   Command: {ssh_command}")
    else:
        print(f"\n✅ Instance {instance_id} launched successfully.")
        print(f"   Status: {status}")
        print(f"   Session log: {session_log}")

    return session_log


def get_ssh_command(preset: dict, instance_id: str, ssh_key: str | None = None) -> str:
    """Generate an SSH command for the instance.

    Args:
        preset: The preset configuration.
        instance_id: The ID of the instance.
        ssh_key: Optional SSH key path.

    Returns:
        The SSH command string.
    """
    instance_ip = preset.get("instance_ip", "unknown")
    username = "root"
    if ssh_key:
        return f"ssh -i {ssh_key} {username}@{instance_ip}"
    return f"ssh {username}@{instance_ip}"


def get_session_log() -> Path:
    """Get the path to the session log file.

    Returns:
        The path to the sessions.json file.
    """
    return Path.home() / ".vastai-init" / "sessions" / "sessions.json"


def get_recent_sessions(count: int = 5) -> list[dict]:
    """Get the most recent session entries.

    Args:
        count: Number of recent sessions to return.

    Returns:
        List of session entry dictionaries.
    """
    log_path = get_session_log()
    if not log_path.exists():
        return []

    try:
        with open(log_path, "r") as f:
            sessions = json.load(f)
        return sessions[-count:] if len(sessions) >= count else sessions
    except (json.JSONDecodeError, IOError):
        return []
