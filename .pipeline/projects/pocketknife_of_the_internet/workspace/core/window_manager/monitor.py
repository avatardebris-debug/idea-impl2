"""Monitor and MonitorManager classes for multi-monitor support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .window import Window


@dataclass
class Monitor:
    """Represents a physical or virtual display.

    Attributes:
        id: Unique identifier for the monitor.
        name: Human-readable display name (e.g. 'Primary', 'Secondary 1').
        x: X coordinate of the monitor's top-left corner in global screen space.
        y: Y coordinate of the monitor's top-left corner in global screen space.
        width: Width of the monitor in pixels.
        height: Height of the monitor in pixels.
        is_primary: Whether this is the primary display.
    """

    id: int
    name: str
    x: int = 0
    y: int = 0
    width: int = 1920
    height: int = 1080
    is_primary: bool = False

    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is within this monitor's bounds.

        Args:
            x: X coordinate to check.
            y: Y coordinate to check.

        Returns:
            True if the point is within the monitor's bounds.
        """
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def contains_window(self, window: Window) -> bool:
        """Check if a window is fully contained within this monitor.

        Args:
            window: Window to check.

        Returns:
            True if the window is fully within the monitor's bounds.
        """
        return (
            self.x <= window.x
            and self.y <= window.y
            and window.x + window.width <= self.x + self.width
            and window.y + window.height <= self.y + self.height
        )

    def intersects_window(self, window: Window) -> bool:
        """Check if a window intersects with this monitor.

        Args:
            window: Window to check.

        Returns:
            True if the window intersects the monitor's bounds.
        """
        return not (
            window.x + window.width <= self.x
            or window.x >= self.x + self.width
            or window.y + window.height <= self.y
            or window.y >= self.y + self.height
        )

    def get_center(self) -> tuple[int, int]:
        """Get the center coordinates of the monitor.

        Returns:
            Tuple of (x, y) center coordinates.
        """
        return (self.x + self.width // 2, self.y + self.height // 2)

    def get_bounds(self) -> tuple[int, int, int, int]:
        """Get the monitor's bounds as (x, y, width, height).

        Returns:
            Tuple of (x, y, width, height).
        """
        return (self.x, self.y, self.width, self.height)

    def __repr__(self) -> str:
        return (
            f"Monitor(id={self.id}, name={self.name!r}, "
            f"bounds=({self.x}, {self.y}, {self.width}x{self.height}), "
            f"primary={self.is_primary})"
        )


class MonitorManager:
    """Manages available monitors and provides monitor-related queries.

    Attributes:
        monitors: List of Monitor instances.
        primary_monitor: The primary monitor instance.
    """

    def __init__(self) -> None:
        """Initialize an empty MonitorManager."""
        self.monitors: list[Monitor] = []
        self.primary_monitor: Monitor | None = None

    def add_monitor(self, monitor: Monitor) -> None:
        """Add a monitor to the manager.

        Args:
            monitor: Monitor instance to add.
        """
        self.monitors.append(monitor)
        if monitor.is_primary:
            self.primary_monitor = monitor

    def remove_monitor(self, monitor_id: int) -> bool:
        """Remove a monitor by ID.

        Args:
            monitor_id: ID of the monitor to remove.

        Returns:
            True if the monitor was removed, False if not found.
        """
        for i, monitor in enumerate(self.monitors):
            if monitor.id == monitor_id:
                self.monitors.pop(i)
                if self.primary_monitor and self.primary_monitor.id == monitor_id:
                    self.primary_monitor = self.monitors[0] if self.monitors else None
                return True
        return False

    def get_monitor_at(self, x: int, y: int) -> Monitor | None:
        """Get the monitor that contains the given point.

        Args:
            x: X coordinate.
            y: Y coordinate.

        Returns:
            Monitor instance or None if no monitor contains the point.
        """
        for monitor in self.monitors:
            if monitor.contains_point(x, y):
                return monitor
        return None

    def get_monitor_for_window(self, window: Window) -> Monitor | None:
        """Get the monitor that contains the majority of a window.

        Args:
            window: Window to check.

        Returns:
            Monitor instance or None if no monitor contains the window.
        """
        # Check for monitors that fully contain the window
        for monitor in self.monitors:
            if monitor.contains_window(window):
                return monitor

        # Check for monitors that intersect the window
        intersecting_monitors: list[Monitor] = []
        for monitor in self.monitors:
            if monitor.intersects_window(window):
                intersecting_monitors.append(monitor)

        if not intersecting_monitors:
            return None

        # Return the monitor with the largest intersection area
        best_monitor = None
        max_area = 0

        for monitor in intersecting_monitors:
            # Calculate intersection area
            x_overlap = min(window.x + window.width, monitor.x + monitor.width) - max(
                window.x, monitor.x
            )
            y_overlap = min(window.y + window.height, monitor.y + monitor.height) - max(
                window.y, monitor.y
            )
            area = x_overlap * y_overlap

            if area > max_area:
                max_area = area
                best_monitor = monitor

        return best_monitor

    def get_primary_monitor(self) -> Monitor:
        """Get the primary monitor.

        Returns:
            Primary Monitor instance.
        """
        if self.primary_monitor:
            return self.primary_monitor
        if self.monitors:
            return self.monitors[0]
        # Fallback to a default monitor
        return Monitor(
            id=0,
            name="Default",
            x=0,
            y=0,
            width=1920,
            height=1080,
            is_primary=True,
        )

    def get_monitors_in_rect(self, x: int, y: int, width: int, height: int) -> list[Monitor]:
        """Get all monitors that intersect with a given rectangle.

        Args:
            x: X coordinate of the rectangle.
            y: Y coordinate of the rectangle.
            width: Width of the rectangle.
            height: Height of the rectangle.

        Returns:
            List of intersecting Monitor instances.
        """
        rect = {"x": x, "y": y, "width": width, "height": height}
        return [m for m in self.monitors if self._rects_intersect(rect, m.get_bounds())]

    @staticmethod
    def _rects_intersect(
        rect1: dict, rect2: tuple[int, int, int, int]
    ) -> bool:
        """Check if two rectangles intersect.

        Args:
            rect1: Dictionary with keys 'x', 'y', 'width', 'height'.
            rect2: Tuple of (x, y, width, height).

        Returns:
            True if the rectangles intersect.
        """
        x1, y1, w1, h1 = rect1["x"], rect1["y"], rect1["width"], rect1["height"]
        x2, y2, w2, h2 = rect2

        return not (
            x1 + w1 <= x2
            or x1 >= x2 + w2
            or y1 + h1 <= y2
            or y1 >= y2 + h2
        )

    def clamp_window_to_monitor(
        self, window: Window, monitor: Monitor | None = None
    ) -> None:
        """Clamp a window's position to fit within a monitor's bounds.

        If the window is larger than the monitor, it will be centered.
        If monitor is None, uses the monitor that contains the window's center.

        Args:
            window: Window to clamp.
            monitor: Monitor to clamp to. If None, uses the monitor containing the window.
        """
        if monitor is None:
            monitor = self.get_monitor_for_window(window) or self.get_primary_monitor()

        # If window is larger than monitor, center it
        if window.width > monitor.width:
            window.x = monitor.x + (monitor.width - window.width) // 2
        elif window.x < monitor.x:
            window.x = monitor.x
        elif window.x + window.width > monitor.x + monitor.width:
            window.x = monitor.x + monitor.width - window.width

        if window.height > monitor.height:
            window.y = monitor.y + (monitor.height - window.height) // 2
        elif window.y < monitor.y:
            window.y = monitor.y
        elif window.y + window.height > monitor.y + monitor.height:
            window.y = monitor.y + monitor.height - window.height

    def to_dict(self) -> dict:
        """Return monitor state as a dictionary.

        Returns:
            Dictionary containing monitor information.
        """
        return {
            "monitors": [
                {
                    "id": m.id,
                    "name": m.name,
                    "x": m.x,
                    "y": m.y,
                    "width": m.width,
                    "height": m.height,
                    "is_primary": m.is_primary,
                }
                for m in self.monitors
            ],
            "primary_monitor_id": self.primary_monitor.id if self.primary_monitor else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MonitorManager:
        """Create a MonitorManager from a dictionary.

        Args:
            data: Dictionary containing monitor information.

        Returns:
            MonitorManager instance.
        """
        manager = cls()
        for monitor_data in data.get("monitors", []):
            monitor = Monitor(
                id=monitor_data["id"],
                name=monitor_data["name"],
                x=monitor_data["x"],
                y=monitor_data["y"],
                width=monitor_data["width"],
                height=monitor_data["height"],
                is_primary=monitor_data["is_primary"],
            )
            manager.add_monitor(monitor)
        return manager

    def __repr__(self) -> str:
        return f"MonitorManager(monitors={len(self.monitors)}, primary={self.primary_monitor.id if self.primary_monitor else None})"
