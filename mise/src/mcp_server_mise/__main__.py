"""Entry point for running the MCP server as a module."""

import asyncio
from .server import main


def cli_main():
    """Entry point for the CLI script."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()