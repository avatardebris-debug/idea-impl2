"""DropStore - Automated Dropshipping Store Builder

Main entry point for the application.
"""

import asyncio
import uvicorn


async def main():
    """Run the DropStore application."""
    config = uvicorn.Config(
        "backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
