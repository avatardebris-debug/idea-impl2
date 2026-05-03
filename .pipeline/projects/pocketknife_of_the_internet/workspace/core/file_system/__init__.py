"""Virtual file system module for Pocketknife Browser Engine."""

from .virtual_file_system import VirtualFileSystem, VirtualFile, VirtualDirectory
from .file_persistence import FilePersistence
from .user_preferences import UserPreferences
from .file_explorer import FileExplorer

__all__ = [
    "VirtualFileSystem",
    "VirtualFile",
    "VirtualDirectory",
    "FilePersistence",
    "UserPreferences",
    "FileExplorer",
]
