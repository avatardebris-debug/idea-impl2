"""Main entry point for the Pocketknife Browser Engine."""

import sys
import os

# Add workspace to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "workspace"))

from core.browser.browser_engine import BrowserEngine


def main():
    """Initialize and demonstrate the Pocketknife Browser Engine."""
    print("=" * 60)
    print("  Pocketknife Browser Engine")
    print("  A lightweight windowing browser engine")
    print("=" * 60)
    print()

    # Create the browser engine
    engine = BrowserEngine()
    print("[*] Browser engine initialized.")
    print(f"    Windows: {len(engine.window_manager.windows)}")
    print(f"    Tabs: {len(engine.tab_registry)}")
    print()

    # Create initial window/tab
    print("[*] Creating initial window...")
    w1 = engine.create_tab("Pocketknife - Home", "https://pocketknife.dev/home")
    print(f"    Window ID: {w1}")
    print(f"    URL: https://pocketknife.dev/home")
    print()

    # Create additional windows
    print("[*] Creating additional windows...")
    w2 = engine.create_tab("Pocketknife - Docs", "https://pocketknife.dev/docs")
    w3 = engine.create_tab("Pocketknife - Settings", "https://pocketknife.dev/settings")
    print(f"    Window IDs: {w1}, {w2}, {w3}")
    print()

    # Navigate
    print("[*] Navigating window 2...")
    engine.navigate(w2, "https://pocketknife.dev/api")
    print(f"    New URL: https://pocketknife.dev/api")
    print()

    # History
    print("[*] Testing history...")
    prev = engine.go_back(w2)
    print(f"    Go back: {prev}")
    engine.go_forward(w2)
    print(f"    Go forward: https://pocketknife.dev/api")
    print()

    # Focus
    print("[*] Focusing window 1...")
    engine.focus_window(w1)
    active = engine.get_active_window_id()
    print(f"    Active window: {active}")
    print()

    # Arrange
    print("[*] Arranging windows...")
    engine.arrange_windows()
    for wid, win in engine.window_manager.windows.items():
        print(f"    Window {wid}: x={win.x}, y={win.y}, w={win.width}, h={win.height}")
    print()

    # Close
    print("[*] Closing window 3...")
    engine.close_tab(w3)
    print(f"    Remaining windows: {len(engine.window_manager.windows)}")
    print()

    # State
    print("[*] Browser state:")
    state = engine.to_dict()
    print(f"    Windows: {len(state['windows'])}")
    print(f"    Tabs: {len(state['tabs'])}")
    print()

    print("=" * 60)
    print("  Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
