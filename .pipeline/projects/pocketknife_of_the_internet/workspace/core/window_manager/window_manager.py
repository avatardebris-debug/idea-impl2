"""Window Manager that handles multiple windows, z-index ordering, and window lifecycle."""

from __future__ import annotations

from .monitor import Monitor, MonitorManager
from .window import Window


class WindowManager:
    """Manages multiple browser windows, z-index ordering, and window lifecycle.

    Properties:
        windows: Dictionary mapping window IDs to Window instances.
        next_window_id: Counter for generating unique window IDs.
        active_window_id: ID of the currently active window.
        monitor_manager: MonitorManager instance for multi-monitor support.
    """

    def __init__(self) -> None:
        """Initialize an empty WindowManager."""
        self.windows: dict[int, Window] = {}
        self.next_window_id: int = 1
        self.active_window_id: int | None = None
        self.monitor_manager = MonitorManager()
        # Add a default monitor
        self.monitor_manager.add_monitor(
            Monitor(
                id=0,
                name="Primary",
                x=0,
                y=0,
                width=1920,
                height=1080,
                is_primary=True,
            )
        )

    def add_monitor(self, monitor: Monitor) -> None:
        """Add a monitor to the window manager's monitor manager.

        Args:
            monitor: Monitor instance to add.
        """
        self.monitor_manager.add_monitor(monitor)

    def remove_monitor(self, monitor_id: int) -> bool:
        """Remove a monitor from the window manager's monitor manager.

        Args:
            monitor_id: ID of the monitor to remove.

        Returns:
            True if the monitor was removed, False if not found.
        """
        return self.monitor_manager.remove_monitor(monitor_id)

    def create_window(
        self,
        title: str,
        url: str,
        x: int = 100,
        y: int = 100,
        width: int = 800,
        height: int = 600,
        monitor_id: int | None = None,
    ) -> Window:
        """Create a new window.

        Args:
            title: Window title.
            url: URL to display.
            x: X position (default 100).
            y: Y position (default 100).
            width: Window width (default 800).
            height: Window height (default 600).
            monitor_id: Optional monitor ID to place the window on.

        Returns:
            The newly created Window instance.
        """
        window_id = self.next_window_id
        self.next_window_id += 1

        # Calculate z_index: one more than the current max
        max_z = max((w.z_index for w in self.windows.values()), default=0)
        z_index = max_z + 1

        # Determine the monitor for positioning
        monitor = self.monitor_manager.get_primary_monitor()
        if monitor_id is not None:
            for m in self.monitor_manager.monitors:
                if m.id == monitor_id:
                    monitor = m
                    break

        # If no monitor_id given, check if x,y is on a monitor
        if monitor_id is None:
            placed_monitor = self.monitor_manager.get_monitor_at(x, y)
            if placed_monitor:
                monitor = placed_monitor
            # Clamp position to monitor bounds
            self.monitor_manager.clamp_window_to_monitor(
                Window(id=0, title="", url="", x=x, y=y, width=width, height=height),
                monitor,
            )
            # Use clamped position
            x = max(x, monitor.x)
            y = max(y, monitor.y)

        window = Window(
            id=window_id,
            title=title,
            url=url,
            x=x,
            y=y,
            width=width,
            height=height,
        )
        window.set_z_index(z_index)
        window.current_monitor_id = monitor.id

        self.windows[window_id] = window
        self.active_window_id = window_id
        return window

    def close_window(self, window_id: int) -> bool:
        """Close and remove a window.

        Args:
            window_id: ID of the window to close.

        Returns:
            True if the window was closed, False if it didn't exist.
        """
        if window_id not in self.windows:
            return False

        del self.windows[window_id]

        # If the closed window was active, set a new active window
        if self.active_window_id == window_id:
            if self.windows:
                self.active_window_id = max(
                    self.windows.keys(),
                    key=lambda wid: self.windows[wid].z_index,
                )
            else:
                self.active_window_id = None

        return True

    def get_window(self, window_id: int) -> Window | None:
        """Get a window by ID.

        Args:
            window_id: ID of the window to retrieve.

        Returns:
            Window instance or None if not found.
        """
        return self.windows.get(window_id)

    def focus_window(self, window_id: int) -> bool:
        """Bring a window to the front and set it as active.

        Args:
            window_id: ID of the window to focus.

        Returns:
            True if the window was focused, False if it didn't exist.
        """
        if window_id not in self.windows:
            return False

        # Bring to front by giving it the highest z_index
        max_z = max((w.z_index for w in self.windows.values()), default=0)
        self.windows[window_id].set_z_index(max_z + 1)
        self.active_window_id = window_id
        return True

    def get_active_window(self) -> Window | None:
        """Get the currently active window.

        Returns:
            The active Window instance or None.
        """
        if self.active_window_id is None:
            return None
        return self.windows.get(self.active_window_id)

    def arrange_windows(self) -> None:
        """Arrange all windows in a cascade layout to prevent overlap.

        Windows are positioned diagonally with a fixed offset so that
        each window is partially visible.
        """
        if not self.windows:
            return

        cascade_offset = 800
        num_windows = len(self.windows)

        for i, (window_id, window) in enumerate(self.windows.items()):
            # Skip minimized windows
            if window.is_minimized:
                continue

            # Position in a cascade pattern
            x = 50 + (i * cascade_offset)
            y = 50 + (i * cascade_offset)

            window.move(x, y)

    def clamp_active_window_to_monitor(self) -> None:
        """Clamp the active window to its current monitor bounds."""
        active = self.get_active_window()
        if active and active.current_monitor_id is not None:
            monitor = self.monitor_manager.get_monitor_at(active.x, active.y)
            if monitor:
                self.monitor_manager.clamp_window_to_monitor(active, monitor)

    def to_dict(self) -> dict:
        """Return all windows as a dictionary.

        Returns:
            Dictionary mapping window IDs to their state dictionaries.
        """
        return {wid: win.to_dict() for wid, win in self.windows.items()}

    def __repr__(self) -> str:
        return f"WindowManager(windows={len(self.windows)}, active={self.active_window_id})"
