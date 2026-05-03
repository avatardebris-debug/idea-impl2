"""Core Window class that represents a draggable browser window/tab."""


class Window:
    """Represents a draggable browser window.

    Properties:
        id: Unique identifier for the window.
        title: Window title.
        url: Current URL displayed in the window.
        x: X coordinate of the window's top-left corner.
        y: Y coordinate of the window's top-left corner.
        width: Window width in pixels.
        height: Window height in pixels.
        z_index: Z-order index for stacking windows.
        is_minimized: Whether the window is minimized.
        is_maximized: Whether the window is maximized.
    """

    def __init__(self, id, title, url, x=100, y=100, width=800, height=600):
        """Initialize a new Window instance.

        Args:
            id: Unique identifier for the window.
            title: Title of the window.
            url: URL to display in the window.
            x: X position (default 100).
            y: Y position (default 100).
            width: Window width (default 800).
            height: Window height (default 600).
        """
        self.id = id
        self.title = title
        self.url = url
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.z_index = 1
        self.is_minimized = False
        self.is_maximized = False
        self.current_monitor_id: int | None = None
        # Store original dimensions for restore
        self._original_x = x
        self._original_y = y
        self._original_width = width
        self._original_height = height

    def move(self, x, y):
        """Move window to a new position.

        Args:
            x: New X coordinate.
            y: New Y coordinate.
        """
        self.x = x
        self.y = y

    def resize(self, width, height):
        """Resize the window.

        Args:
            width: New width.
            height: New height.
        """
        self.width = width
        self.height = height

    def set_z_index(self, z_index):
        """Bring window to a specific z-index position.

        Args:
            z_index: The z-index to set.
        """
        self.z_index = z_index

    def minimize(self):
        """Minimize the window."""
        self.is_minimized = True

    def maximize(self):
        """Maximize the window."""
        if not self.is_maximized:
            # Store current state before maximizing
            self._original_x = self.x
            self._original_y = self.y
            self._original_width = self.width
            self._original_height = self.height
        self.is_maximized = True

    def restore(self):
        """Restore window from minimized or maximized state."""
        self.is_minimized = False
        self.is_maximized = False
        # Restore original dimensions if they were stored
        if self._original_width and self._original_height:
            self.width = self._original_width
            self.height = self._original_height
            self.x = self._original_x
            self.y = self._original_y

    def to_dict(self):
        """Return window state as a dictionary.

        Returns:
            Dictionary containing all window properties.
        """
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "z_index": self.z_index,
            "is_minimized": self.is_minimized,
            "is_maximized": self.is_maximized,
            "current_monitor_id": self.current_monitor_id,
        }

    @classmethod
    def from_dict(cls, data):
        """Create a Window instance from a dictionary.

        Args:
            data: Dictionary containing window properties.

        Returns:
            A new Window instance.
        """
        window = cls(
            id=data["id"],
            title=data["title"],
            url=data["url"],
            x=data.get("x", 100),
            y=data.get("y", 100),
            width=data.get("width", 800),
            height=data.get("height", 600),
        )
        window.z_index = data.get("z_index", 1)
        window.is_minimized = data.get("is_minimized", False)
        window.is_maximized = data.get("is_maximized", False)
        window.current_monitor_id = data.get("current_monitor_id")
        # Restore original dimensions if available
        if "x" in data and "y" in data and "width" in data and "height" in data:
            window._original_x = data["x"]
            window._original_y = data["y"]
            window._original_width = data["width"]
            window._original_height = data["height"]
        return window

    def __repr__(self):
        return (
            f"Window(id={self.id}, title={self.title!r}, url={self.url!r}, "
            f"x={self.x}, y={self.y}, width={self.width}, height={self.height}, "
            f"z_index={self.z_index}, minimized={self.is_minimized}, "
            f"maximized={self.is_maximized})"
        )
