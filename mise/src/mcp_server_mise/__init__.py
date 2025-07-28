"""Mise MCP Server - Dependency management through mise commands."""

import asyncio

from .server import main

__version__ = "0.0.1"
__all__ = ["main"]


if __name__ == "__main__":
    asyncio.run(main())
