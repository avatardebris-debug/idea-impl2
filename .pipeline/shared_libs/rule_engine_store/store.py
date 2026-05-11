"""RuleStore — loads and saves rules to/from JSON files."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from rule_engine.models import Rule

logger = logging.getLogger(__name__)


class RuleStoreError(Exception):
    """Raised when a RuleStore operation fails."""


class RuleStore:
    """Persists rules to and from JSON files.

    Supports saving a list of Rule objects and loading them back
    without data loss.
    """

    def save(self, rules: list[Rule], filepath: str) -> None:
        """Save a list of rules to a JSON file.

        Creates parent directories if they don't exist.

        Args:
            rules: The list of Rule objects to save.
            filepath: The path to the JSON file.

        Raises:
            RuleStoreError: If the file cannot be written.
        """
        try:
            # Create parent directories if needed
            parent_dir = os.path.dirname(filepath)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            data: list[dict[str, Any]] = [rule.to_dict() for rule in rules]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info("Saved %d rules to %s", len(rules), filepath)
        except (IOError, OSError) as e:
            raise RuleStoreError(f"Failed to save rules to {filepath}: {e}") from e

    def load(self, filepath: str) -> list[Rule]:
        """Load rules from a JSON file.

        Args:
            filepath: The path to the JSON file.

        Returns:
            A list of Rule objects.

        Raises:
            RuleStoreError: If the file cannot be read or contains invalid JSON.
        """
        try:
            if not os.path.exists(filepath):
                raise RuleStoreError(f"File not found: {filepath}")

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                logger.warning("Empty file %s, returning empty rule list", filepath)
                return []

            data = json.loads(content)

            if not isinstance(data, list):
                raise RuleStoreError(
                    f"Invalid JSON structure in {filepath}: expected a list"
                )

            rules = [Rule.from_dict(item) for item in data]
            logger.info("Loaded %d rules from %s", len(rules), filepath)
            return rules

        except json.JSONDecodeError as e:
            raise RuleStoreError(
                f"Invalid JSON in {filepath}: {e}"
            ) from e
        except (IOError, OSError) as e:
            raise RuleStoreError(f"Failed to load rules from {filepath}: {e}") from e
