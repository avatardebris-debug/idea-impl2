"""SOP Store — Filesystem-based CRUD for SOP YAML files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from .config import get_sops_dir
from .sop_schema import SOP, load_sop


def _get_sops_dir() -> Path:
    """Return the SOPs directory as a Path object."""
    return get_sops_dir()


def list_sops(sops_dir: Path | None = None) -> list[str]:
    """Return sorted list of SOP names (without .yaml extension)."""
    sops_dir = sops_dir or get_sops_dir()
    if not sops_dir.exists():
        return []
    return sorted(p.stem for p in sops_dir.glob("*.yaml"))


def get_sop_path(name: str, sops_dir: Path | None = None) -> Optional[Path]:
    """Return the full path to an SOP YAML file, or None if not found."""
    sops_dir = sops_dir or get_sops_dir()
    path = sops_dir / f"{name}.yaml"
    return path if path.exists() else None


def get_sop(name: str, sops_dir: Path | None = None) -> SOP:
    """Load and validate an SOP by name."""
    path = get_sop_path(name, sops_dir)
    if path is None:
        raise FileNotFoundError(f"SOP '{name}' not found")
    return load_sop(path)


def save_sop(sop: SOP, sops_dir: Path | None = None) -> Path:
    """Save an SOP object to a YAML file.

    Args:
        sop:        SOP object to save.
        sops_dir:   Override the default SOPs directory.

    Returns:
        The path to the saved file.
    """
    sops_dir = sops_dir or get_sops_dir()
    sops_dir.mkdir(parents=True, exist_ok=True)
    path = sops_dir / f"{sop.name}.yaml"

    import yaml as _yaml
    content = _yaml.dump(
        sop.model_dump(),
        default_flow_style=False,
        sort_keys=False,
    )
    path.write_text(content, encoding="utf-8")
    return path


def create_sop(
    name: str,
    yaml_content: str | dict,
    sops_dir: Path | None = None,
) -> Path:
    """Write a new SOP YAML file.

    Args:
        name:       SOP name (used as filename stem).
        yaml_content:  Raw YAML string or a dict that will be dumped to YAML.
        sops_dir:     Override the default SOPs directory.

    Returns:
        The path to the created file.
    """
    sops_dir = sops_dir or get_sops_dir()
    sops_dir.mkdir(parents=True, exist_ok=True)
    path = sops_dir / f"{name}.yaml"

    if isinstance(yaml_content, dict):
        import yaml as _yaml
        content = _yaml.dump(yaml_content, default_flow_style=False, sort_keys=False)
    else:
        content = yaml_content

    path.write_text(content, encoding="utf-8")
    return path


def delete_sop(name: str, sops_dir: Path | None = None) -> bool:
    """Remove an SOP file. Returns True if it existed, False otherwise."""
    sops_dir = sops_dir or get_sops_dir()
    path = get_sop_path(name, sops_dir)
    if path is not None and path.exists():
        path.unlink()
        return True
    return False


class SOPStore:
    """Filesystem-based store for SOPs with CRUD operations."""

    def __init__(self, sops_dir: Path | None = None):
        """Initialize the SOP store.
        
        Args:
            sops_dir: Directory to store SOP files. Defaults to config-sops_dir.
        """
        self.sops_dir = Path(sops_dir) if sops_dir else get_sops_dir()
        self.sops_dir.mkdir(parents=True, exist_ok=True)

    def list_sops(self) -> list[SOP]:
        """Return list of all loaded SOPs."""
        sop_names = list_sops(self.sops_dir)
        return [get_sop(name, self.sops_dir) for name in sop_names]

    def get_sop(self, name: str) -> SOP:
        """Load and return an SOP by name."""
        return get_sop(name, self.sops_dir)

    def save_sop(self, sop: SOP) -> Path:
        """Save an SOP to the store."""
        return save_sop(sop, self.sops_dir)

    def create_sop(
        self,
        name: str,
        yaml_content: str | dict,
    ) -> Path:
        """Create a new SOP in the store."""
        return create_sop(name, yaml_content, self.sops_dir)

    def delete_sop(self, name: str) -> bool:
        """Delete an SOP from the store. Returns True if it existed."""
        return delete_sop(name, self.sops_dir)

    def exists(self, name: str) -> bool:
        """Check if an SOP exists in the store."""
        return get_sop_path(name, self.sops_dir) is not None
