"""Pytest configuration for pantrychef_core tests.

On Windows, SQLite keeps file locks until the connection is explicitly closed
or garbage-collected. Because ``TemporaryDirectory.__exit__`` tries to
delete the directory while a ``Database`` object may still be alive, we
patch ``TemporaryDirectory`` to use ``ignore_cleanup_errors=True`` so that
Windows PermissionErrors during cleanup don't fail tests.
"""

import gc
import sys
import tempfile

import pytest


# Monkey-patch TemporaryDirectory to ignore cleanup errors on Windows.
# This is a targeted workaround for the Windows file-lock behaviour of SQLite.
if sys.platform == "win32":
    _OriginalTemporaryDirectory = tempfile.TemporaryDirectory

    class _WindowsTolerantTemporaryDirectory(_OriginalTemporaryDirectory):
        """TemporaryDirectory that silently ignores cleanup errors on Windows."""

        def cleanup(self):
            try:
                super().cleanup()
            except (PermissionError, OSError):
                pass  # best-effort on Windows with open SQLite file handles

        def __exit__(self, exc_type, exc_val, exc_tb):
            gc.collect()  # give Python a chance to close SQLite handles
            gc.collect()
            self.cleanup()

    tempfile.TemporaryDirectory = _WindowsTolerantTemporaryDirectory  # type: ignore[misc]


@pytest.fixture(autouse=True)
def _force_gc_after_test():
    """Force GC after every test to release SQLite connections."""
    yield
    gc.collect()
    gc.collect()
