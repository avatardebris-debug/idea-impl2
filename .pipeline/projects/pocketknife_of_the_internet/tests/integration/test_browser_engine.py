"""Integration tests for the Pocketknife Browser Engine (Phase 3).

Tests the Taskbar class and its integration with the browser engine.
"""

import unittest
from core.taskbar.taskbar import Taskbar


class TestTaskbar(unittest.TestCase):
    """Tests for the Taskbar class (Phase 3)."""

    def setUp(self):
        """Set up a fresh Taskbar for each test."""
        self.taskbar = Taskbar()

    def test_default_position(self):
        """Test that the taskbar defaults to bottom position."""
        self.assertEqual(self.taskbar.position, "bottom")

    def test_default_height(self):
        """Test that the taskbar defaults to 48px height."""
        self.assertEqual(self.taskbar.height, 48)

    def test_default_visible(self):
        """Test that the taskbar is visible by default."""
        self.assertTrue(self.taskbar.is_visible)

    def test_custom_initialization(self):
        """Test custom taskbar initialization."""
        tb = Taskbar(position="top", height=64, is_visible=False)
        self.assertEqual(tb.position, "top")
        self.assertEqual(tb.height, 64)
        self.assertFalse(tb.is_visible)

    def test_add_window(self):
        """Test adding a window to the taskbar."""
        self.taskbar.add_window(
            window_id=1,
            title="Test Window",
            url="https://example.com",
        )
        windows = self.taskbar.windows
        self.assertEqual(len(windows), 1)
        self.assertIn(1, windows)
        self.assertEqual(windows[1]["title"], "Test Window")
        self.assertEqual(windows[1]["url"], "https://example.com")
        self.assertFalse(windows[1]["is_minimized"])
        self.assertFalse(windows[1]["is_maximized"])
        self.assertFalse(windows[1]["is_active"])
        self.assertEqual(windows[1]["z_index"], 1)

    def test_add_window_with_state(self):
        """Test adding a window with initial state."""
        self.taskbar.add_window(
            window_id=1,
            title="Test Window",
            url="https://example.com",
            state={"is_minimized": True, "is_active": True},
        )
        window = self.taskbar.windows[1]
        self.assertTrue(window["is_minimized"])
        self.assertFalse(window["is_maximized"])
        self.assertTrue(window["is_active"])

    def test_add_multiple_windows(self):
        """Test adding multiple windows."""
        self.taskbar.add_window(1, "Win1", "https://1.com")
        self.taskbar.add_window(2, "Win2", "https://2.com")
        self.taskbar.add_window(3, "Win3", "https://3.com")
        self.assertEqual(len(self.taskbar.windows), 3)

    def test_remove_window(self):
        """Test removing a window from the taskbar."""
        self.taskbar.add_window(1, "Test", "https://example.com")
        self.assertTrue(self.taskbar.remove_window(1))
        self.assertEqual(len(self.taskbar.windows), 0)

    def test_remove_nonexistent_window(self):
        """Test removing a nonexistent window returns False."""
        self.assertFalse(self.taskbar.remove_window(999))

    def test_update_window_state(self):
        """Test updating window state."""
        self.taskbar.add_window(1, "Test", "https://example.com")
        self.taskbar.update_window_state(1, {"is_minimized": True, "is_active": True})
        window = self.taskbar.windows[1]
        self.assertTrue(window["is_minimized"])
        self.assertTrue(window["is_active"])

    def test_update_nonexistent_window_state(self):
        """Test updating a nonexistent window does nothing."""
        self.taskbar.update_window_state(999, {"is_minimized": True})
        self.assertEqual(len(self.taskbar.windows), 0)

    def test_get_window_list(self):
        """Test getting the window list."""
        self.taskbar.add_window(1, "Win1", "https://1.com")
        self.taskbar.add_window(2, "Win2", "https://2.com")
        window_list = self.taskbar.get_window_list()
        self.assertEqual(len(window_list), 2)
        self.assertEqual(window_list[0]["title"], "Win1")
        self.assertEqual(window_list[1]["title"], "Win2")

    def test_get_active_window(self):
        """Test getting the active window."""
        self.taskbar.add_window(1, "Win1", "https://1.com")
        self.taskbar.add_window(2, "Win2", "https://2.com")
        self.taskbar.update_window_state(2, {"is_active": True})
        active = self.taskbar.get_active_window()
        self.assertIsNotNone(active)
        self.assertEqual(active["window_id"], 2)

    def test_get_active_window_none(self):
        """Test getting active window when none is active."""
        self.taskbar.add_window(1, "Win1", "https://1.com")
        active = self.taskbar.get_active_window()
        self.assertIsNone(active)

    def test_render_preview(self):
        """Test rendering a window preview."""
        self.taskbar.add_window(
            1,
            "Preview Window",
            "https://preview.com",
            state={"is_minimized": True, "is_maximized": False, "is_active": True, "z_index": 5},
        )
        preview = self.taskbar.render_preview(1)
        self.assertIsNotNone(preview)
        self.assertEqual(preview["title"], "Preview Window")
        self.assertEqual(preview["url"], "https://preview.com")
        self.assertTrue(preview["is_minimized"])
        self.assertFalse(preview["is_maximized"])
        self.assertTrue(preview["is_active"])
        self.assertEqual(preview["z_index"], 5)

    def test_render_nonexistent_preview(self):
        """Test rendering a preview for a nonexistent window returns None."""
        preview = self.taskbar.render_preview(999)
        self.assertIsNone(preview)

    def test_windows_property_is_readonly_copy(self):
        """Test that the windows property returns a copy."""
        self.taskbar.add_window(1, "Test", "https://example.com")
        windows_copy = self.taskbar.windows
        windows_copy[2] = {"fake": True}
        self.assertNotIn(2, self.taskbar.windows)

    def test_repr(self):
        """Test the __repr__ method."""
        self.taskbar.add_window(1, "Test", "https://example.com")
        repr_str = repr(self.taskbar)
        self.assertIn("Taskbar", repr_str)
        self.assertIn("bottom", repr_str)
        self.assertIn("48", repr_str)
        self.assertIn("True", repr_str)
        self.assertIn("windows=1", repr_str)

    def test_position_setter(self):
        """Test setting the position."""
        self.taskbar.position = "top"
        self.assertEqual(self.taskbar.position, "top")

    def test_height_setter(self):
        """Test setting the height."""
        self.taskbar.height = 64
        self.assertEqual(self.taskbar.height, 64)

    def test_visible_setter(self):
        """Test setting the visibility."""
        self.taskbar.is_visible = False
        self.assertFalse(self.taskbar.is_visible)


if __name__ == "__main__":
    unittest.main()
