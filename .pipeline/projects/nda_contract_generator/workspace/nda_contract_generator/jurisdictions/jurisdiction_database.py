"""Jurisdiction database — loads and manages jurisdiction configurations."""

import importlib
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Mapping of jurisdiction keys to their module paths
_JURISDICTION_MODULES = {
    "california": "nda_contract_generator.jurisdictions.us.california",
    "england_wales": "nda_contract_generator.jurisdictions.uk.england_wales",
    "gdpr_compliant": "nda_contract_generator.jurisdictions.eu.gdpr_compliant",
}


class JurisdictionDatabase:
    """Loads and manages jurisdiction configurations from module files."""

    def __init__(self):
        """Initialize the jurisdiction database."""
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all jurisdiction configurations."""
        for key, module_path in _JURISDICTION_MODULES.items():
            try:
                module = importlib.import_module(module_path)
                config = module.get_config()
                self._configs[key] = config
                logger.info("Loaded jurisdiction '%s' from %s", key, module_path)
            except ImportError as e:
                logger.warning("Could not load jurisdiction '%s': %s", key, e)

    def get_config(self, key: str) -> Optional[Dict[str, Any]]:
        """Get the configuration for a jurisdiction.

        Args:
            key: The jurisdiction key (e.g., 'california').

        Returns:
            The jurisdiction config dict, or None if not found.
        """
        config = self._configs.get(key)
        if config is None:
            logger.warning("Unknown jurisdiction key: '%s'", key)
        return config

    def get_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all jurisdiction configurations.

        Returns:
            Dict mapping jurisdiction keys to their configs.
        """
        return dict(self._configs)

    def list_jurisdictions(self) -> List[str]:
        """List all available jurisdiction keys.

        Returns:
            List of jurisdiction key strings.
        """
        return list(self._configs.keys())

    def get_display_name(self, key: str) -> Optional[str]:
        """Get the display name for a jurisdiction.

        Args:
            key: The jurisdiction key.

        Returns:
            The display name, or None if not found.
        """
        config = self._configs.get(key)
        if config is None:
            return None
        return config.get("display_name")

    def get_governing_law(self, key: str) -> Optional[str]:
        """Get the governing law for a jurisdiction.

        Args:
            key: The jurisdiction key.

        Returns:
            The governing law string, or None if not found.
        """
        config = self._configs.get(key)
        if config is None:
            return None
        return config.get("governing_law")

    def get_required_clauses(self, key: str) -> List[str]:
        """Get the required clauses for a jurisdiction.

        Args:
            key: The jurisdiction key.

        Returns:
            List of required clause names, or empty list if not found.
        """
        config = self._configs.get(key)
        if config is None:
            return []
        return list(config.get("required_clauses", []))

    def get_optional_clauses(self, key: str) -> List[str]:
        """Get the optional clauses for a jurisdiction.

        Args:
            key: The jurisdiction key.

        Returns:
            List of optional clause names, or empty list if not found.
        """
        config = self._configs.get(key)
        if config is None:
            return []
        return list(config.get("optional_clauses", []))

    def get_mandatory_fields(self, key: str) -> List[str]:
        """Get the mandatory form fields for a jurisdiction.

        Args:
            key: The jurisdiction key.

        Returns:
            List of mandatory field names, or empty list if not found.
        """
        config = self._configs.get(key)
        if config is None:
            return []
        return list(config.get("mandatory_fields", []))

    def get_special_notes(self, key: str) -> List[str]:
        """Get the special notes for a jurisdiction.

        Args:
            key: The jurisdiction key.

        Returns:
            List of special note strings, or empty list if not found.
        """
        config = self._configs.get(key)
        if config is None:
            return []
        return list(config.get("special_notes", []))

    def get_default_term(self, key: str) -> Optional[str]:
        """Get the default term for a jurisdiction.

        Args:
            key: The jurisdiction key.

        Returns:
            The default term string, or None if not found.
        """
        config = self._configs.get(key)
        if config is None:
            return None
        return config.get("default_term")

    def get_template_path(self, key: str) -> Optional[str]:
        """Get the template path for a jurisdiction.

        Args:
            key: The jurisdiction key.

        Returns:
            The template path string, or None if not found.
        """
        config = self._configs.get(key)
        if config is None:
            return None
        return config.get("template_path")

    def get_config_count(self) -> int:
        """Get the total number of jurisdictions.

        Returns:
            Number of jurisdictions.
        """
        return len(self._configs)

    def validate_jurisdiction(self, key: str) -> bool:
        """Check if a jurisdiction key is valid.

        Args:
            key: The jurisdiction key to validate.

        Returns:
            True if the jurisdiction exists, False otherwise.
        """
        return key in self._configs

    def get_all_special_notes(self) -> Dict[str, List[str]]:
        """Get all special notes for all jurisdictions.

        Returns:
            Dict mapping jurisdiction keys to their special notes.
        """
        result = {}
        for key in self._configs:
            result[key] = self.get_special_notes(key)
        return result

    def get_all_mandatory_fields(self) -> Dict[str, List[str]]:
        """Get all mandatory fields for all jurisdictions.

        Returns:
            Dict mapping jurisdiction keys to their mandatory fields.
        """
        result = {}
        for key in self._configs:
            result[key] = self.get_mandatory_fields(key)
        return result

    def validate_clauses(self, key: str, provided_clauses: List[str]) -> Dict[str, Any]:
        """Validate that all required clauses for a jurisdiction are present.

        Args:
            key: The jurisdiction key.
            provided_clauses: List of clause names present in the contract.

        Returns:
            Dict with 'valid' (bool), 'missing' (list), and 'extra' (list).
        """
        config = self._configs.get(key)
        if config is None:
            return {"valid": False, "missing": [], "extra": [], "error": f"Unknown jurisdiction: {key}"}

        required = set(config.get("required_clauses", []))
        optional = set(config.get("optional_clauses", []))
        provided = set(provided_clauses)

        missing = list(required - provided)
        extra = list(provided - required - optional)
        valid = len(missing) == 0

        return {
            "valid": valid,
            "missing": missing,
            "extra": extra,
        }
