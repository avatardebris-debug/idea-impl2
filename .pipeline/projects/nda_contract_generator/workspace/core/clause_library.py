"""JSON-backed clause registry for NDA contract generation."""

import json
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ClauseLibrary:
    """Loads and manages clause definitions from a JSON data file.

    Each clause has: name, default value, allowed values, description,
    and optional jurisdiction overrides.
    """

    def __init__(self, data_path: Optional[str] = None, overrides_path: Optional[str] = None):
        """Initialize the clause library.

        Args:
            data_path: Path to the JSON clause data file.
                        Defaults to clause_data.json in the same directory.
            overrides_path: Path to the JSON overrides file for persistence.
                           Defaults to clause_overrides.json in the same directory.
        """
        if data_path is None:
            data_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "clause_data.json"
            )
        self._data_path = data_path
        if overrides_path is None:
            overrides_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "clause_overrides.json"
            )
        self._overrides_path = overrides_path
        self._clauses: Dict[str, Dict[str, Any]] = {}
        self._overrides: Dict[str, str] = {}
        self._load()
        self._load_overrides()

    def _load(self) -> None:
        """Load clause definitions from the JSON data file."""
        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for clause in data.get("clauses", []):
                name = clause["name"]
                self._clauses[name] = {
                    "name": name,
                    "default": clause.get("default", ""),
                    "allowed_values": clause.get("allowed_values", []),
                    "description": clause.get("description", ""),
                    "jurisdiction_overrides": clause.get("jurisdiction_overrides", {}),
                }
            logger.info("Loaded %d clauses from %s", len(self._clauses), self._data_path)
        except FileNotFoundError:
            logger.error("Clause data file not found: %s", self._data_path)
            raise
        except json.JSONDecodeError as e:
            logger.error("Malformed JSON in clause data file: %s — %s", self._data_path, e)
            raise

    def _load_overrides(self) -> None:
        """Load persisted overrides from the overrides JSON file."""
        try:
            if os.path.exists(self._overrides_path):
                with open(self._overrides_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._overrides = data.get("overrides", {})
                logger.info("Loaded %d persisted overrides from %s", len(self._overrides), self._overrides_path)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not load overrides from %s: %s", self._overrides_path, e)
            self._overrides = {}

    def save_overrides(self) -> bool:
        """Save current overrides to the overrides JSON file.

        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            with open(self._overrides_path, "w", encoding="utf-8") as f:
                json.dump({"overrides": self._overrides}, f, indent=2)
            logger.info("Saved %d overrides to %s", len(self._overrides), self._overrides_path)
            return True
        except OSError as e:
            logger.error("Could not save overrides to %s: %s", self._overrides_path, e)
            return False

    def get_clause(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a clause definition by name.

        Args:
            name: The clause name.

        Returns:
            The clause definition dict, or None if not found.
        """
        clause = self._clauses.get(name)
        if clause is None:
            return None
        result = dict(clause)
        # Apply any global override
        if name in self._overrides:
            result["current_value"] = self._overrides[name]
        else:
            result["current_value"] = result["default"]
        return result

    def get_all_clauses(self) -> Dict[str, Dict[str, Any]]:
        """Get all clause definitions.

        Returns:
            Dict mapping clause names to their definitions.
        """
        result = {}
        for name, clause in self._clauses.items():
            entry = dict(clause)
            entry["current_value"] = self._overrides.get(name, clause["default"])
            result[name] = entry
        return result

    def get_allowed_values(self, name: str) -> List[str]:
        """Get the allowed values for a clause.

        Args:
            name: The clause name.

        Returns:
            List of allowed values, or empty list if clause not found.
        """
        clause = self._clauses.get(name)
        if clause is None:
            return []
        return list(clause["allowed_values"])

    def apply_overrides(self, jurisdiction: str) -> Dict[str, str]:
        """Apply jurisdiction-specific overrides to get effective clause values.

        Args:
            jurisdiction: The jurisdiction key (e.g., 'california').

        Returns:
            Dict mapping clause names to their effective values for the jurisdiction.
        """
        effective = {}
        for name, clause in self._clauses.items():
            overrides = clause.get("jurisdiction_overrides", {})
            if jurisdiction in overrides:
                effective[name] = overrides[jurisdiction]
            else:
                effective[name] = clause["default"]
        return effective

    def override_clause(self, name: str, value: str) -> bool:
        """Override a clause's default value.

        Args:
            name: The clause name.
            value: The new value to set.

        Returns:
            True if the override was applied, False if clause not found or value invalid.
        """
        clause = self._clauses.get(name)
        if clause is None:
            return False
        if value not in clause["allowed_values"]:
            return False
        self._overrides[name] = value
        return True

    def remove_override(self, name: str) -> bool:
        """Remove a clause override, reverting to default.

        Args:
            name: The clause name.

        Returns:
            True if the override was removed, False if no override existed.
        """
        if name in self._overrides:
            del self._overrides[name]
            return True
        return False

    def get_clause_count(self) -> int:
        """Get the total number of clauses in the library.

        Returns:
            Number of clauses.
        """
        return len(self._clauses)

    def list_clause_names(self) -> List[str]:
        """List all clause names.

        Returns:
            List of clause name strings.
        """
        return list(self._clauses.keys())
