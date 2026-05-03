"""File persistence layer for saving and loading VirtualFileSystem state to disk."""

from __future__ import annotations

import json
import os
from typing import Any


class FilePersistence:
    """Handles saving and loading VirtualFileSystem state to/from disk.

    Uses JSON format for persistence. Supports custom file paths and
    automatic directory creation for the persistence file.

    Attributes:
        file_path: Path to the JSON file used for persistence.
    """

    def __init__(self, file_path: str = "pocketknife_filesystem.json") -> None:
        """Initialize the FilePersistence layer.

        Args:
            file_path: Path to the JSON file for persistence.
        """
        self.file_path = file_path

    def save(self, data: dict[str, Any]) -> bool:
        """Save data to the persistence file.

        Args:
            data: Dictionary to save.

        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            # Ensure the directory exists
            directory = os.path.dirname(self.file_path)
            if directory:
                os.makedirs(directory, exist_ok=True)

            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError, TypeError, ValueError) as e:
            print(f"Error saving file: {e}")
            return False

    def load(self) -> dict[str, Any] | None:
        """Load data from the persistence file.

        Returns:
            Dictionary of loaded data, or None if the file does not exist
            or cannot be loaded.
        """
        if not os.path.exists(self.file_path):
            return None

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, OSError, json.JSONDecodeError, ValueError) as e:
            print(f"Error loading file: {e}")
            return None

    def exists(self) -> bool:
        """Check if the persistence file exists.

        Returns:
            True if the file exists, False otherwise.
        """
        return os.path.exists(self.file_path)

    def delete(self) -> bool:
        """Delete the persistence file.

        Returns:
            True if deleted successfully, False otherwise.
        """
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
                return True
            return False
        except (IOError, OSError) as e:
            print(f"Error deleting file: {e}")
            return False

    def get_file_path(self) -> str:
        """Get the current file path.

        Returns:
            The file path string.
        """
        return self.file_path

    def set_file_path(self, file_path: str) -> None:
        """Set a new file path for persistence.

        Args:
            file_path: New file path.
        """
        self.file_path = file_path
