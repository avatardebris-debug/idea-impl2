# Phase 5 Tasks

- [ ] Task 1: Implement VirtualFileSystem core
  - What: Build the VirtualFileSystem class that provides an in-memory directory tree with file create, read, write, delete, move, and rename operations. Support directories and files with metadata (name, path, size, mime_type, created_at, modified_at).
  - Files: workspace/core/file_system/virtual_file_system.py (new), workspace/core/file_system/__init__.py (new)
  - Done when: Can create directories and files, read/write file content, delete files/dirs, rename/move entries, list directory contents, and serialize/deserialize the entire file system state to a dict. At least 10 files across 3 directories can be created and manipulated without errors.

- [ ] Task 2: Implement FilePersistence layer
  - What: Build a FilePersistence class that saves and loads the VirtualFileSystem state to disk (JSON) so the file system survives across browser sessions. Also add a UserPreferences class for storing user settings (window positions, theme, pinned apps) with the same persistence mechanism.
  - Files: workspace/core/file_system/file_persistence.py (new), workspace/core/file_system/user_preferences.py (new)
  - Done when: Can save a populated VirtualFileSystem to a JSON file, load it back, and verify all files/directories are intact. UserPreferences can store and retrieve arbitrary key-value settings with persistence. Loading a non-existent file creates a fresh empty state gracefully.

- [ ] Task 3: Integrate file system with BrowserEngine and Tab
  - What: Add a VirtualFileSystem instance to BrowserEngine so every tab/window can access the shared file system. Extend Tab with a download() method that creates a file in the virtual file system from tab content. Add upload() method to read a virtual file and make it available to a tab.
  - Files: workspace/core/browser/browser_engine.py (modify), workspace/core/browser/tab.py (modify)
  - Done when: BrowserEngine creates and exposes a VirtualFileSystem instance. Tab.download() creates a file in the virtual file system with the correct content and metadata. Tab.upload() reads a file from the virtual file system and sets it as the tab's content. File system is shared across all tabs in the same engine instance.

- [ ] Task 4: Build File Explorer window type
  - What: Create a FileExplorer class that represents a window for browsing the virtual file system. It should display directory listings, support navigation (open folder, go up, go back/forward), and show file metadata. Integrate it with the StartMenu so users can launch it from the app launcher.
  - Files: workspace/core/file_system/file_explorer.py (new), workspace/core/taskbar/start_menu.py (modify)
  - Done when: FileExplorer can list directory contents, navigate into subdirectories, go up one level, and go back/forward through navigation history. Shows file metadata (name, size, type). StartMenu includes a "File Explorer" entry that opens a FileExplorer window. FileExplorer can be launched and navigated without errors.

- [ ] Task 5: Add drag-and-drop file sharing between windows
  - What: Implement drag-and-drop support in the Window class and WindowManager to allow files from the virtual file system to be dragged from a FileExplorer window and dropped onto another window/tab. Track drag state and provide drop-zone detection.
  - Files: workspace/core/window_manager/window.py (modify), workspace/core/window_manager/window_manager.py (modify)
  - Done when: A file can be "dragged" from a FileExplorer and "dropped" onto another window, resulting in the file being accessible in the target window's context. Drag state is tracked correctly (dragging, drop target, drop result). WindowManager handles drop events and routes them to the correct window. No files are lost or corrupted during drag-and-drop.

- [ ] Task 6: Write tests and integration verification
  - What: Write unit tests for VirtualFileSystem, FilePersistence, UserPreferences, FileExplorer, and the drag-and-drop integration. Write an integration test that exercises the full flow: create files in FileExplorer, drag-drop to another window, save state to disk, reload, and verify persistence.
  - Files: workspace/tests/test_file_system.py (new), workspace/tests/test_integration.py (modify)
  - Done when: All unit tests pass with pytest. Integration test covers: file creation, drag-and-drop, persistence across sessions, cross-app file access. At least 20 test cases covering happy paths and edge cases (empty directories, missing files, circular references, large files).