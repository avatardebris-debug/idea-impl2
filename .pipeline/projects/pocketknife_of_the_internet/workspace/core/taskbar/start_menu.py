"""StartMenu class that provides quick access to bookmarked web applications."""

from __future__ import annotations


_DEFAULT_APPS = [
    {"id": "google", "name": "Google", "url": "https://www.google.com", "icon": "🔍", "category": "search"},
    {"id": "github", "name": "GitHub", "url": "https://github.com", "icon": "🐙", "category": "development"},
    {"id": "youtube", "name": "YouTube", "url": "https://www.youtube.com", "icon": "▶️", "category": "media"},
    {"id": "wikipedia", "name": "Wikipedia", "url": "https://www.wikipedia.org", "icon": "📚", "category": "reference"},
]


class StartMenu:
    """Start menu / app launcher for quick access to bookmarked web apps.

    Properties:
        is_open: Whether the start menu is currently displayed.
        apps: List of app dicts.
        search_query: Current search/filter string.
        selected_category: Currently selected category.
        position: Relative position to the taskbar ('left', 'center', 'right').
    """

    def __init__(
        self,
        apps: list[dict] | None = None,
        position: str = "left",
    ):
        """Initialize the StartMenu.

        Args:
            apps: Optional list of app dicts. Defaults to built-in apps.
            position: Position relative to the taskbar edge.
        """
        self.is_open = False
        self.search_query = ""
        self.selected_category = "all"
        self.position = position
        self._apps: dict[str, dict] = {}
        for app in apps or _DEFAULT_APPS:
            self.add_app(
                app_id=app["id"],
                name=app["name"],
                url=app["url"],
                icon=app.get("icon"),
                category=app.get("category"),
            )

    # ── app management ──

    def add_app(
        self,
        app_id: str,
        name: str,
        url: str,
        icon: str | None = None,
        category: str | None = None,
    ) -> None:
        """Register a bookmarked web app.

        Args:
            app_id: Unique identifier for the app.
            name: Display name.
            url: Launch URL.
            icon: Optional icon string/emoji.
            category: Optional category for grouping.
        """
        self._apps[app_id] = {
            "id": app_id,
            "name": name,
            "url": url,
            "icon": icon or "🌐",
            "category": category,
        }

    def remove_app(self, app_id: str) -> bool:
        """Remove a bookmarked app.

        Args:
            app_id: App to remove.

        Returns:
            True if removed, False if not found.
        """
        if app_id in self._apps:
            del self._apps[app_id]
            return True
        return False

    def get_app(self, app_id: str) -> dict | None:
        """Get an app by ID.

        Args:
            app_id: App ID to look up.

        Returns:
            App dict or None if not found.
        """
        return self._apps.get(app_id)

    # ── menu actions ──

    def toggle(self) -> bool:
        """Open or close the start menu.

        Returns:
            The new is_open state.
        """
        self.is_open = not self.is_open
        return self.is_open

    def search_apps(self, query: str) -> list[dict]:
        """Filter apps by name or category matching the query string.

        Args:
            query: Search string (case-insensitive).

        Returns:
            List of matching app dicts.
        """
        q = query.lower()
        return [
            app
            for app in self._apps.values()
            if q in app["name"].lower() or (app.get("category") and q in app["category"].lower())
        ]

    def get_apps_by_category(self, category: str) -> list[dict]:
        """Get apps by category.

        Args:
            category: Category to filter by.

        Returns:
            List of matching app dicts.
        """
        if category == "all":
            return list(self._apps.values())
        return [
            app
            for app in self._apps.values()
            if app.get("category") == category
        ]

    def open_app(self, app_id: str) -> dict | None:
        """Open an app by ID.

        Args:
            app_id: App to open.

        Returns:
            The app dict, or None if not found.
        """
        app = self._apps.get(app_id)
        return app

    def get_app_list(self) -> list[dict]:
        """Return all apps, optionally filtered by current search_query or selected_category.

        Returns:
            List of app dicts.
        """
        if self.search_query:
            return self.search_apps(self.search_query)
        if self.selected_category and self.selected_category != "all":
            return self.get_apps_by_category(self.selected_category)
        return list(self._apps.values())

    def get_categories(self) -> list[str]:
        """Return a list of unique categories.

        Returns:
            List of category strings.
        """
        categories = {app["category"] for app in self._apps.values() if app.get("category")}
        return sorted(categories)

    @property
    def apps(self) -> list[dict]:
        """Return all apps (read-only view)."""
        return list(self._apps.values())

    def to_dict(self) -> dict:
        """Serialize the StartMenu state.

        Returns:
            Dict with apps, search_query, and selected_category.
        """
        return {
            "apps": list(self._apps.values()),
            "search_query": self.search_query,
            "selected_category": self.selected_category,
        }

    @classmethod
    def from_dict(cls, state: dict) -> "StartMenu":
        """Deserialize a StartMenu from a dict.

        Args:
            state: Dict with apps, search_query, and selected_category.

        Returns:
            New StartMenu instance.
        """
        menu = cls(apps=state.get("apps", []))
        menu.search_query = state.get("search_query", "")
        menu.selected_category = state.get("selected_category", "all")
        return menu

    def __repr__(self) -> str:
        return (
            f"StartMenu(is_open={self.is_open}, apps={len(self._apps)}, "
            f"position={self.position!r})"
        )
