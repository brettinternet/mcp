"""Main MCP server for standup report generation."""

import asyncio
import logging
from typing import Any

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)

from .github import GitHubService
from .utils import DateParser
from .formatting import StandupFormatter

logger = logging.getLogger(__name__)

# Initialize services
github_service = GitHubService()
date_parser = DateParser()
formatter = StandupFormatter()

# Create server instance
server = Server("standup-server")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="get_standup_summary",
            description="Generate a comprehensive standup summary from GitHub activity",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Target date (e.g., 'yesterday', 'friday', '2024-07-22'). Defaults to last workday.",
                    },
                    "username": {
                        "type": "string",
                        "description": "GitHub username to filter by. If not provided, uses current authenticated user.",
                    },
                    "repos": {
                        "type": "string",
                        "description": "Comma-separated list of repositories (org/repo format). If not provided, uses all org repos.",
                    },
                },
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_github_activity",
            description="Get detailed GitHub activity for a specific date and user",
            inputSchema={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Target date (e.g., 'yesterday', 'friday', '2024-07-22')",
                    },
                    "username": {
                        "type": "string",
                        "description": "GitHub username to filter by",
                    },
                    "repos": {
                        "type": "string",
                        "description": "Comma-separated list of repositories (org/repo format)",
                    },
                },
                "required": ["date"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_workday_date",
            description="Parse and convert human-readable date expressions to ISO dates",
            inputSchema={
                "type": "object",
                "properties": {
                    "date_expression": {
                        "type": "string",
                        "description": "Date expression like 'yesterday', 'last friday', 'monday', etc.",
                    },
                },
                "required": ["date_expression"],
                "additionalProperties": False,
            },
        ),
        Tool(
            name="format_standup_report",
            description="Format activity data into a standup-friendly report",
            inputSchema={
                "type": "object",
                "properties": {
                    "github_activity": {
                        "type": "object",
                        "description": "GitHub activity data",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "text", "json"],
                        "description": "Output format",
                        "default": "markdown",
                    },
                },
                "required": ["github_activity"],
                "additionalProperties": False,
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[TextContent]:
    """Handle tool calls."""
    if arguments is None:
        arguments = {}

    try:
        if name == "get_standup_summary":
            return await _get_standup_summary(arguments)
        elif name == "get_github_activity":
            return await _get_github_activity(arguments)
        elif name == "get_workday_date":
            return await _get_workday_date(arguments)
        elif name == "format_standup_report":
            return await _format_standup_report(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def _get_standup_summary(arguments: dict[str, Any]) -> list[TextContent]:
    """Generate a comprehensive standup summary."""
    date = arguments.get("date", "")
    username = arguments.get("username", "")
    repos = arguments.get("repos", "")
    # Parse target date
    target_date = date_parser.parse_date(date)

    # Get GitHub activity
    github_activity = github_service.get_activity(
        target_date=target_date,
        username=username,
        repos=repos.split(",") if repos else None,
    )

    # Format the standup report
    report = formatter.format_standup_report(
        github_activity=github_activity,
        format_type="markdown",
    )

    return [TextContent(type="text", text=report)]


async def _get_github_activity(arguments: dict[str, Any]) -> list[TextContent]:
    """Get detailed GitHub activity."""
    date = arguments["date"]
    username = arguments.get("username", "")
    repos = arguments.get("repos", "")

    target_date = date_parser.parse_date(date)

    activity = github_service.get_activity(
        target_date=target_date,
        username=username,
        repos=repos.split(",") if repos else None,
    )

    formatted = formatter.format_github_activity(activity)
    return [TextContent(type="text", text=formatted)]


async def _get_workday_date(arguments: dict[str, Any]) -> list[TextContent]:
    """Parse date expression to ISO date."""
    date_expression = arguments["date_expression"]
    parsed_date = date_parser.parse_date(date_expression)

    return [TextContent(type="text", text=f"Parsed date: {parsed_date.isoformat()}")]


async def _format_standup_report(arguments: dict[str, Any]) -> list[TextContent]:
    """Format activity data into standup report."""
    github_activity = arguments["github_activity"]
    format_type = arguments.get("format", "markdown")

    report = formatter.format_standup_report(
        github_activity=github_activity,
        format_type=format_type,
    )

    return [TextContent(type="text", text=report)]


async def main():
    """Main entry point for the server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="standup-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities=None,
                ),
            ),
        )


def main_sync():
    """Synchronous entry point for console scripts."""
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
