"""VAST.ai instance status polling utilities.

Provides functions for polling the status of a VAST.ai instance
and waiting for it to reach a desired state.
"""

import time
from typing import Any


def poll_instance_status(
    instance_id: str,
    preset: dict[str, Any],
    target_states: list[str] | None = None,
) -> str:
    """Poll the status of a VAST.ai instance until it reaches a target state.

    Args:
        instance_id: The ID of the instance to query.
        preset: The preset dictionary containing configuration options.
        target_states: List of target states to wait for. Defaults to ['running'].

    Returns:
        The final status string from the API.

    Raises:
        TimeoutError: If the instance does not reach a target state within the timeout.
    """
    if target_states is None:
        target_states = ["running"]

    timeout = preset.get("timeout", 300)
    poll_interval = preset.get("poll_interval", 10)

    start_time = time.time()
    while True:
        status = get_instance_status(instance_id)
        if status in target_states:
            return status
        if time.time() - start_time > timeout:
            raise TimeoutError(
                f"Instance {instance_id} did not reach target states {target_states} "
                f"within {timeout} seconds. Current status: {status}"
            )
        time.sleep(poll_interval)


def get_instance_status(instance_id: str) -> str:
    """Get the current status of a VAST.ai instance.

    Args:
        instance_id: The ID of the instance to query.

    Returns:
        The current status string from the API.
    """
    try:
        api_key = authenticate()
        if not api_key:
            return "unreachable"

        import requests
        from .auth import get_auth_headers

        headers = get_auth_headers(api_key)
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


def authenticate() -> str | None:
    """Authenticate with the VAST.ai API.

    Returns:
        The API key string if authentication succeeds, None otherwise.
    """
    import os
    api_key = os.environ.get("VASTAI_API_KEY")
    if api_key and api_key.strip():
        return api_key.strip()

    from pathlib import Path
    import configparser
    config_path = Path.home() / ".vastai-init" / "config.ini"
    if config_path.exists():
        try:
            config = configparser.ConfigParser()
            config.read(config_path)
            if "api" in config and "api_key" in config["api"]:
                key = config["api"]["api_key"].strip()
                if key:
                    return key
        except (configparser.Error, KeyError):
            pass

    return None
