"""WindowSwitcher class that manages and cycles through open windows."""

from __future__ import annotations


class WindowSwitcher:
    """Manages a list of windows and allows focusing/switching between them.

    Properties:
        is_active: Whether the switcher overlay is currently shown.
        selected_window_id: ID of the currently focused window, or None.
        windows: List of window dicts.
    """

    def __init__(self) -> None:
        """Initialize the WindowSwitcher."""
        self.is_active = False
        self.selected_window_id: int | None = None
        self._windows: dict[int, dict] = {}

    # ── window management ──

    def add_window(
        self,
        window_id: int,
        title: str,
        url: str,
        icon: str | None = None,
    ) -> None:
        """Add a window to the switcher.

        Args:
            window_id: Unique window identifier.
            title: Window title.
            url: Window URL.
            icon: Optional icon string/emoji.
        """
        self._windows[window_id] = {
            "window_id": window_id,
            "title": title,
            "url": url,
            "icon": icon or "🌐",
        }

    def remove_window(self, window_id: int) -> bool:
        """Remove a window from the switcher.

        Args:
            window_id: Window to remove.

        Returns:
            True if removed, False if not found.
        """
        if window_id in self._windows:
            del self._windows[window_id]
            if self.selected_window_id == window_id:
                self.selected_window_id = None
            return True
        return False

    def get_window(self, window_id: int) -> dict | None:
        """Get a window by ID.

        Args:
            window_id: Window ID to look up.

        Returns:
            Window dict or None if not found.
        """
        return self._windows.get(window_id)

    @property
    def windows(self) -> list[dict]:
        """Return all windows (read-only view)."""
        return list(self._windows.values())

    # ── focus ──

    def focus_window(self, window_id: int) -> bool:
        """Focus a window by ID.

        Args:
            window_id: Window to focus.

        Returns:
            True if focused, False if not found.
        """
        if window_id in self._windows:
            self.selected_window_id = window_id
            return True
        return False

    # ── lifecycle ──

    def activate(self) -> None:
        """Start the switcher."""
        self.is_active = True

    def deactivate(self) -> None:
        """End the switcher."""
        self.is_active = False

    # ── serialization ──

    def to_dict(self) -> dict:
        """Serialize the WindowSwitcher state.

        Returns:
            Dict with windows and selected_window_id.
        """
        return {
            "windows": list(self._windows.values()),
            "selected_window_id": self.selected_window_id,
        }

    @classmethod
    def from_dict(cls, state: dict) -> "WindowSwitcher":
        """Deserialize a WindowSwitcher from a dict.

        Args:
            state: Dict with windows and selected_window_id.

        Returns:
            New WindowSwitcher instance.
        """
        switcher = cls()
        switcher._windows = {w["window_id"]: w for w in state.get("windows", [])}
        switcher.selected_window_id = state.get("selected_window_id")
        return switcher

    def __repr__(self) -> str:
        return (
            f"WindowSwitcher(is_active={self.is_active}, "
            f"selected={self.selected_window_id}, windows={len(self._windows)})"
        )
