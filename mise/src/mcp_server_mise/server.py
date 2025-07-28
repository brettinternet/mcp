"""Main MCP server implementation."""

from typing import Sequence

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .handlers import TOOL_HANDLERS
from .tools import get_all_tools


app = Server("mise-mcp-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available mise management tools."""
    return get_all_tools()


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
    """Handle tool calls for mise operations."""
    try:
        if name in TOOL_HANDLERS:
            return await TOOL_HANDLERS[name](arguments)
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]


async def main():
    """Main entry point for the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mise-mcp-server",
                server_version="0.0.1",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
