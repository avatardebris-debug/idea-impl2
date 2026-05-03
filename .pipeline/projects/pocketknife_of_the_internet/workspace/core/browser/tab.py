"""Tab class that represents a browser tab with navigation history."""


class Tab:
    """Represents a browser tab with navigation history.

    Properties:
        window_id: ID of the window this tab belongs to.
        url: Current URL displayed in the tab.
        history: List of URLs visited in order.
        history_index: Current position in the history.
        is_detached: Whether this tab has been detached into a floating window.
        title: Title of the tab (used when detaching/reattaching).
    """

    def __init__(self, window_id, url, title=None):
        """Initialize a new Tab instance.

        Args:
            window_id: ID of the window this tab belongs to.
            url: Initial URL to display.
            title: Optional title for the tab. Defaults to url if not provided.
        """
        self.window_id = window_id
        self.original_window_id = window_id
        self.url = url
        self.history = [url]
        self.history_index = 0
        self.is_detached = False
        self.title = title or url

    def detach(self):
        """Mark this tab as detached.

        Returns:
            The tab's state as a dict for serialization during detach.
        """
        self.is_detached = True
        return {
            "window_id": self.window_id,
            "original_window_id": self.original_window_id,
            "url": self.url,
            "history": self.history,
            "history_index": self.history_index,
            "title": self.title,
        }

    def reattach(self, state):
        """Re-attach this tab from a detached window state.

        Args:
            state: Dict containing the detached state to restore.
        """
        self.is_detached = False
        self.window_id = state["window_id"]
        self.url = state["url"]
        self.history = state["history"]
        self.history_index = state["history_index"]
        self.title = state["title"]

    def navigate(self, url):
        """Navigate to a new URL, adding it to history.

        Args:
            url: The URL to navigate to.
        """
        # If we're not at the end of history, truncate forward history
        if self.history_index < len(self.history) - 1:
            self.history = self.history[: self.history_index + 1]

        self.history.append(url)
        self.history_index = len(self.history) - 1
        self.url = url

    def go_back(self):
        """Go back to the previous URL in history.

        Returns:
            The previous URL, or None if at the beginning of history.
        """
        if self.history_index > 0:
            self.history_index -= 1
            self.url = self.history[self.history_index]
            return self.url
        return None

    def go_forward(self):
        """Go forward to the next URL in history.

        Returns:
            The next URL, or None if at the end of history.
        """
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.url = self.history[self.history_index]
            return self.url
        return None

    def reload(self):
        """Reload the current URL.

        Returns:
            The current URL.
        """
        return self.url

    def to_dict(self):
        """Return tab state as a dictionary.

        Returns:
            Dictionary containing all tab properties.
        """
        return {
            "window_id": self.window_id,
            "url": self.url,
            "history": self.history,
            "history_index": self.history_index,
            "title": self.title,
            "is_detached": self.is_detached,
        }

    @classmethod
    def from_dict(cls, data):
        """Create a Tab instance from a dictionary.

        Args:
            data: Dictionary containing tab properties.

        Returns:
            A new Tab instance.
        """
        tab = cls(
            window_id=data["window_id"],
            url=data["url"],
            title=data.get("title"),
        )
        tab.history = data.get("history", [data["url"]])
        tab.history_index = data.get("history_index", len(tab.history) - 1)
        tab.is_detached = data.get("is_detached", False)
        return tab

    def __repr__(self):
        return (
            f"Tab(window_id={self.window_id}, url={self.url!r}, "
            f"history_len={len(self.history)}, is_detached={self.is_detached})"
        )
