"""CLI entry point for SEC Importer 2."""

from __future__ import annotations

import logging
import sys

from .commands import main

logger = logging.getLogger(__name__)


def cli():
    """CLI entry point."""
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"CLI error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
