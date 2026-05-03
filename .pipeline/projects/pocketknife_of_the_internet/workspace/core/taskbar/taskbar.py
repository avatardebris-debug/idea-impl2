"""Taskbar class that tracks all open windows and displays their current state."""

from __future__ import annotations


class Taskbar:
    """Persistent taskbar that tracks all open windows and displays their current state.

    Properties:
        windows: Dict mapping window_id to tracked window info dicts.
        position: Where the taskbar is positioned (top/bottom/left/right).
        height: Height of the taskbar in pixels.
        is_visible: Whether the taskbar is currently visible.
    """

    def __init__(
        self,
        position: str = "bottom",
        height: int = 48,
        is_visible: bool = True,
    ):
        """Initialize the Taskbar.

        Args:
            position: Position on screen. One of 'top', 'bottom', 'left', 'right'.
            height: Height in pixels.
            is_visible: Whether the taskbar is visible.
        """
        self.position = position
        self.height = height
        self.is_visible = is_visible
        self._windows: dict[int, dict] = {}

    # ── window tracking ──────────────────────────────────────────────

    def add_window(
        self,
        window_id: int,
        title: str,
        url: str,
        state: dict | None = None,
    ) -> None:
        """Register a window for tracking.

        Args:
            window_id: Unique window identifier.
            title: Window title.
            url: Current URL.
            state: Optional dict with keys is_minimized, is_maximized, is_active, z_index.
        """
        self._windows[window_id] = {
            "window_id": window_id,
            "title": title,
            "url": url,
            "is_minimized": False,
            "is_maximized": False,
            "is_active": False,
            "z_index": 1,
        }
        if state:
            self.update_window_state(window_id, state)

    def remove_window(self, window_id: int) -> bool:
        """Unregister a window.

        Args:
            window_id: Window to remove.

        Returns:
            True if the window was removed, False if it wasn't tracked.
        """
        if window_id in self._windows:
            del self._windows[window_id]
            return True
        return False

    def update_window_state(
        self,
        window_id: int,
        state_updates: dict,
    ) -> None:
        """Update the tracked state of a window.

        Args:
            window_id: Window to update.
            state_updates: Dict of keys to update (e.g. {'is_minimized': True}).
        """
        if window_id not in self._windows:
            return
        for key, value in state_updates.items():
            if key in self._windows[window_id]:
                self._windows[window_id][key] = value

    # ── queries ──────────────────────────────────────────────────────

    def get_window_list(self) -> list[dict]:
        """Return a list of dicts for every tracked window.

        Each dict contains: window_id, title, url, is_minimized, is_maximized, is_active.
        """
        return [
            {
                "window_id": info["window_id"],
                "title": info["title"],
                "url": info["url"],
                "is_minimized": info["is_minimized"],
                "is_maximized": info["is_maximized"],
                "is_active": info["is_active"],
            }
            for info in self._windows.values()
        ]

    def get_active_window(self) -> dict | None:
        """Return the currently active window's info dict, or None."""
        for info in self._windows.values():
            if info.get("is_active"):
                return info
        return None

    def render_preview(self, window_id: int) -> dict | None:
        """Return preview data for a tracked window.

        Returns:
            Dict with title, url, is_minimized, is_maximized, is_active, z_index
            or None if the window is not tracked.
        """
        info = self._windows.get(window_id)
        if info is None:
            return None
        return {
            "title": info["title"],
            "url": info["url"],
            "is_minimized": info["is_minimized"],
            "is_maximized": info["is_maximized"],
            "is_active": info["is_active"],
            "z_index": info["z_index"],
        }

    # ── helpers ──────────────────────────────────────────────────────

    @property
    def windows(self) -> dict[int, dict]:
        """Return the internal tracking dict (read-only view)."""
        return dict(self._windows)

    def __repr__(self) -> str:
        return (
            f"Taskbar(position={self.position!r}, height={self.height}, "
            f"visible={self.is_visible}, windows={len(self._windows)})"
        )
