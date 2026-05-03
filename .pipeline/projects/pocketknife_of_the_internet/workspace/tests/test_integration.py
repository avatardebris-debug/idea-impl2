"""Integration tests for the Pocketknife Browser Engine."""

import unittest
import sys
import os

# Add workspace to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.window_manager.window import Window
from core.window_manager.window_manager import WindowManager
from core.browser.browser_engine import BrowserEngine
from core.browser.tab import Tab
from core.browser.html_renderer import HtmlRenderer
from core.taskbar.start_menu import StartMenu
from core.taskbar.window_switcher import WindowSwitcher
from core.taskbar.system_tray import SystemTray


class TestWindow(unittest.TestCase):
    """Tests for the Window class."""

    def test_window_creation(self):
        """Test that a window is created with correct defaults."""
        window = Window(id=1, title="Test", url="https://example.com")
        self.assertEqual(window.id, 1)
        self.assertEqual(window.title, "Test")
        self.assertEqual(window.url, "https://example.com")
        self.assertEqual(window.x, 100)
        self.assertEqual(window.y, 100)
        self.assertEqual(window.width, 800)
        self.assertEqual(window.height, 600)
        self.assertEqual(window.z_index, 1)
        self.assertFalse(window.is_minimized)
        self.assertFalse(window.is_maximized)

    def test_window_move(self):
        """Test that a window can be moved."""
        window = Window(id=1, title="Test", url="https://example.com")
        window.move(200, 300)
        self.assertEqual(window.x, 200)
        self.assertEqual(window.y, 300)

    def test_window_resize(self):
        """Test that a window can be resized."""
        window = Window(id=1, title="Test", url="https://example.com")
        window.resize(1024, 768)
        self.assertEqual(window.width, 1024)
        self.assertEqual(window.height, 768)

    def test_window_minimize_maximize(self):
        """Test window minimize and maximize states."""
        window = Window(id=1, title="Test", url="https://example.com")
        self.assertFalse(window.is_minimized)
        self.assertFalse(window.is_maximized)

        window.minimize()
        self.assertTrue(window.is_minimized)
        self.assertFalse(window.is_maximized)

        window.restore()
        self.assertFalse(window.is_minimized)
        self.assertFalse(window.is_maximized)

        window.maximize()
        self.assertFalse(window.is_minimized)
        self.assertTrue(window.is_maximized)

        window.restore()
        self.assertFalse(window.is_minimized)
        self.assertFalse(window.is_maximized)

    def test_window_to_dict(self):
        """Test that window state can be serialized."""
        window = Window(id=1, title="Test", url="https://example.com")
        window.move(200, 300)
        window.resize(1024, 768)
        window.minimize()

        state = window.to_dict()
        self.assertEqual(state["id"], 1)
        self.assertEqual(state["title"], "Test")
        self.assertEqual(state["url"], "https://example.com")
        self.assertEqual(state["x"], 200)
        self.assertEqual(state["y"], 300)
        self.assertEqual(state["width"], 1024)
        self.assertEqual(state["height"], 768)
        self.assertEqual(state["z_index"], 1)
        self.assertTrue(state["is_minimized"])
        self.assertFalse(state["is_maximized"])

    def test_window_from_dict(self):
        """Test that window state can be deserialized."""
        state = {
            "id": 2,
            "title": "Restored",
            "url": "https://restored.com",
            "x": 50,
            "y": 50,
            "width": 640,
            "height": 480,
            "z_index": 5,
            "is_minimized": True,
            "is_maximized": False,
        }
        window = Window.from_dict(state)
        self.assertEqual(window.id, 2)
        self.assertEqual(window.title, "Restored")
        self.assertEqual(window.url, "https://restored.com")
        self.assertEqual(window.x, 50)
        self.assertEqual(window.y, 50)
        self.assertEqual(window.width, 640)
        self.assertEqual(window.height, 480)
        self.assertEqual(window.z_index, 5)
        self.assertTrue(window.is_minimized)
        self.assertFalse(window.is_maximized)


class TestWindowManager(unittest.TestCase):
    """Tests for the WindowManager class."""

    def setUp(self):
        """Set up a fresh WindowManager for each test."""
        self.wm = WindowManager()

    def test_create_and_close_window(self):
        """Test creating and closing a window."""
        window = self.wm.create_window("Test", "https://example.com")
        self.assertIsNotNone(window)
        self.assertEqual(len(self.wm.windows), 1)
        self.assertEqual(self.wm.active_window_id, window.id)

        closed = self.wm.close_window(window.id)
        self.assertTrue(closed)
        self.assertEqual(len(self.wm.windows), 0)
        self.assertIsNone(self.wm.active_window_id)

    def test_window_focus_ordering(self):
        """Test that focusing a window updates z-index."""
        w1 = self.wm.create_window("Win1", "https://1.com")
        w2 = self.wm.create_window("Win2", "https://2.com")
        w3 = self.wm.create_window("Win3", "https://3.com")

        # Initially, z-indices should be 1, 2, 3
        self.assertEqual(w1.z_index, 1)
        self.assertEqual(w2.z_index, 2)
        self.assertEqual(w3.z_index, 3)

        # Focus w1, it should get highest z-index
        self.wm.focus_window(w1.id)
        self.assertEqual(self.wm.active_window_id, w1.id)
        self.assertEqual(w1.z_index, 4)  # next available
        self.assertEqual(w2.z_index, 2)
        self.assertEqual(w3.z_index, 3)

    def test_window_arrangement(self):
        """Test that window arrangement prevents overlap."""
        w1 = self.wm.create_window("Win1", "https://1.com")
        w2 = self.wm.create_window("Win2", "https://2.com")
        w3 = self.wm.create_window("Win3", "https://3.com")

        self.wm.arrange_windows()

        # Check that windows don't overlap
        windows = list(self.wm.windows.values())
        for i, w1 in enumerate(windows):
            for j, w2 in enumerate(windows):
                if i >= j:
                    continue
                # Check for overlap
                if (
                    w1.x < w2.x + w2.width
                    and w1.x + w1.width > w2.x
                    and w1.y < w2.y + w2.height
                    and w1.y + w1.height > w2.y
                ):
                    self.fail(f"Windows {w1.id} and {w2.id} overlap after arrangement")

    def test_minimize_maximize(self):
        """Test window minimize and maximize via WindowManager."""
        window = self.wm.create_window("Test", "https://example.com")
        self.assertFalse(window.is_minimized)
        self.assertFalse(window.is_maximized)

        window.minimize()
        self.assertTrue(window.is_minimized)

        window.maximize()
        self.assertTrue(window.is_maximized)

        window.restore()
        self.assertFalse(window.is_minimized)
        self.assertFalse(window.is_maximized)


class TestTab(unittest.TestCase):
    """Tests for the Tab class."""

    def test_tab_creation(self):
        """Test that a tab is created with correct defaults."""
        tab = Tab(window_id=1, url="https://example.com")
        self.assertEqual(tab.window_id, 1)
        self.assertEqual(tab.url, "https://example.com")
        self.assertEqual(tab.history, ["https://example.com"])
        self.assertEqual(tab.history_index, 0)

    def test_tab_navigate(self):
        """Test that navigating updates URL and history."""
        tab = Tab(window_id=1, url="https://example.com")
        tab.navigate("https://google.com")
        self.assertEqual(tab.url, "https://google.com")
        self.assertEqual(len(tab.history), 2)
        self.assertEqual(tab.history_index, 1)

    def test_tab_history_navigation(self):
        """Test back and forward navigation."""
        tab = Tab(window_id=1, url="https://example.com")
        tab.navigate("https://google.com")
        tab.navigate("https://wikipedia.org")

        # Go back
        prev = tab.go_back()
        self.assertEqual(prev, "https://google.com")
        self.assertEqual(tab.url, "https://google.com")
        self.assertEqual(tab.history_index, 1)

        # Go forward
        next_url = tab.go_forward()
        self.assertEqual(next_url, "https://wikipedia.org")
        self.assertEqual(tab.url, "https://wikipedia.org")
        self.assertEqual(tab.history_index, 2)

        # Go back twice
        tab.go_back()
        tab.go_back()
        self.assertEqual(tab.url, "https://example.com")
        self.assertEqual(tab.history_index, 0)

        # Can't go back further
        self.assertIsNone(tab.go_back())

        # Can go forward again
        tab.go_forward()
        self.assertEqual(tab.url, "https://google.com")
        tab.go_forward()
        self.assertEqual(tab.url, "https://wikipedia.org")

    def test_tab_reload(self):
        """Test that reload returns current URL."""
        tab = Tab(window_id=1, url="https://example.com")
        self.assertEqual(tab.reload(), "https://example.com")

    def test_tab_to_dict(self):
        """Test that tab state can be serialized."""
        tab = Tab(window_id=1, url="https://example.com")
        tab.navigate("https://google.com")
        state = tab.to_dict()
        self.assertEqual(state["window_id"], 1)
        self.assertEqual(state["url"], "https://google.com")
        self.assertEqual(len(state["history"]), 2)
        self.assertEqual(state["history_index"], 1)

    def test_tab_from_dict(self):
        """Test that tab state can be deserialized."""
        state = {
            "window_id": 2,
            "url": "https://restored.com",
            "history": ["https://start.com", "https://restored.com"],
            "history_index": 1,
        }
        tab = Tab.from_dict(state)
        self.assertEqual(tab.window_id, 2)
        self.assertEqual(tab.url, "https://restored.com")
        self.assertEqual(len(tab.history), 2)
        self.assertEqual(tab.history_index, 1)


class TestBrowserEngine(unittest.TestCase):
    """Tests for the BrowserEngine class."""

    def setUp(self):
        """Set up a fresh BrowserEngine for each test."""
        self.engine = BrowserEngine()

    def test_create_and_navigate_tab(self):
        """Test creating a tab and navigating."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        self.assertIsNotNone(window_id)
        self.assertEqual(len(self.engine.tab_registry), 1)

        result = self.engine.navigate(window_id, "https://google.com")
        self.assertTrue(result)
        tab = self.engine.get_tab(window_id)
        self.assertEqual(tab["url"], "https://google.com")

    def test_history_navigation(self):
        """Test history navigation via BrowserEngine."""
        window_id = self.engine.create_tab("Test", "https://example.com")

        self.engine.navigate(window_id, "https://google.com")
        self.engine.navigate(window_id, "https://wikipedia.org")

        prev = self.engine.go_back(window_id)
        self.assertEqual(prev, "https://google.com")

        next_url = self.engine.go_forward(window_id)
        self.assertEqual(next_url, "https://wikipedia.org")

    def test_tab_lifecycle(self):
        """Test creating and closing a tab."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        self.assertIsNotNone(window_id)
        self.assertIn(window_id, self.engine.tab_registry)

        closed = self.engine.close_tab(window_id)
        self.assertTrue(closed)
        self.assertNotIn(window_id, self.engine.tab_registry)
        self.assertIsNone(self.engine.get_tab(window_id))

    def test_active_window(self):
        """Test getting the active window."""
        w1 = self.engine.create_tab("Win1", "https://1.com")
        w2 = self.engine.create_tab("Win2", "https://2.com")

        self.assertEqual(self.engine.get_active_window_id(), w2)

        self.engine.focus_window(w1)
        self.assertEqual(self.engine.get_active_window_id(), w1)

    def test_arrange_windows(self):
        """Test arranging windows."""
        w1 = self.engine.create_tab("Win1", "https://1.com")
        w2 = self.engine.create_tab("Win2", "https://2.com")
        w3 = self.engine.create_tab("Win3", "https://3.com")

        self.engine.arrange_windows()

        # Check no overlaps
        windows = list(self.engine.window_manager.windows.values())
        for i, w1 in enumerate(windows):
            for j, w2 in enumerate(windows):
                if i >= j:
                    continue
                if (
                    w1.x < w2.x + w2.width
                    and w1.x + w1.width > w2.x
                    and w1.y < w2.y + w2.height
                    and w1.y + w1.height > w2.y
                ):
                    self.fail(f"Windows {w1.id} and {w2.id} overlap after arrangement")


class TestHtmlRenderer(unittest.TestCase):
    """Tests for the HtmlRenderer class."""

    def test_render_basic_html(self):
        """Test rendering basic HTML."""
        renderer = HtmlRenderer()
        html = "<h1>Title</h1><p>Paragraph</p>"
        result = renderer.render(html)
        self.assertIn("<h1", result)
        self.assertIn("Title", result)
        self.assertIn("<p", result)
        self.assertIn("Paragraph", result)

    def test_render_url_placeholder(self):
        """Test that render_url returns placeholder."""
        renderer = HtmlRenderer()
        result = renderer.render_url("https://example.com")
        self.assertIn("https://example.com", result)
        self.assertIn("placeholder", result)

    def test_get_content(self):
        """Test getting rendered content."""
        renderer = HtmlRenderer()
        renderer.render("<p>Test</p>")
        self.assertEqual(renderer.get_content(), "<p>Test</p>")


if __name__ == "__main__":
    unittest.main()


class TestTabDetachReattach(unittest.TestCase):
    """Tests for tab detach and reattach functionality (Phase 2)."""

    def setUp(self):
        """Set up a fresh BrowserEngine for each test."""
        self.engine = BrowserEngine()

    def test_detach_tab_creates_floating_window(self):
        """Test that detaching a tab creates a new floating window."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        self.engine.navigate(window_id, "https://google.com")

        result = self.engine.detach_tab_to_window(window_id)

        self.assertIsNotNone(result)
        self.assertIn("detached_window_id", result)
        self.assertIn("transition", result)

        # Original tab should be removed from registry
        self.assertNotIn(window_id, self.engine.tab_registry)

        # New window should be in registry
        detached_id = result["detached_window_id"]
        self.assertIn(detached_id, self.engine.tab_registry)

        # New tab should be marked as detached
        detached_tab = self.engine.tab_registry[detached_id]
        self.assertTrue(detached_tab.is_detached)

    def test_detach_preserves_url_and_history(self):
        """Test that detaching preserves URL and history."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        self.engine.navigate(window_id, "https://google.com")
        self.engine.navigate(window_id, "https://wikipedia.org")

        result = self.engine.detach_tab_to_window(window_id)
        detached_id = result["detached_window_id"]
        detached_tab = self.engine.tab_registry[detached_id]

        self.assertEqual(detached_tab.url, "https://wikipedia.org")
        self.assertEqual(len(detached_tab.history), 3)
        self.assertEqual(detached_tab.history_index, 2)

    def test_detach_preserves_title(self):
        """Test that detaching preserves the tab title."""
        window_id = self.engine.create_tab("My Page", "https://example.com")
        self.engine.navigate(window_id, "https://google.com")

        result = self.engine.detach_tab_to_window(window_id)
        detached_id = result["detached_window_id"]
        detached_tab = self.engine.tab_registry[detached_id]

        self.assertEqual(detached_tab.title, "My Page")

    def test_detach_returns_transition_metadata(self):
        """Test that detach returns transition metadata for animation."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        result = self.engine.detach_tab_to_window(window_id)

        transition = result["transition"]
        self.assertIn("start_x", transition)
        self.assertIn("start_y", transition)
        self.assertIn("end_x", transition)
        self.assertIn("end_y", transition)
        self.assertIn("duration_ms", transition)
        self.assertIn("easing_type", transition)

        # Transition should show movement (offset)
        self.assertNotEqual(transition["start_x"], transition["end_x"])
        self.assertNotEqual(transition["start_y"], transition["end_y"])

    def test_detach_nonexistent_window(self):
        """Test that detaching a nonexistent window returns None."""
        result = self.engine.detach_tab_to_window(999)
        self.assertIsNone(result)

    def test_detach_already_detached_tab(self):
        """Test that detaching an already detached tab returns None."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        self.engine.detach_tab_to_window(window_id)

        # Try to detach again (should return None since original is gone)
        result = self.engine.detach_tab_to_window(window_id)
        self.assertIsNone(result)

    def test_reattach_window_restores_tab(self):
        """Test that reattaching a window restores the tab."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        self.engine.navigate(window_id, "https://google.com")

        detach_result = self.engine.detach_tab_to_window(window_id)
        detached_id = detach_result["detached_window_id"]

        # Reattach the detached window
        reattach_result = self.engine.reattach_window_to_tab(detached_id)

        self.assertIsNotNone(reattach_result)
        self.assertIn("reattached_window_id", reattach_result)
        self.assertIn("transition", reattach_result)

        # Window should be back in registry
        self.assertIn(detached_id, self.engine.tab_registry)

        # Tab should no longer be detached
        reattached_tab = self.engine.tab_registry[detached_id]
        self.assertFalse(reattached_tab.is_detached)

    def test_reattach_preserves_url_and_history(self):
        """Test that reattaching preserves URL and history."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        self.engine.navigate(window_id, "https://google.com")
        self.engine.navigate(window_id, "https://wikipedia.org")

        detach_result = self.engine.detach_tab_to_window(window_id)
        detached_id = detach_result["detached_window_id"]

        reattach_result = self.engine.reattach_window_to_tab(detached_id)
        reattached_tab = self.engine.tab_registry[detached_id]

        self.assertEqual(reattached_tab.url, "https://wikipedia.org")
        self.assertEqual(len(reattached_tab.history), 3)
        self.assertEqual(reattached_tab.history_index, 2)

    def test_reattach_preserves_title(self):
        """Test that reattaching preserves the tab title."""
        window_id = self.engine.create_tab("My Page", "https://example.com")
        self.engine.navigate(window_id, "https://google.com")

        detach_result = self.engine.detach_tab_to_window(window_id)
        detached_id = detach_result["detached_window_id"]

        reattach_result = self.engine.reattach_window_to_tab(detached_id)
        reattached_tab = self.engine.tab_registry[detached_id]

        self.assertEqual(reattached_tab.title, "My Page")

    def test_reattach_returns_transition_metadata(self):
        """Test that reattach returns transition metadata for animation."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        detach_result = self.engine.detach_tab_to_window(window_id)
        detached_id = detach_result["detached_window_id"]

        reattach_result = self.engine.reattach_window_to_tab(detached_id)
        transition = reattach_result["transition"]

        self.assertIn("start_x", transition)
        self.assertIn("start_y", transition)
        self.assertIn("end_x", transition)
        self.assertIn("end_y", transition)
        self.assertIn("duration_ms", transition)
        self.assertIn("easing_type", transition)

    def test_reattach_nonexistent_window(self):
        """Test that reattaching a nonexistent window returns None."""
        result = self.engine.reattach_window_to_tab(999)
        self.assertIsNone(result)

    def test_reattach_non_detached_window(self):
        """Test that reattaching a non-detached window returns None."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        result = self.engine.reattach_window_to_tab(window_id)
        self.assertIsNone(result)

    def test_full_detach_reattach_cycle(self):
        """Test a full detach and reattach cycle."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        self.engine.navigate(window_id, "https://google.com")
        self.engine.navigate(window_id, "https://wikipedia.org")

        # Detach
        detach_result = self.engine.detach_tab_to_window(window_id)
        detached_id = detach_result["detached_window_id"]
        detached_tab = self.engine.tab_registry[detached_id]

        # Verify detached state
        self.assertTrue(detached_tab.is_detached)
        self.assertEqual(detached_tab.url, "https://wikipedia.org")
        self.assertNotIn(window_id, self.engine.tab_registry)

        # Navigate while detached
        self.engine.navigate(detached_id, "https://duckduckgo.com")
        self.assertEqual(detached_tab.url, "https://duckduckgo.com")

        # Reattach
        reattach_result = self.engine.reattach_window_to_tab(detached_id)
        reattached_tab = self.engine.tab_registry[detached_id]

        # Verify reattached state
        self.assertFalse(reattached_tab.is_detached)
        self.assertEqual(reattached_tab.url, "https://duckduckgo.com")
        self.assertEqual(len(reattached_tab.history), 4)

    def test_multiple_detaches_from_same_tab(self):
        """Test that detaching the same tab twice doesn't create duplicates."""
        window_id = self.engine.create_tab("Test", "https://example.com")

        detach_result1 = self.engine.detach_tab_to_window(window_id)
        detached_id1 = detach_result1["detached_window_id"]

        # Original tab is gone, so detaching again should return None
        detach_result2 = self.engine.detach_tab_to_window(window_id)
        self.assertIsNone(detach_result2)

        # Only one detached tab should exist
        self.assertEqual(len(self.engine.tab_registry), 1)
        self.assertIn(detached_id1, self.engine.tab_registry)


class TestStateSync(unittest.TestCase):
    """Tests for state synchronization between tab and window."""

    def setUp(self):
        """Set up a fresh BrowserEngine for each test."""
        self.engine = BrowserEngine()

    def test_window_url_syncs_with_tab(self):
        """Test that window URL updates when tab navigates."""
        window_id = self.engine.create_tab("Test", "https://example.com")

        self.engine.navigate(window_id, "https://google.com")

        # Window URL should match tab URL
        window = self.engine.window_manager.windows[window_id]
        self.assertEqual(window.url, "https://google.com")

    def test_window_url_syncs_on_back(self):
        """Test that window URL updates when tab goes back."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        self.engine.navigate(window_id, "https://google.com")
        self.engine.navigate(window_id, "https://wikipedia.org")

        self.engine.go_back(window_id)

        window = self.engine.window_manager.windows[window_id]
        self.assertEqual(window.url, "https://google.com")

    def test_window_url_syncs_on_forward(self):
        """Test that window URL updates when tab goes forward."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        self.engine.navigate(window_id, "https://google.com")
        self.engine.navigate(window_id, "https://wikipedia.org")
        self.engine.go_back(window_id)

        self.engine.go_forward(window_id)

        window = self.engine.window_manager.windows[window_id]
        self.assertEqual(window.url, "https://wikipedia.org")

    def test_tab_state_matches_window_state(self):
        """Test that tab and window states are consistent."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        self.engine.navigate(window_id, "https://google.com")

        tab = self.engine.tab_registry[window_id]
        window = self.engine.window_manager.windows[window_id]

        self.assertEqual(tab.url, window.url)
        self.assertEqual(tab.history[-1], window.url)


class TestRoundTripIntegrity(unittest.TestCase):
    """Tests for state round-trip integrity."""

    def setUp(self):
        """Set up a fresh BrowserEngine for each test."""
        self.engine = BrowserEngine()

    def test_tab_state_round_trip(self):
        """Test that tab state survives serialization/deserialization."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        self.engine.navigate(window_id, "https://google.com")
        self.engine.navigate(window_id, "https://wikipedia.org")

        tab = self.engine.tab_registry[window_id]
        state = tab.to_dict()

        # Deserialize
        new_tab = Tab.from_dict(state)

        # Verify all properties match
        self.assertEqual(new_tab.window_id, tab.window_id)
        self.assertEqual(new_tab.url, tab.url)
        self.assertEqual(new_tab.history, tab.history)
        self.assertEqual(new_tab.history_index, tab.history_index)
        self.assertEqual(new_tab.title, tab.title)
        self.assertEqual(new_tab.is_detached, tab.is_detached)

    def test_browser_state_round_trip(self):
        """Test that browser state survives serialization/deserialization."""
        window_id = self.engine.create_tab("Test", "https://example.com")
        self.engine.navigate(window_id, "https://google.com")

        state = self.engine.to_dict()

        # Verify structure
        self.assertIn("windows", state)
        self.assertIn("tabs", state)
        self.assertIn(window_id, state["tabs"])

        # Verify tab data
        tab_state = state["tabs"][window_id]
        self.assertEqual(tab_state["url"], "https://google.com")
        self.assertEqual(len(tab_state["history"]), 2)


if __name__ == "__main__":
    unittest.main()

class TestStartMenu(unittest.TestCase):
    """Tests for the StartMenu class (Phase 3)."""

    def setUp(self):
        """Set up a fresh StartMenu for each test."""
        self.start_menu = StartMenu()

    def test_default_apps_loaded(self):
        """Test that default apps are loaded on initialization."""
        apps = self.start_menu.apps
        self.assertGreater(len(apps), 0)
        app_ids = [app["id"] for app in apps]
        self.assertIn("google", app_ids)
        self.assertIn("github", app_ids)
        self.assertIn("youtube", app_ids)
        self.assertIn("wikipedia", app_ids)

    def test_add_app(self):
        """Test adding a new app."""
        self.start_menu.add_app(
            app_id="custom",
            name="Custom App",
            url="https://custom.com",
            icon="🔧",
            category="tools",
        )
        apps = self.start_menu.apps
        custom_apps = [a for a in apps if a["id"] == "custom"]
        self.assertEqual(len(custom_apps), 1)
        self.assertEqual(custom_apps[0]["name"], "Custom App")
        self.assertEqual(custom_apps[0]["url"], "https://custom.com")
        self.assertEqual(custom_apps[0]["icon"], "🔧")
        self.assertEqual(custom_apps[0]["category"], "tools")

    def test_remove_app(self):
        """Test removing an app."""
        self.start_menu.add_app(
            app_id="temp",
            name="Temp App",
            url="https://temp.com",
        )
        self.assertTrue(self.start_menu.remove_app("temp"))
        apps = self.start_menu.apps
        temp_apps = [a for a in apps if a["id"] == "temp"]
        self.assertEqual(len(temp_apps), 0)

    def test_remove_nonexistent_app(self):
        """Test removing a nonexistent app returns False."""
        self.assertFalse(self.start_menu.remove_app("nonexistent"))

    def test_get_app(self):
        """Test getting an app by ID."""
        app = self.start_menu.get_app("google")
        self.assertIsNotNone(app)
        self.assertEqual(app["id"], "google")
        self.assertEqual(app["name"], "Google")

    def test_get_nonexistent_app(self):
        """Test getting a nonexistent app returns None."""
        app = self.start_menu.get_app("nonexistent")
        self.assertIsNone(app)

    def test_search_apps(self):
        """Test searching apps by query."""
        results = self.start_menu.search_apps("google")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "google")

    def test_search_apps_no_match(self):
        """Test searching apps with no match returns empty list."""
        results = self.start_menu.search_apps("nonexistent")
        self.assertEqual(len(results), 0)

    def test_search_apps_case_insensitive(self):
        """Test that search is case-insensitive."""
        results = self.start_menu.search_apps("GOOGLE")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], "google")

    def test_search_apps_partial_match(self):
        """Test that search matches partial names."""
        results = self.start_menu.search_apps("wiki")
        self.assertGreater(len(results), 0)
        self.assertTrue(any("wiki" in a["name"].lower() for a in results))

    def test_get_apps_by_category(self):
        """Test getting apps by category."""
        apps = self.start_menu.get_apps_by_category("search")
        self.assertGreater(len(apps), 0)
        self.assertTrue(all(a["category"] == "search" for a in apps))

    def test_get_apps_by_nonexistent_category(self):
        """Test getting apps by nonexistent category returns empty list."""
        apps = self.start_menu.get_apps_by_category("nonexistent")
        self.assertEqual(len(apps), 0)

    def test_to_dict(self):
        """Test that StartMenu state can be serialized."""
        self.start_menu.add_app(
            app_id="temp",
            name="Temp App",
            url="https://temp.com",
        )
        state = self.start_menu.to_dict()
        self.assertIn("apps", state)
        self.assertIn("search_query", state)
        self.assertIn("selected_category", state)
        self.assertEqual(state["search_query"], "")
        self.assertEqual(state["selected_category"], "all")

    def test_from_dict(self):
        """Test that StartMenu state can be deserialized."""
        state = {
            "apps": [
                {
                    "id": "custom",
                    "name": "Custom App",
                    "url": "https://custom.com",
                    "icon": "🔧",
                    "category": "tools",
                }
            ],
            "search_query": "custom",
            "selected_category": "tools",
        }
        start_menu = StartMenu.from_dict(state)
        self.assertEqual(len(start_menu.apps), 1)
        self.assertEqual(start_menu.apps[0]["id"], "custom")
        self.assertEqual(start_menu.search_query, "custom")
        self.assertEqual(start_menu.selected_category, "tools")

    def test_open_app(self):
        """Test that opening an app returns the app data."""
        result = self.start_menu.open_app("google")
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "google")
        self.assertEqual(result["url"], "https://www.google.com")

    def test_open_nonexistent_app(self):
        """Test that opening a nonexistent app returns None."""
        result = self.start_menu.open_app("nonexistent")
        self.assertIsNone(result)


class TestWindowSwitcher(unittest.TestCase):
    """Tests for the WindowSwitcher class (Phase 3)."""

    def setUp(self):
        """Set up a fresh WindowSwitcher for each test."""
        self.switcher = WindowSwitcher()

    def test_add_window(self):
        """Test adding a window to the switcher."""
        self.switcher.add_window(
            window_id=1,
            title="Test Window",
            url="https://example.com",
            icon="🌐",
        )
        windows = self.switcher.windows
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0]["window_id"], 1)
        self.assertEqual(windows[0]["title"], "Test Window")
        self.assertEqual(windows[0]["url"], "https://example.com")
        self.assertEqual(windows[0]["icon"], "🌐")

    def test_remove_window(self):
        """Test removing a window from the switcher."""
        self.switcher.add_window(
            window_id=1,
            title="Test Window",
            url="https://example.com",
        )
        self.assertTrue(self.switcher.remove_window(1))
        self.assertEqual(len(self.switcher.windows), 0)

    def test_remove_nonexistent_window(self):
        """Test removing a nonexistent window returns False."""
        self.assertFalse(self.switcher.remove_window(999))

    def test_get_window(self):
        """Test getting a window by ID."""
        self.switcher.add_window(
            window_id=1,
            title="Test Window",
            url="https://example.com",
        )
        window = self.switcher.get_window(1)
        self.assertIsNotNone(window)
        self.assertEqual(window["window_id"], 1)
        self.assertEqual(window["title"], "Test Window")

    def test_get_nonexistent_window(self):
        """Test getting a nonexistent window returns None."""
        window = self.switcher.get_window(999)
        self.assertIsNone(window)

    def test_focus_window(self):
        """Test focusing a window."""
        self.switcher.add_window(
            window_id=1,
            title="Test Window",
            url="https://example.com",
        )
        result = self.switcher.focus_window(1)
        self.assertTrue(result)
        self.assertEqual(self.switcher.selected_window_id, 1)

    def test_focus_nonexistent_window(self):
        """Test focusing a nonexistent window returns False."""
        result = self.switcher.focus_window(999)
        self.assertFalse(result)

    def test_to_dict(self):
        """Test that WindowSwitcher state can be serialized."""
        self.switcher.add_window(
            window_id=1,
            title="Test Window",
            url="https://example.com",
        )
        state = self.switcher.to_dict()
        self.assertIn("windows", state)
        self.assertIn("selected_window_id", state)
        self.assertEqual(state["selected_window_id"], None)

    def test_from_dict(self):
        """Test that WindowSwitcher state can be deserialized."""
        state = {
            "windows": [
                {
                    "window_id": 1,
                    "title": "Test Window",
                    "url": "https://example.com",
                    "icon": "🌐",
                }
            ],
            "selected_window_id": 1,
        }
        switcher = WindowSwitcher.from_dict(state)
        self.assertEqual(len(switcher.windows), 1)
        self.assertEqual(switcher.windows[0]["window_id"], 1)
        self.assertEqual(switcher.selected_window_id, 1)


class TestSystemTray(unittest.TestCase):
    """Tests for the SystemTray class (Phase 3)."""

    def setUp(self):
        """Set up a fresh SystemTray for each test."""
        self.tray = SystemTray()

    def test_default_items_loaded(self):
        """Test that default items are loaded on initialization."""
        items = self.tray.items
        self.assertGreater(len(items), 0)
        item_ids = [item["id"] for item in items]
        self.assertIn("clock", item_ids)
        self.assertIn("volume", item_ids)
        self.assertIn("network", item_ids)

    def test_add_item(self):
        """Test adding a new item."""
        self.tray.add_item(
            item_id="custom",
            name="Custom Item",
            icon="🔧",
            tooltip="Custom Tooltip",
        )
        items = self.tray.items
        custom_items = [i for i in items if i["id"] == "custom"]
        self.assertEqual(len(custom_items), 1)
        self.assertEqual(custom_items[0]["name"], "Custom Item")
        self.assertEqual(custom_items[0]["icon"], "🔧")
        self.assertEqual(custom_items[0]["tooltip"], "Custom Tooltip")

    def test_remove_item(self):
        """Test removing an item."""
        self.tray.add_item(
            item_id="temp",
            name="Temp Item",
            icon="🔧",
        )
        self.assertTrue(self.tray.remove_item("temp"))
        items = self.tray.items
        temp_items = [i for i in items if i["id"] == "temp"]
        self.assertEqual(len(temp_items), 0)

    def test_remove_nonexistent_item(self):
        """Test removing a nonexistent item returns False."""
        self.assertFalse(self.tray.remove_item("nonexistent"))

    def test_get_item(self):
        """Test getting an item by ID."""
        item = self.tray.get_item("clock")
        self.assertIsNotNone(item)
        self.assertEqual(item["id"], "clock")
        self.assertEqual(item["name"], "Clock")

    def test_get_nonexistent_item(self):
        """Test getting a nonexistent item returns None."""
        item = self.tray.get_item("nonexistent")
        self.assertIsNone(item)

    def test_update_clock(self):
        """Test updating the clock item."""
        self.tray.update_clock()
        clock_item = self.tray.get_item("clock")
        self.assertIsNotNone(clock_item)
        self.assertIn("tooltip", clock_item)
        self.assertIn("time", clock_item)

    def test_update_volume(self):
        """Test updating the volume item."""
        self.tray.update_volume(50)
        volume_item = self.tray.get_item("volume")
        self.assertIsNotNone(volume_item)
        self.assertEqual(volume_item["volume"], 50)

    def test_update_network(self):
        """Test updating the network item."""
        self.tray.update_network(True, 100)
        network_item = self.tray.get_item("network")
        self.assertIsNotNone(network_item)
        self.assertTrue(network_item["connected"])
        self.assertEqual(network_item["signal_strength"], 100)

    def test_to_dict(self):
        """Test that SystemTray state can be serialized."""
        state = self.tray.to_dict()
        self.assertIn("items", state)
        self.assertIn("clock", state)
        self.assertIn("volume", state)
        self.assertIn("network", state)

    def test_from_dict(self):
        """Test that SystemTray state can be deserialized."""
        state = {
            "items": [
                {
                    "id": "custom",
                    "name": "Custom Item",
                    "icon": "🔧",
                    "tooltip": "Custom Tooltip",
                }
            ],
            "clock": {"time": "12:00:00"},
            "volume": {"volume": 50},
            "network": {"connected": True, "signal_strength": 100},
        }
        tray = SystemTray.from_dict(state)
        self.assertEqual(len(tray.items), 1)
        self.assertEqual(tray.items[0]["id"], "custom")
        self.assertEqual(tray.clock["time"], "12:00:00")
        self.assertEqual(tray.volume["volume"], 50)
        self.assertTrue(tray.network["connected"])


if __name__ == "__main__":
    unittest.main()
