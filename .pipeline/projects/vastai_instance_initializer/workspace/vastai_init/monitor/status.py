"""Instance monitoring and status polling module.

Provides a polling loop that queries the VAST.ai API for instance state
and reports progress updates until the instance reaches a terminal state.
"""

import time
from typing import Any


def poll_instance_status(
    instance_id: str,
    preset: dict[str, Any],
) -> str:
    """Poll the VAST.ai API for instance status until a terminal state is reached.

    Args:
        instance_id: The ID of the instance to poll.
        preset: The preset configuration (contains timeout and poll_interval).

    Returns:
        The final status of the instance (e.g., 'running', 'stopped', 'failed').

    Raises:
        RuntimeError: If polling fails or times out.
    """
    timeout = preset.get("timeout", 300)
    poll_interval = preset.get("poll_interval", 10)
    start_time = time.time()

    status_messages = {
        "queued": "⏳ Instance is queued, waiting for resources...",
        "starting": "🚀 Instance is starting up...",
        "running": "✅ Instance is running!",
        "stopped": "⏹️ Instance has stopped.",
        "failed": "❌ Instance failed to start.",
        "unreachable": "🔌 Instance is unreachable.",
    }

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise RuntimeError(
                f"Polling timed out after {timeout}s. "
                f"Instance {instance_id} may still be starting."
            )

        status = _get_instance_status(instance_id)
        status_text = status_messages.get(status, f"⏳ Unknown status: {status}")
        typer_echo(f"[{elapsed:.0f}s] {status_text}")

        if status in ("running", "stopped", "failed", "unreachable"):
            return status

        time.sleep(poll_interval)


def _get_instance_status(instance_id: str) -> str:
    """Query the VAST.ai API for the current instance status.

    Args:
        instance_id: The ID of the instance to query.

    Returns:
        The current status string from the API.
    """
    try:
        import requests
        from vastai_init.api.auth import authenticate

        api_key = authenticate()
        if not api_key:
            return "unreachable"

        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(
            f"https://cloud.vast.ai/api/v0x/instantiate/{instance_id}/",
            headers=headers,
            timeout=15,
        )

        if response.status_code == 200:
            data = response.json()
            return data.get("state", data.get("status", "unknown"))

        return "unreachable"

    except Exception:
        return "unreachable"


def typer_echo(message: str) -> None:
    """Print a message to stdout (mimics typer.echo for compatibility)."""
    print(message)


# Re-export for use in other modules
__all__ = ["poll_instance_status", "typer_echo"]
