"""VAST.ai instance validator agent.

Validates VAST.ai instance configurations and dependencies.
"""

import json
from pathlib import Path
from typing import Any


class ValidatorAgent:
    """Validates VAST.ai instance configurations and dependencies."""

    def __init__(self, run_dir: Path) -> None:
        """Initialize the validator.

        Args:
            run_dir: Directory for running the pipeline.
        """
        self._run_dir = run_dir
        self._validation_results: list[dict[str, Any]] = []

    def validate(self, config: dict[str, Any]) -> dict[str, Any]:
        """Validate a VAST.ai instance configuration.

        Args:
            config: The configuration dictionary to validate.

        Returns:
            Dictionary with validation results.
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Check required fields
        required_fields = ["name", "gpu_type", "price_cap", "storage", "image"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: '{field}'")
            elif not str(config[field]).strip():
                errors.append(f"Field '{field}' must be a non-empty string")

        # Validate price_cap
        if "price_cap" in config:
            try:
                price = float(config["price_cap"])
                if price < 0:
                    errors.append("Field 'price_cap' must be non-negative")
            except (ValueError, TypeError):
                errors.append("Field 'price_cap' must be a valid number")

        # Validate storage
        if "storage" in config:
            storage = config["storage"]
            if isinstance(storage, str):
                if not any(unit in storage.upper() for unit in ["GB", "TB"]):
                    warnings.append("Field 'storage' should include a unit (GB or TB)")
            elif isinstance(storage, (int, float)):
                if storage < 0:
                    errors.append("Field 'storage' must be non-negative")

        # Check dependencies
        if "requires" in config:
            deps = config["requires"]
            if isinstance(deps, str):
                dep_list = [d.strip() for d in deps.split(",")]
                for dep in dep_list:
                    if not dep:
                        continue
                    dep_path = self._run_dir / f"{dep}.json"
                    if not dep_path.exists():
                        warnings.append(f"Dependency '{dep}' not found in run directory")

        # Check for circular dependencies
        if "requires" in config and isinstance(config["requires"], str):
            deps = [d.strip() for d in config["requires"].split(",") if d.strip()]
            if self._has_circular_dependency(config, deps, set()):
                errors.append("Circular dependency detected")

        result = {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

        self._validation_results.append(result)
        return result

    def _has_circular_dependency(
        self,
        config: dict[str, Any],
        deps: list[str],
        visited: set[str],
    ) -> bool:
        """Check for circular dependencies.

        Args:
            config: The current configuration.
            deps: List of dependencies to check.
            visited: Set of already visited dependencies.

        Returns:
            True if a circular dependency is detected, False otherwise.
        """
        for dep in deps:
            if dep in visited:
                return True
            visited.add(dep)

            # Load dependency config
            dep_path = self._run_dir / f"{dep}.json"
            if dep_path.exists():
                with open(dep_path, "r") as f:
                    dep_config = json.load(f)

                if "requires" in dep_config:
                    dep_deps = [d.strip() for d in dep_config["requires"].split(",") if d.strip()]
                    if self._has_circular_dependency(dep_config, dep_deps, visited):
                        return True

            visited.discard(dep)

        return False

    def get_validation_results(self) -> list[dict[str, Any]]:
        """Get all validation results.

        Returns:
            List of validation result dictionaries.
        """
        return list(self._validation_results)

    def clear_results(self) -> None:
        """Clear all validation results."""
        self._validation_results.clear()
