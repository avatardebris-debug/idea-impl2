"""FileExplorer widget for browsing the virtual file system."""

from __future__ import annotations

from typing import Any
from .virtual_file_system import VirtualFileSystem, VirtualFile, VirtualDirectory


class FileExplorer:
    """Widget for browsing and interacting with the virtual file system.

    Provides a navigable interface for viewing, creating, editing,
    and managing files and directories within the virtual file system.

    Attributes:
        file_system: The VirtualFileSystem instance to browse.
        current_path: Current directory path being viewed.
        selected_file: Currently selected file (if any).
    """

    def __init__(self, file_system: VirtualFileSystem | None = None) -> None:
        """Initialize the FileExplorer.

        Args:
            file_system: Optional VirtualFileSystem instance. Creates a new one if not provided.
        """
        self.file_system = file_system or VirtualFileSystem()
        self.current_path = "/"
        self.selected_file: VirtualFile | None = None

    def navigate_to(self, path: str) -> list[dict[str, Any]]:
        """Navigate to a directory and return its contents.

        Args:
            path: Path to navigate to.

        Returns:
            List of directory contents.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        directory = self.file_system._resolve_path(path)
        self.current_path = path
        self.selected_file = None
        return directory.list_contents()

    def get_current_directory(self) -> VirtualDirectory:
        """Get the current directory.

        Returns:
            The current VirtualDirectory.
        """
        return self.file_system.get_directory(self.current_path)

    def select_file(self, file_name: str) -> VirtualFile | None:
        """Select a file in the current directory.

        Args:
            file_name: Name of the file to select.

        Returns:
            The selected VirtualFile, or None if not found.
        """
        directory = self.get_current_directory()
        file = directory.get_file(file_name)
        if file:
            self.selected_file = file
            return file
        return None

    def create_file(self, name: str, content: str = "") -> VirtualFile:
        """Create a new file in the current directory.

        Args:
            name: Name of the file.
            content: Initial content.

        Returns:
            The created VirtualFile.
        """
        directory = self.get_current_directory()
        return directory.create_file(name, content)

    def create_directory(self, name: str) -> VirtualDirectory:
        """Create a new directory in the current directory.

        Args:
            name: Name of the directory.

        Returns:
            The created VirtualDirectory.
        """
        directory = self.get_current_directory()
        return directory.create_directory(name)

    def delete_file(self, name: str) -> bool:
        """Delete a file from the current directory.

        Args:
            name: Name of the file to delete.

        Returns:
            True if deleted, False if not found.
        """
        directory = self.get_current_directory()
        return directory.delete_file(name)

    def delete_directory(self, name: str) -> bool:
        """Delete a directory from the current directory.

        Args:
            name: Name of the directory to delete.

        Returns:
            True if deleted, False if not found or not empty.
        """
        directory = self.get_current_directory()
        return directory.delete_directory(name)

    def rename_file(self, old_name: str, new_name: str) -> bool:
        """Rename a file in the current directory.

        Args:
            old_name: Current name of the file.
            new_name: New name for the file.

        Returns:
            True if renamed, False if not found.
        """
        directory = self.get_current_directory()
        return directory.rename_file(old_name, new_name)

    def get_file_content(self, file_name: str) -> str | None:
        """Get the content of a file.

        Args:
            file_name: Name of the file.

        Returns:
            File content, or None if not found.
        """
        directory = self.get_current_directory()
        file = directory.get_file(file_name)
        if file:
            return file.content
        return None

    def update_file_content(self, file_name: str, content: str) -> bool:
        """Update the content of a file.

        Args:
            file_name: Name of the file.
            content: New content.

        Returns:
            True if updated, False if not found.
        """
        directory = self.get_current_directory()
        file = directory.get_file(file_name)
        if file:
            file.content = content
            return True
        return False

    def get_file_metadata(self, file_name: str) -> dict[str, Any] | None:
        """Get metadata for a file.

        Args:
            file_name: Name of the file.

        Returns:
            File metadata, or None if not found.
        """
        directory = self.get_current_directory()
        file = directory.get_file(file_name)
        if file:
            return file.to_dict()
        return None

    def get_directory_metadata(self) -> dict[str, Any]:
        """Get metadata for the current directory.

        Returns:
            Directory metadata.
        """
        directory = self.get_current_directory()
        return directory.to_dict()

    def search_files(self, query: str) -> list[VirtualFile]:
        """Search for files by name or content.

        Args:
            query: Search query.

        Returns:
            List of matching VirtualFiles.
        """
        return self.file_system.search_files(query)

    def get_file_path(self, file_name: str) -> str | None:
        """Get the full path of a file.

        Args:
            file_name: Name of the file.

        Returns:
            Full path, or None if not found.
        """
        directory = self.get_current_directory()
        file = directory.get_file(file_name)
        if file:
            return f"{self.current_path}/{file_name}"
        return None

    def get_parent_path(self) -> str:
        """Get the parent directory path.

        Returns:
            Parent directory path.
        """
        if self.current_path == "/":
            return "/"
        parts = self.current_path.rstrip("/").split("/")
        if len(parts) == 1:
            return "/"
        return "/".join(parts[:-1])

    def get_breadcrumb(self) -> list[str]:
        """Get breadcrumb navigation.

        Returns:
            List of path segments for breadcrumb navigation.
        """
        if self.current_path == "/":
            return ["/"]
        return self.current_path.strip("/").split("/")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the FileExplorer state.

        Returns:
            Dictionary containing the FileExplorer state.
        """
        return {
            "current_path": self.current_path,
            "selected_file": self.selected_file.to_dict() if self.selected_file else None,
        }

    @classmethod
    def from_dict(cls, state: dict[str, Any], file_system: VirtualFileSystem | None = None) -> FileExplorer:
        """Deserialize a FileExplorer from a dictionary.

        Args:
            state: Dictionary containing the FileExplorer state.
            file_system: Optional VirtualFileSystem instance. Creates a new one if not provided.

        Returns:
            New FileExplorer instance.
        """
        explorer = cls(file_system)
        explorer.current_path = state.get("current_path", "/")
        if state.get("selected_file"):
            explorer.selected_file = VirtualFile.from_dict(state["selected_file"])
        return explorer

    def __repr__(self) -> str:
        return f"FileExplorer(current_path={self.current_path!r}, files={len(self.get_current_directory().files)})"
