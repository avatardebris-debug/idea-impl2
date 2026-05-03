"""Virtual file system providing an in-memory directory tree with full CRUD operations."""

from __future__ import annotations

import time
import os
from typing import Any
from dataclasses import dataclass, field


@dataclass
class VirtualFile:
    """Represents a file in the virtual file system.

    Attributes:
        name: File name.
        path: Full path of the file.
        content: File content as a string.
        mime_type: MIME type of the file.
        size: Size of the file in bytes.
        created_at: Timestamp when the file was created.
        modified_at: Timestamp when the file was last modified.
    """

    name: str
    path: str
    content: str = ""
    mime_type: str = "text/plain"
    size: int = 0
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        """Update size after content is set."""
        self.size = len(self.content.encode("utf-8"))
        self.modified_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the file to a dictionary."""
        return {
            "type": "file",
            "name": self.name,
            "path": self.path,
            "content": self.content,
            "mime_type": self.mime_type,
            "size": self.size,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VirtualFile":
        """Create a VirtualFile from a dictionary."""
        return cls(
            name=data["name"],
            path=data["path"],
            content=data.get("content", ""),
            mime_type=data.get("mime_type", "text/plain"),
            size=data.get("size", 0),
            created_at=data.get("created_at", time.time()),
            modified_at=data.get("modified_at", time.time()),
        )


@dataclass
class VirtualDirectory:
    """Represents a directory in the virtual file system.

    Attributes:
        name: Directory name.
        path: Full path of the directory.
        children: Dictionary of child entries (files and directories).
        created_at: Timestamp when the directory was created.
        modified_at: Timestamp when the directory was last modified.
    """

    name: str
    path: str
    children: dict[str, "VirtualDirectory | VirtualFile"] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    modified_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        """Update modified_at when children change."""
        self.modified_at = time.time()

    def add_child(self, entry: "VirtualDirectory | VirtualFile") -> None:
        """Add a child entry to this directory.

        Args:
            entry: The entry to add.
        """
        self.children[entry.name] = entry
        self.modified_at = time.time()

    def remove_child(self, name: str) -> bool:
        """Remove a child entry from this directory.

        Args:
            name: Name of the entry to remove.

        Returns:
            True if removed, False if not found.
        """
        if name in self.children:
            del self.children[name]
            self.modified_at = time.time()
            return True
        return False

    def get_child(self, name: str) -> "VirtualDirectory | VirtualFile | None":
        """Get a child entry by name.

        Args:
            name: Name of the entry to get.

        Returns:
            The entry or None if not found.
        """
        return self.children.get(name)

    def list_contents(self) -> list[dict[str, Any]]:
        """List all contents of this directory.

        Returns:
            List of dictionaries representing each entry.
        """
        result = []
        for name, entry in self.children.items():
            if isinstance(entry, VirtualDirectory):
                result.append({
                    "name": entry.name,
                    "path": entry.path,
                    "type": "directory",
                    "created_at": entry.created_at,
                    "modified_at": entry.modified_at,
                })
            else:
                result.append({
                    "name": entry.name,
                    "path": entry.path,
                    "type": "file",
                    "mime_type": entry.mime_type,
                    "size": entry.size,
                    "created_at": entry.created_at,
                    "modified_at": entry.modified_at,
                })
        return result

    def to_dict(self) -> dict[str, Any]:
        """Serialize the directory to a dictionary."""
        return {
            "type": "directory",
            "name": self.name,
            "path": self.path,
            "children": {name: entry.to_dict() for name, entry in self.children.items()},
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VirtualDirectory":
        """Create a VirtualDirectory from a dictionary."""
        directory = cls(
            name=data["name"],
            path=data["path"],
            created_at=data.get("created_at", time.time()),
            modified_at=data.get("modified_at", time.time()),
        )
        for name, child_data in data.get("children", {}).items():
            if child_data["type"] == "file":
                directory.add_child(VirtualFile.from_dict(child_data))
            else:
                directory.add_child(VirtualDirectory.from_dict(child_data))
        return directory


class VirtualFileSystem:
    """In-memory virtual file system with directory tree support.

    Provides CRUD operations for files and directories, path resolution,
    and serialization/deserialization of the entire file system state.

    Attributes:
        root: Root directory of the file system.
        current_path: Current working directory path.
    """

    def __init__(self) -> None:
        """Initialize the virtual file system with an empty root directory."""
        self.root = VirtualDirectory(name="", path="/")
        self.current_path = "/"

    def _resolve_path(self, path: str) -> VirtualDirectory:
        """Resolve a path to a directory.

        Args:
            path: Path to resolve.

        Returns:
            The resolved directory.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        if path == "/":
            return self.root

        parts = path.strip("/").split("/")
        current = self.root

        for part in parts:
            if not part:
                continue
            if isinstance(current, VirtualDirectory):
                child = current.get_child(part)
                if child is None:
                    raise FileNotFoundError(f"Path not found: {path}")
                current = child
            else:
                raise FileNotFoundError(f"Path not found: {path}")

        if not isinstance(current, VirtualDirectory):
            raise FileNotFoundError(f"Path not found: {path}")

        return current

    def _get_parent_and_name(self, path: str) -> tuple[VirtualDirectory, str]:
        """Get the parent directory and entry name for a path.

        Args:
            path: Path to parse.

        Returns:
            Tuple of (parent directory, entry name).

        Raises:
            FileNotFoundError: If the parent directory does not exist.
        """
        parts = path.strip("/").split("/")
        if not parts or parts == [""]:
            raise FileNotFoundError(f"Cannot get parent of root: {path}")

        name = parts[-1]
        parent_path = "/".join(parts[:-1]) or "/"
        parent = self._resolve_path(parent_path)

        return parent, name

    def create_directory(self, path: str) -> VirtualDirectory:
        """Create a new directory at the specified path.

        Args:
            path: Path for the new directory.

        Returns:
            The created directory.

        Raises:
            FileExistsError: If a file or directory already exists at the path.
            FileNotFoundError: If the parent directory does not exist.
        """
        parent, name = self._get_parent_and_name(path)
        if name in parent.children:
            raise FileExistsError(f"Path already exists: {path}")

        directory = VirtualDirectory(name=name, path=path)
        parent.add_child(directory)
        return directory

    def create_file(self, path: str, content: str = "", mime_type: str = "text/plain") -> VirtualFile:
        """Create a new file at the specified path.

        Args:
            path: Path for the new file.
            content: Initial content for the file.
            mime_type: MIME type of the file.

        Returns:
            The created file.

        Raises:
            FileExistsError: If a file or directory already exists at the path.
            FileNotFoundError: If the parent directory does not exist.
        """
        parent, name = self._get_parent_and_name(path)
        if name in parent.children:
            raise FileExistsError(f"Path already exists: {path}")

        file_entry = VirtualFile(name=name, path=path, content=content, mime_type=mime_type)
        parent.add_child(file_entry)
        return file_entry

    def read_file(self, path: str) -> VirtualFile:
        """Read a file at the specified path.

        Args:
            path: Path to the file.

        Returns:
            The file entry.

        Raises:
            FileNotFoundError: If the file does not exist.
            IsADirectoryError: If the path points to a directory.
        """
        parts = path.strip("/").split("/")
        current = self.root

        for part in parts:
            if not part:
                continue
            if isinstance(current, VirtualDirectory):
                child = current.get_child(part)
                if child is None:
                    raise FileNotFoundError(f"File not found: {path}")
                current = child
            else:
                raise FileNotFoundError(f"File not found: {path}")

        if isinstance(current, VirtualDirectory):
            raise IsADirectoryError(f"Path is a directory: {path}")

        return current

    def write_file(self, path: str, content: str) -> None:
        """Write content to a file at the specified path.

        Args:
            path: Path to the file.
            content: Content to write.

        Raises:
            FileNotFoundError: If the file does not exist.
            IsADirectoryError: If the path points to a directory.
        """
        file_entry = self.read_file(path)
        file_entry.content = content
        file_entry.size = len(content.encode("utf-8"))
        file_entry.modified_at = time.time()

    def delete(self, path: str) -> None:
        """Delete a file or directory at the specified path.

        Args:
            path: Path to delete.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        parent, name = self._get_parent_and_name(path)
        if name not in parent.children:
            raise FileNotFoundError(f"Path not found: {path}")

        parent.remove_child(name)

    def move(self, source: str, destination: str) -> None:
        """Move a file or directory from source to destination.

        Args:
            source: Source path.
            destination: Destination path.

        Raises:
            FileNotFoundError: If the source does not exist.
            FileExistsError: If the destination already exists.
        """
        source_entry = self.read_file(source) if not self._is_directory(source) else self._resolve_path(source)

        if self._is_directory(destination):
            dest_dir = self._resolve_path(destination)
            new_path = f"{destination.rstrip('/')}/{source_entry.name}"
        else:
            dest_parent, dest_name = self._get_parent_and_name(destination)
            if dest_name in dest_parent.children:
                raise FileExistsError(f"Destination already exists: {destination}")
            new_path = destination

        # Remove from source
        source_parent, source_name = self._get_parent_and_name(source)
        source_parent.remove_child(source_name)

        # Update path and add to destination
        source_entry.path = new_path
        if self._is_directory(destination):
            dest_dir.add_child(source_entry)
        else:
            dest_parent.add_child(source_entry)

    def rename(self, path: str, new_name: str) -> None:
        """Rename a file or directory.

        Args:
            path: Current path of the entry.
            new_name: New name for the entry.

        Raises:
            FileNotFoundError: If the path does not exist.
            FileExistsError: If an entry with the new name already exists.
        """
        parent, name = self._get_parent_and_name(path)
        if new_name in parent.children:
            raise FileExistsError(f"Name already exists: {new_name}")

        entry = parent.children[name]
        entry.name = new_name
        entry.path = f"{path.rsplit('/', 1)[0]}/{new_name}"
        parent.children[new_name] = entry
        del parent.children[name]
        parent.modified_at = time.time()

    def list_directory(self, path: str | None = None) -> list[dict[str, Any]]:
        """List the contents of a directory.

        Args:
            path: Path to list. Defaults to current_path.

        Returns:
            List of dictionaries representing each entry.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        target_path = path if path is not None else self.current_path
        directory = self._resolve_path(target_path)
        return directory.list_contents()

    def get_file(self, path: str) -> VirtualFile:
        """Get a file entry by path.

        Args:
            path: Path to the file.

        Returns:
            The file entry.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        return self.read_file(path)

    def get_directory(self, path: str) -> VirtualDirectory:
        """Get a directory entry by path.

        Args:
            path: Path to the directory.

        Returns:
            The directory entry.

        Raises:
            FileNotFoundError: If the directory does not exist.
        """
        return self._resolve_path(path)

    def _is_directory(self, path: str) -> bool:
        """Check if a path points to a directory.

        Args:
            path: Path to check.

        Returns:
            True if the path points to a directory, False otherwise.
        """
        try:
            entry = self._resolve_path(path)
            return isinstance(entry, VirtualDirectory)
        except FileNotFoundError:
            return False

    def to_dict(self) -> dict[str, Any]:
        """Serialize the entire file system state to a dictionary.

        Returns:
            Dictionary containing the file system state.
        """
        return {
            "root": self.root.to_dict(),
            "current_path": self.current_path,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VirtualFileSystem":
        """Create a VirtualFileSystem from a dictionary.

        Args:
            data: Dictionary containing the file system state.

        Returns:
            A new VirtualFileSystem instance.
        """
        fs = cls()
        fs.root = VirtualDirectory.from_dict(data["root"])
        fs.current_path = data.get("current_path", "/")
        return fs

    def __repr__(self) -> str:
        return f"VirtualFileSystem(current_path={self.current_path!r}, files={len(self._count_files())})"

    def _count_files(self) -> int:
        """Count the total number of files in the file system.

        Returns:
            Number of files.
        """
        count = 0
        for entry in self.root.children.values():
            if isinstance(entry, VirtualFile):
                count += 1
            elif isinstance(entry, VirtualDirectory):
                count += self._count_directory_files(entry)
        return count

    def _count_directory_files(self, directory: VirtualDirectory) -> int:
        """Count files in a directory recursively.

        Args:
            directory: Directory to count files in.

        Returns:
            Number of files.
        """
        count = 0
        for entry in directory.children.values():
            if isinstance(entry, VirtualFile):
                count += 1
            elif isinstance(entry, VirtualDirectory):
                count += self._count_directory_files(entry)
        return count
