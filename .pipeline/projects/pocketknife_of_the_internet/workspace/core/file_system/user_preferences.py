"""UserPreferences class for storing and persisting user settings."""

from __future__ import annotations

from typing import Any
from .file_persistence import FilePersistence


_DEFAULT_PREFERENCES = {
    "theme": "light",
    "window_layout": "tiled",
    "pinned_apps": [],
    "taskbar_position": "bottom",
    "taskbar_size": 48,
    "start_menu_position": "left",
    "font_size": 14,
    "accent_color": "#4a90d9",
    "notifications_enabled": True,
    "auto_save": True,
}


class UserPreferences:
    """Manages user preferences with persistence support.

    Stores arbitrary key-value settings and provides a persistent
    storage layer via FilePersistence.

    Attributes:
        preferences: Dictionary of user preferences.
        persistence: FilePersistence instance for saving/loading.
    """

    def __init__(
        self,
        persistence: FilePersistence | None = None,
        file_path: str = "pocketknife_preferences.json",
    ) -> None:
        """Initialize UserPreferences.

        Args:
            persistence: Optional FilePersistence instance.
            file_path: Path for preferences file (if no persistence given).
        """
        self.preferences: dict[str, Any] = dict(_DEFAULT_PREFERENCES)
        if persistence is not None:
            self.persistence = persistence
        else:
            self.persistence = FilePersistence(file_path)
        self._load()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a preference value.

        Args:
            key: Preference key.
            default: Default value if key not found.

        Returns:
            The preference value or default.
        """
        return self.preferences.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a preference value.

        Args:
            key: Preference key.
            value: Value to set.
        """
        self.preferences[key] = value
        self._save()

    def delete(self, key: str) -> bool:
        """Delete a preference.

        Args:
            key: Preference key to delete.

        Returns:
            True if deleted, False if key not found.
        """
        if key in self.preferences:
            del self.preferences[key]
            self._save()
            return True
        return False

    def get_all(self) -> dict[str, Any]:
        """Get all preferences.

        Returns:
            Copy of all preferences.
        """
        return dict(self.preferences)

    def update(self, preferences: dict[str, Any]) -> None:
        """Update multiple preferences at once.

        Args:
            preferences: Dictionary of preferences to update.
        """
        self.preferences.update(preferences)
        self._save()

    def reset(self) -> None:
        """Reset all preferences to defaults."""
        self.preferences = dict(_DEFAULT_PREFERENCES)
        self._save()

    def _load(self) -> None:
        """Load preferences from the persistence file."""
        data = self.persistence.load()
        if data is not None:
            self.preferences.update(data)

    def _save(self) -> None:
        """Save preferences to the persistence file."""
        self.persistence.save(self.preferences)

    def to_dict(self) -> dict[str, Any]:
        """Serialize preferences to a dictionary.

        Returns:
            Dictionary of all preferences.
        """
        return dict(self.preferences)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        persistence: FilePersistence | None = None,
        file_path: str = "pocketknife_preferences.json",
    ) -> "UserPreferences":
        """Create a UserPreferences instance from a dictionary.

        Args:
            data: Dictionary of preferences.
            persistence: Optional FilePersistence instance.
            file_path: Path for preferences file.

        Returns:
            New UserPreferences instance.
        """
        prefs = cls(persistence=persistence, file_path=file_path)
        prefs.preferences = data
        return prefs

    def __repr__(self) -> str:
        return f"UserPreferences(keys={list(self.preferences.keys())})"
