"""python -m pipeline.engines → show package help / grok_build CLI pointer."""

from __future__ import annotations

import sys


def main() -> int:
    print(
        "pipeline.engines — dual-engine package (classic default + grok_build).\n"
        "\n"
        "  python -m pipeline.engines.grok_build --help\n"
        "  python -m pipeline.engines.grok_build --slug SLUG --phase 1 --step implement --dry-run\n"
        "\n"
        "Env: PIPELINE_ENGINE=classic|grok_build  GROK_BUILD_CMD  GROK_BUILD_DRY_RUN=1\n"
        "See COMMANDS.md § Dual-engine (Grok Build factory track).\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
