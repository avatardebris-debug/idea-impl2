"""VAST.ai API adapter module.

Handles creating instances on VAST.ai using the preset configuration.
"""

from .auth import authenticate


def create_instance(preset: dict) -> str | None:
    """Create a VAST.ai instance using the preset configuration.

    Args:
        preset: The validated preset dictionary with instance parameters.

    Returns:
        The instance ID if creation was successful, None otherwise.

    Raises:
        RuntimeError: If authentication fails or the API request fails.
    """
    api_key = authenticate()

    if not api_key:
        raise RuntimeError("Authentication failed: no valid API key available.")

    # Build the request payload from the preset
    payload = {
        "gpu_type": preset.get("gpu_type", ""),
        "price_cap": preset.get("price_cap", 0),
        "storage": preset.get("storage", "50GB"),
        "image": preset.get("image", "ubuntu:latest"),
        "disk_size": preset.get("disk_size"),
        "region": preset.get("region"),
        "min_vram": preset.get("min_vram"),
        "uptime": preset.get("uptime"),
        "ssh_public_key": preset.get("ssh_public_key"),
        "docker_args": preset.get("docker_args", {}),
        "ports": preset.get("ports", []),
        "labels": preset.get("labels", {}),
    }

    # Filter out None values
    payload = {k: v for k, v in payload.items() if v is not None}

    # Make the API call to VAST.ai
    try:
        import requests

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            "https://cloud.vast.ai/api/v0x/instantiate/",
            json=payload,
            headers=headers,
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            instance_id = result.get("id") or result.get("instance_id")
            if instance_id:
                return str(instance_id)

        # Handle specific error cases
        if response.status_code == 401:
            raise RuntimeError(
                "Authentication failed: invalid or expired API key."
            )
        elif response.status_code == 422:
            errors = response.json().get("errors", [])
            error_msg = "; ".join(str(e) for e in errors) if errors else "Invalid parameters"
            raise RuntimeError(f"Invalid instance parameters: {error_msg}")
        elif response.status_code == 503:
            raise RuntimeError(
                "No GPUs available: the requested GPU type is not available in any region."
            )
        else:
            raise RuntimeError(
                f"API error: HTTP {response.status_code} - {response.text[:200]}"
            )

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Failed to connect to VAST.ai API. Check your internet connection."
        )
    except requests.exceptions.Timeout:
        raise RuntimeError(
            "Request to VAST.ai API timed out. Try again later."
        )

    return None
