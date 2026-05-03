"""WindowSnapper class for window snapping functionality."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .monitor import Monitor
    from .window import Window
    from .window_manager import WindowManager


@dataclass
class SnapZone:
    """Represents a zone where a window can snap to.

    Attributes:
        zone_type: Type of snap zone (e.g., 'left', 'right', 'center', 'fullscreen').
        bounds: Tuple of (x, y, width, height) representing the snap zone.
        threshold: Distance threshold for triggering the snap.
    """

    zone_type: str
    bounds: tuple[int, int, int, int]
    threshold: int = 20


class WindowSnapper:
    """Handles window snapping functionality.

    Attributes:
        window_manager: Reference to the WindowManager.
        threshold: Distance threshold for triggering snaps (default 20 pixels).
        snap_zones: List of SnapZone instances for the current monitor.
    """

    def __init__(self, window_manager: WindowManager, threshold: int = 20) -> None:
        """Initialize the WindowSnapper.

        Args:
            window_manager: Reference to the WindowManager.
            threshold: Distance threshold for triggering snaps (default 20 pixels).
        """
        self.window_manager = window_manager
        self.threshold = threshold
        self.snap_zones: list[SnapZone] = []

    def update_snap_zones(self, monitor: Monitor | None = None) -> None:
        """Update snap zones based on the current monitor.

        Args:
            monitor: Monitor to calculate snap zones for. If None, uses primary monitor.
        """
        if monitor is None:
            monitor = self.window_manager.monitor_manager.get_primary_monitor()

        self.snap_zones = [
            SnapZone(
                zone_type="left",
                bounds=(monitor.x, monitor.y, monitor.width // 2, monitor.height),
                threshold=self.threshold,
            ),
            SnapZone(
                zone_type="right",
                bounds=(monitor.x + monitor.width // 2, monitor.y, monitor.width // 2, monitor.height),
                threshold=self.threshold,
            ),
            SnapZone(
                zone_type="top",
                bounds=(monitor.x, monitor.y, monitor.width, monitor.height // 2),
                threshold=self.threshold,
            ),
            SnapZone(
                zone_type="bottom",
                bounds=(monitor.x, monitor.y + monitor.height // 2, monitor.width, monitor.height // 2),
                threshold=self.threshold,
            ),
            SnapZone(
                zone_type="fullscreen",
                bounds=(monitor.x, monitor.y, monitor.width, monitor.height),
                threshold=self.threshold,
            ),
        ]

    def get_snap_zone(self, window: Window) -> SnapZone | None:
        """Get the snap zone that a window should snap to.

        Args:
            window: Window to check.

        Returns:
            SnapZone instance or None if no snap zone is applicable.
        """
        # Get the monitor containing the window
        monitor = self.window_manager.monitor_manager.get_monitor_for_window(window)
        if not monitor:
            return None

        # Update snap zones for this monitor
        self.update_snap_zones(monitor)

        # Check each snap zone
        for zone in self.snap_zones:
            if self._is_in_snap_zone(window, zone):
                return zone

        return None

    def _is_in_snap_zone(self, window: Window, zone: SnapZone) -> bool:
        """Check if a window is within the snap threshold of a zone.

        Args:
            window: Window to check.
            zone: SnapZone to check against.

        Returns:
            True if the window is within the snap threshold of the zone.
        """
        # Check if the window's edge is within the threshold of the zone's edge
        zone_x, zone_y, zone_w, zone_h = zone.bounds

        # Left edge of window near left edge of zone
        if abs(window.x - zone_x) <= self.threshold:
            return True

        # Right edge of window near right edge of zone
        if abs((window.x + window.width) - (zone_x + zone_w)) <= self.threshold:
            return True

        # Top edge of window near top edge of zone
        if abs(window.y - zone_y) <= self.threshold:
            return True

        # Bottom edge of window near bottom edge of zone
        if abs((window.y + window.height) - (zone_y + zone_h)) <= self.threshold:
            return True

        return False

    def snap_window(self, window: Window, zone: SnapZone | None = None) -> None:
        """Snap a window to a zone.

        Args:
            window: Window to snap.
            zone: SnapZone to snap to. If None, uses the zone containing the window.
        """
        if zone is None:
            zone = self.get_snap_zone(window)

        if zone is None:
            return

        # Get the monitor for the snap zone
        monitor = self.window_manager.monitor_manager.get_primary_monitor()
        for m in self.window_manager.monitor_manager.monitors:
            if m.contains_point(zone.bounds[0], zone.bounds[1]):
                monitor = m
                break

        # Calculate new position and size based on zone type
        zone_x, zone_y, zone_w, zone_h = zone.bounds

        if zone.zone_type == "fullscreen":
            window.x = monitor.x
            window.y = monitor.y
            window.width = monitor.width
            window.height = monitor.height
        elif zone.zone_type == "left":
            window.x = monitor.x
            window.y = monitor.y
            window.width = monitor.width // 2
            window.height = monitor.height
        elif zone.zone_type == "right":
            window.x = monitor.x + monitor.width // 2
            window.y = monitor.y
            window.width = monitor.width // 2
            window.height = monitor.height
        elif zone.zone_type == "top":
            window.x = monitor.x
            window.y = monitor.y
            window.width = monitor.width
            window.height = monitor.height // 2
        elif zone.zone_type == "bottom":
            window.x = monitor.x
            window.y = monitor.y + monitor.height // 2
            window.width = monitor.width
            window.height = monitor.height // 2

        # Update window's monitor
        window.current_monitor_id = monitor.id

    def get_snap_zones_for_monitor(self, monitor: Monitor) -> list[SnapZone]:
        """Get all snap zones for a specific monitor.

        Args:
            monitor: Monitor to get snap zones for.

        Returns:
            List of SnapZone instances.
        """
        self.update_snap_zones(monitor)
        return self.snap_zones

    def to_dict(self) -> dict:
        """Return snapper state as a dictionary.

        Returns:
            Dictionary containing snapper information.
        """
        return {
            "threshold": self.threshold,
            "snap_zones": [
                {
                    "zone_type": zone.zone_type,
                    "bounds": zone.bounds,
                    "threshold": zone.threshold,
                }
                for zone in self.snap_zones
            ],
        }

    @classmethod
    def from_dict(cls, data: dict, window_manager: WindowManager) -> WindowSnapper:
        """Create a WindowSnapper from a dictionary.

        Args:
            data: Dictionary containing snapper information.
            window_manager: Reference to the WindowManager.

        Returns:
            WindowSnapper instance.
        """
        snapper = cls(window_manager, data.get("threshold", 20))
        for zone_data in data.get("snap_zones", []):
            snapper.snap_zones.append(
                SnapZone(
                    zone_type=zone_data["zone_type"],
                    bounds=tuple(zone_data["bounds"]),
                    threshold=zone_data["threshold"],
                )
            )
        return snapper

    def __repr__(self) -> str:
        return f"WindowSnapper(threshold={self.threshold}, zones={len(self.snap_zones)})"
