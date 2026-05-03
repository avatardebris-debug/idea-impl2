"""Tests for the detach_tab_to_window and reattach_window_to_tab functionality."""

import sys
import os

# Add workspace to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "workspace"))

from core.browser.browser_engine import BrowserEngine


def test_detach_creates_new_window_and_removes_original():
    """Detaching a tab should create a new floating window and remove the original."""
    engine = BrowserEngine()

    # Create initial window
    w1 = engine.create_tab("Home", "https://example.com")
    assert w1 == 1
    assert len(engine.window_manager.windows) == 1
    assert len(engine.tab_registry) == 1

    # Detach the tab
    result = engine.detach_tab_to_window(w1)
    assert result is not None
    assert "detached_window_id" in result
    assert "transition" in result

    # Original window should be gone
    assert w1 not in engine.window_manager.windows
    assert w1 not in engine.tab_registry

    # New floating window should exist
    new_id = result["detached_window_id"]
    assert new_id in engine.window_manager.windows
    assert new_id in engine.tab_registry

    # The new tab should be marked as detached
    detached_tab = engine.tab_registry[new_id]
    assert detached_tab.is_detached is True
    assert detached_tab.url == "https://example.com"

    # Only one window should remain
    assert len(engine.window_manager.windows) == 1
    assert len(engine.tab_registry) == 1

    print("✓ test_detach_creates_new_window_and_removes_original passed")


def test_detach_preserves_history():
    """Detaching should preserve the tab's navigation history."""
    engine = BrowserEngine()
    w1 = engine.create_tab("Home", "https://example.com")

    # Navigate a few times
    engine.navigate(w1, "https://example.com/page1")
    engine.navigate(w1, "https://example.com/page2")

    # Detach
    result = engine.detach_tab_to_window(w1)
    new_id = result["detached_window_id"]
    detached_tab = engine.tab_registry[new_id]

    assert detached_tab.url == "https://example.com/page2"
    assert len(detached_tab.history) == 3
    assert detached_tab.history[0] == "https://example.com"
    assert detached_tab.history[1] == "https://example.com/page1"
    assert detached_tab.history[2] == "https://example.com/page2"

    print("✓ test_detach_preserves_history passed")


def test_detach_transition_metadata():
    """Detaching should return proper transition metadata for animation."""
    engine = BrowserEngine()
    w1 = engine.create_tab("Home", "https://example.com", x=100, y=200)

    result = engine.detach_tab_to_window(w1)

    assert result["transition"]["start_x"] == 100
    assert result["transition"]["start_y"] == 200
    assert result["transition"]["end_x"] == 120  # 100 + 20 offset
    assert result["transition"]["end_y"] == 220  # 200 + 20 offset
    assert result["transition"]["duration_ms"] == 300
    assert result["transition"]["easing_type"] == "ease-out"

    print("✓ test_detach_transition_metadata passed")


def test_detach_already_detached_returns_none():
    """Detaching an already-detached tab should return None."""
    engine = BrowserEngine()
    w1 = engine.create_tab("Home", "https://example.com")
    engine.detach_tab_to_window(w1)

    # The original window ID no longer exists in the registry
    result = engine.detach_tab_to_window(w1)
    assert result is None

    print("✓ test_detach_already_detached_returns_none passed")


def test_detach_nonexistent_window_returns_none():
    """Detaching a nonexistent window should return None."""
    engine = BrowserEngine()
    result = engine.detach_tab_to_window(999)
    assert result is None

    print("✓ test_detach_nonexistent_window_returns_none passed")


def test_reattach_restores_tab():
    """Reattaching should restore the tab and remove the floating window."""
    engine = BrowserEngine()
    w1 = engine.create_tab("Home", "https://example.com")

    # Navigate and detach
    engine.navigate(w1, "https://example.com/page1")
    result = engine.detach_tab_to_window(w1)
    new_id = result["detached_window_id"]

    # Verify detached state
    assert new_id in engine.tab_registry
    assert engine.tab_registry[new_id].is_detached is True
    assert new_id in engine.window_manager.windows

    # Reattach
    reattach_result = engine.reattach_window_to_tab(new_id)
    assert reattach_result is not None
    assert "reattached_window_id" in reattach_result

    # The floating window should be gone
    assert new_id not in engine.window_manager.windows

    # The tab should be restored
    assert w1 in engine.tab_registry
    restored_tab = engine.tab_registry[w1]
    assert restored_tab.is_detached is False
    assert restored_tab.url == "https://example.com/page1"
    assert len(restored_tab.history) == 2

    print("✓ test_reattach_restores_tab passed")


def test_reattach_non_detached_returns_none():
    """Reattaching a non-detached tab should return None."""
    engine = BrowserEngine()
    w1 = engine.create_tab("Home", "https://example.com")

    result = engine.reattach_window_to_tab(w1)
    assert result is None

    print("✓ test_reattach_non_detached_returns_none passed")


def test_multiple_detaches():
    """Multiple tabs can be detached independently."""
    engine = BrowserEngine()
    w1 = engine.create_tab("Home", "https://example.com")
    w2 = engine.create_tab("Docs", "https://docs.example.com")

    # Detach both
    r1 = engine.detach_tab_to_window(w1)
    r2 = engine.detach_tab_to_window(w2)

    assert r1 is not None
    assert r2 is not None
    assert r1["detached_window_id"] != r2["detached_window_id"]

    # Both floating windows should exist
    assert len(engine.window_manager.windows) == 2
    assert len(engine.tab_registry) == 2

    # Original window IDs should be gone
    assert w1 not in engine.tab_registry
    assert w2 not in engine.tab_registry

    print("✓ test_multiple_detaches passed")


if __name__ == "__main__":
    test_detach_creates_new_window_and_removes_original()
    test_detach_preserves_history()
    test_detach_transition_metadata()
    test_detach_already_detached_returns_none()
    test_detach_nonexistent_window_returns_none()
    test_reattach_restores_tab()
    test_reattach_non_detached_returns_none()
    test_multiple_detaches()
    print("\n✅ All tests passed!")
