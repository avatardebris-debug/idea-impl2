"""Core browser engine that manages tabs/windows and provides basic navigation."""

from core.window_manager.window_manager import WindowManager
from core.browser.tab import Tab


class BrowserEngine:
    """Core browser engine that manages tabs and windows."""

    def __init__(self):
        """Initialize the browser engine."""
        self.window_manager = WindowManager()
        self.tab_registry = {}

    def create_tab(self, title: str, url: str, x: int = 100, y: int = 100, width: int = 800, height: int = 600) -> int:
        """Create a new tab/window.

        Args:
            title: Window title
            url: Initial URL
            x: Window x position
            y: Window y position
            width: Window width
            height: Window height

        Returns:
            Window ID
        """
        window = self.window_manager.create_window(title, url, x, y, width, height)
        tab = Tab(window.id, url, title=title)
        self.tab_registry[window.id] = tab
        return window.id

    def close_tab(self, window_id: int) -> bool:
        """Close a tab/window.

        Args:
            window_id: Window ID to close

        Returns:
            True if closed successfully
        """
        if window_id in self.tab_registry:
            del self.tab_registry[window_id]
        return self.window_manager.close_window(window_id)

    def navigate(self, window_id: int, url: str) -> bool:
        """Navigate a window to a URL.

        Args:
            window_id: Window ID
            url: URL to navigate to

        Returns:
            True if navigation successful
        """
        if window_id not in self.tab_registry:
            return False
        tab = self.tab_registry[window_id]
        tab.navigate(url)
        self.window_manager.windows[window_id].url = url
        return True

    def go_back(self, window_id: int) -> str | None:
        """Go back in history.

        Args:
            window_id: Window ID

        Returns:
            Previous URL or None
        """
        if window_id not in self.tab_registry:
            return None
        tab = self.tab_registry[window_id]
        prev_url = tab.go_back()
        if prev_url:
            self.window_manager.windows[window_id].url = prev_url
        return prev_url

    def go_forward(self, window_id: int) -> str | None:
        """Go forward in history.

        Args:
            window_id: Window ID

        Returns:
            Next URL or None
        """
        if window_id not in self.tab_registry:
            return None
        tab = self.tab_registry[window_id]
        next_url = tab.go_forward()
        if next_url:
            self.window_manager.windows[window_id].url = next_url
        return next_url

    def reload(self, window_id: int) -> str | None:
        """Reload current page.

        Args:
            window_id: Window ID

        Returns:
            Current URL or None
        """
        if window_id not in self.tab_registry:
            return None
        tab = self.tab_registry[window_id]
        return tab.reload()

    def get_tab(self, window_id: int) -> dict | None:
        """Get tab state.

        Args:
            window_id: Window ID

        Returns:
            Tab state dictionary or None
        """
        if window_id not in self.tab_registry:
            return None
        return self.tab_registry[window_id].to_dict()

    def get_active_window_id(self) -> int | None:
        """Get the active window ID.

        Returns:
            Active window ID or None
        """
        return self.window_manager.active_window_id

    def focus_window(self, window_id: int) -> bool:
        """Focus a window (bring to front).

        Args:
            window_id: Window ID to focus

        Returns:
            True if window exists
        """
        if window_id in self.window_manager.windows:
            self.window_manager.focus_window(window_id)
            return True
        return False

    def arrange_windows(self) -> None:
        """Arrange all windows in a cascade layout."""
        self.window_manager.arrange_windows()

    def detach_tab_to_window(self, window_id: int) -> dict | None:
        """Detach a tab/window into a floating window.

        Creates a new detached floating window from an existing tab, preserving
        its URL, history, title, and state. The original tab is removed from
        the tab registry but its state is preserved in the detached window.

        Args:
            window_id: The window ID to detach.

        Returns:
            A dict containing the new detached window ID and transition metadata,
            or None if the window_id doesn't exist in the tab registry.
        """
        if window_id not in self.tab_registry:
            return None

        tab = self.tab_registry[window_id]
        if tab.is_detached:
            return None

        # Save the tab's state before detaching
        tab_state = tab.detach()

        # Get the original window's position for transition metadata
        original_window = self.window_manager.windows.get(window_id)
        start_x = original_window.x if original_window else 0
        start_y = original_window.y if original_window else 0

        # Create a new detached window with an offset
        offset_x = 20
        offset_y = 20
        new_window = self.window_manager.create_window(
            title=tab_state["title"],
            url=tab_state["url"],
            x=start_x + offset_x,
            y=start_y + offset_y,
            width=original_window.width if original_window else 800,
            height=original_window.height if original_window else 600,
        )

        # Create a new tab for the detached window with the preserved state
        detached_tab = Tab.from_dict(tab_state)
        detached_tab.window_id = new_window.id
        detached_tab.is_detached = True
        self.tab_registry[new_window.id] = detached_tab

        # Remove the original tab from the registry
        del self.tab_registry[window_id]

        # Remove the original window from the window manager
        # (the tab content is now in the new floating window)
        self.window_manager.close_window(window_id)

        # Return transition metadata for frontend animation
        return {
            "detached_window_id": new_window.id,
            "transition": {
                "start_x": start_x,
                "start_y": start_y,
                "end_x": new_window.x,
                "end_y": new_window.y,
                "duration_ms": 300,
                "easing_type": "ease-out",
            },
        }

    def reattach_window_to_tab(self, window_id: int) -> dict | None:
        """Re-attach a detached floating window back into a tab.

        Converts a detached floating window back into a tab in the tab bar,
        preserving its URL, history, title, and all state. The window is
        removed from the window manager and the tab is added to the tab registry.

        Args:
            window_id: The detached window ID to reattach.

        Returns:
            A dict containing the new tab's window ID and transition metadata,
            or None if the window_id doesn't exist or isn't detached.
        """
        if window_id not in self.tab_registry:
            return None

        tab = self.tab_registry[window_id]
        if not tab.is_detached:
            return None

        # Save the detached tab's state
        detached_state = {
            "window_id": tab.window_id,
            "url": tab.url,
            "history": tab.history,
            "history_index": tab.history_index,
            "title": tab.title,
        }

        # Get the detached window's position for transition metadata
        detached_window = self.window_manager.windows.get(window_id)
        start_x = detached_window.x if detached_window else 0
        start_y = detached_window.y if detached_window else 0

        # The original window ID (where the tab should be restored)
        original_window_id = tab.window_id

        # Create a new tab in the tab bar, restoring it to the original window slot
        new_tab = Tab.from_dict(detached_state)
        new_tab.is_detached = False
        self.tab_registry[original_window_id] = new_tab

        # Remove the detached window from the window manager
        self.window_manager.close_window(window_id)

        # Return transition metadata for frontend animation
        return {
            "reattached_window_id": original_window_id,
            "transition": {
                "start_x": start_x,
                "start_y": start_y,
                "end_x": start_x,  # In a real implementation, this would be the tab bar position
                "end_y": start_y,
                "duration_ms": 300,
                "easing_type": "ease-in",
            },
        }

    def to_dict(self) -> dict:
        """Get browser state as dictionary.

        Returns:
            Browser state dictionary
        """
        return {
            "windows": self.window_manager.to_dict(),
            "tabs": {wid: tab.to_dict() for wid, tab in self.tab_registry.items()},
        }
