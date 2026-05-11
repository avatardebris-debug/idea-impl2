"""SOP Template Manager — CRUD, versioning, and validation for service offerings."""

from __future__ import annotations

import json
import os
from typing import Any

from core.service_offering import ServiceOffering


class TemplateManager:
    """
    Manages SOP templates: create, list, edit, delete, and versioning.
    Stores SOPs as JSON files in a configurable directory.
    """

    def __init__(self, storage_dir: str = "sop_templates"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def _filepath(self, name: str) -> str:
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        return os.path.join(self.storage_dir, f"{safe_name}.json")

    def create(self, offering: ServiceOffering) -> str:
        """Create a new SOP. Returns the filename (key)."""
        errors = offering.validate_self()
        if errors:
            raise ValueError(f"Validation failed: {'; '.join(errors)}")

        filepath = self._filepath(offering.title)
        with open(filepath, "w") as f:
            json.dump(offering.to_dict(), f, indent=2)
        return offering.title

    def get(self, name: str) -> ServiceOffering:
        """Load an SOP by name."""
        filepath = self._filepath(name)
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"SOP not found: {name}")
        with open(filepath, "r") as f:
            return ServiceOffering.from_dict(json.load(f))

    def list_all(self) -> list[ServiceOffering]:
        """List all stored SOPs."""
        sops = []
        for filename in os.listdir(self.storage_dir):
            if filename.endswith(".json"):
                filepath = os.path.join(self.storage_dir, filename)
                with open(filepath, "r") as f:
                    sops.append(ServiceOffering.from_dict(json.load(f)))
        return sops

    def edit(self, name: str, updates: dict[str, Any]) -> ServiceOffering:
        """Edit an existing SOP. Returns the updated SOP."""
        offering = self.get(name)
        offering.update(**updates)
        filepath = self._filepath(offering.title)
        with open(filepath, "w") as f:
            json.dump(offering.to_dict(), f, indent=2)
        return offering

    def delete(self, name: str) -> bool:
        """Delete an SOP by name. Returns True if deleted."""
        filepath = self._filepath(name)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False

    def get_versions(self, name: str) -> list[ServiceOffering]:
        """
        Return version history for an SOP.
        Currently returns the current version (extendable for full history).
        """
        offering = self.get(name)
        return [offering]
