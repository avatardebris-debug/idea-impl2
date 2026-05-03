# Phase 1 Tasks — Pocketknife of the Internet

## Overview
Build the foundational windowing system and core browser infrastructure that enables draggable, movable windows within a browser-based interface.

---

- [x] Task 1: Project Structure Setup
**What to build:** Initialize the workspace directory structure for the browser engine project.
**Files:**
- `.pipeline/projects/pocketknife_of_the_internet/workspace/core/` (directory)
- `.pipeline/projects/pocketknife_of_the_internet/workspace/core/__init__.py`
- `.pipeline/projects/pocketknife_of_the_internet/workspace/core/window_manager/__init__.py`
- `.pipeline/projects/pocketknife_of_the_internet/workspace/core/window_manager/window.py`
- `.pipeline/projects/pocketknife_of_the_internet/workspace/core/window_manager/window_manager.py`
- `.pipeline/projects/pocketknife_of_the_internet/workspace/core/browser/__init__.py`
- `.pipeline/projects/pocketknife_of_the_internet/workspace/core/browser/browser_engine.py`
- `.pipeline/projects/pocketknife_of_the_internet/workspace/core/browser/tab.py`
**Acceptance Criteria:**
- All directories created
- All `__init__.py` files present (can be empty or with basic exports)
- File structure follows Python package conventions

---

- [x] Task 2: Window Class Implementation
**What to build:** Core Window class that represents a draggable browser window/tab.
**Files:**
- `.pipeline/projects/pocketknife_of_the_internet/workspace/core/window_manager/window.py`
**Acceptance Criteria:**
- Window class has properties: `id`, `title`, `url`, `x`, `y`, `width`, `height`, `z_index`, `is_minimized`, `is_maximized`
- Methods implemented:
  - `__init__(self, id, title, url, x=100, y=100, width=800, height=600)`
  - `move(self, x, y)` - moves window to new position
  - `resize(self, width, height)` - resizes window
  - `set_z_index(self, z_index)` - brings window to front
  - `minimize(self)` - minimizes window
  - `maximize(self)` - maximizes window
  - `restore(self)` - restores from minimized/maximized state
  - `to_dict(self)` - returns window state as dictionary
- Window has proper initialization with defaults
- State can be serialized/deserialized via `to_dict`/constructor

---

- [x] Task 3: Window Manager Core
**What to build:** Window manager that handles multiple windows, z-index ordering, and window lifecycle.
**Files:**
- `.pipeline/projects/pocketknife_of_the_internet/workspace/core/window_manager/window_manager.py`
**Acceptance Criteria:**
- WindowManager class has properties: `windows` (dict), `next_window_id` (int), `active_window_id` (int)
- Methods implemented:
  - `__init__(self)` - initializes empty windows dict
  - `create_window(self, title, url, x=100, y=100, width=800, height=600)` - creates new window, returns Window instance
  - `close_window(self, window_id)` - removes window, returns True if closed
  - `get_window(self, window_id)` - returns Window instance or None
  - `focus_window(self, window_id)` - brings window to front, sets as active
  - `get_active_window(self)` - returns currently active window or None
  - `arrange_windows(self)` - arranges windows in cascade layout (prevents overlap)
  - `to_dict(self)` - returns all windows as dictionary
- Window ordering via z_index works correctly
- Active window tracking works
- Cascade arrangement prevents window overlap

---

- [x] Task 4: Browser Engine Core
**What to build:** Core browser engine that manages tabs/windows and provides basic navigation.
**Files:**
- `.pipeline/projects/pocketknife_of_the_internet/workspace/core/browser/browser_engine.py`
- `.pipeline/projects/pocketknife_of_the_internet/workspace/core/browser/tab.py`
**Acceptance Criteria:**
- Tab class has properties: `window_id`, `url`, `history` (list), `history_index` (int)
- Tab methods:
  - `__init__(self, window_id, url)`
  - `navigate(self, url)` - updates URL, adds to history
  - `go_back(self)` - goes to previous URL in history
  - `go_forward(self)` - goes to next URL in history
  - `reload(self)` - reloads current URL
  - `to_dict(self)` - returns tab state
- BrowserEngine class has:
  - `__init__(self)` - initializes window_manager and tab_registry
  - `create_tab(self, title, url)` - creates new window/tab, returns window_id
  - `close_tab(self, window_id)` - closes tab/window
  - `navigate(self, window_id, url)` - navigates window to URL
  - `go_back(self, window_id)` - goes back in history
  - `go_forward(self, window_id)` - goes forward in history
  - `reload(self, window_id)` - reloads current page
  - `get_tab(self, window_id)` - returns tab state dict
  - `get_active_window_id(self)` - returns active window ID
- Tab navigation history works correctly
- BrowserEngine integrates with WindowManager

---

- [x] Task 5: Basic HTML Renderer
**What to build:** Simple HTML renderer that displays content in windows.
**Files:**
- `.pipeline/projects/pocketknife_of_the_internet/workspace/core/browser/html_renderer.py`
**Acceptance Criteria:**
- HtmlRenderer class with methods:
  - `__init__(self)`
  - `render(self, html_content)` - parses and renders basic HTML
  - `render_url(self, url)` - fetches and renders URL content (returns placeholder for now)
  - `get_content(self)` - returns rendered content as HTML string
- Basic HTML tags supported: `p`, `h1-h6`, `a`, `div`, `span`, `img`
- Returns valid HTML string output
- For now, `render_url` returns placeholder text indicating URL navigation

---

- [ ] Task 6: Integration and Testing
**What to build:** Integration tests to verify the windowing system works end-to-end.
**Files:**
- `.pipeline/projects/pocketknife_of_the_internet/workspace/tests/test_integration.py`
- `.pipeline/projects/pocketknife_of_the_internet/workspace/tests/__init__.py`
**Acceptance Criteria:**
- Test class `TestWindowManager` with methods:
  - `test_create_and_close_window` - creates window, verifies properties, closes it
  - `test_window_focus_ordering` - creates multiple windows, verifies z-index updates on focus
  - `test_window_arrangement` - creates windows, verifies cascade arrangement prevents overlap
  - `test_minimize_maximize` - creates window, minimizes, maximizes, restores
- Test class `TestBrowserEngine` with methods:
  - `test_create_and_navigate_tab` - creates tab, navigates, verifies URL update
  - `test_history_navigation` - creates tab, navigates multiple URLs, tests back/forward
  - `test_tab_lifecycle` - creates tab, navigates, closes, verifies cleanup
- All tests pass when run
- Test output is clear and indicates success/failure

---

- [ ] Task 7: Main Entry Point
**What to build:** Main application entry point that initializes the browser engine.
**Files:**
- `.pipeline/projects/pocketknife_of_the_internet/workspace/main.py`
- `.pipeline/projects/pocketknife_of_the_internet/workspace/__init__.py`
**Acceptance Criteria:**
- `main.py` has `if __name__ == "__main__"` block
- Creates BrowserEngine instance
- Demonstrates basic usage: creates initial window/tab
- Prints status messages about browser initialization
- Can be run with `python main.py`
- No errors on startup
- Shows browser is ready (prints "Pocketknife Browser Engine Ready")

---

## Summary
Phase 1 delivers a functional windowing browser engine with:
- Draggable, movable windows with proper z-index management
- Tab-based navigation with history
- Basic HTML rendering capability
- Full integration tests
- Runnable main application

All components are designed to be extended in subsequent phases with full drag-and-drop, window controls, and advanced features.