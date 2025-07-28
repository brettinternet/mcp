"""Tool definitions for the mise MCP server."""

from mcp.types import Tool


def get_mise_tools() -> list[Tool]:
    """Get all mise-related tools."""
    return [
        Tool(
            name="mise_install",
            description="Install a tool or runtime using mise",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool": {
                        "type": "string",
                        "description": "Tool/runtime to install (e.g., 'python@3.11', 'node@20', 'go@latest')",
                    },
                    "global": {
                        "type": "boolean",
                        "description": "Install globally (default: false)",
                        "default": False,
                    },
                },
                "required": ["tool"],
            },
        ),
        Tool(
            name="mise_uninstall",
            description="Uninstall a tool or runtime using mise",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool": {
                        "type": "string",
                        "description": "Tool/runtime to uninstall (e.g., 'python@3.11', 'node@20')",
                    },
                },
                "required": ["tool"],
            },
        ),
        Tool(
            name="mise_use",
            description="Set tool version for current directory or globally",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool": {
                        "type": "string",
                        "description": "Tool and version to use (e.g., 'python@3.11', 'node@20')",
                    },
                    "global": {
                        "type": "boolean",
                        "description": "Set globally (default: false)",
                        "default": False,
                    },
                },
                "required": ["tool"],
            },
        ),
        Tool(
            name="mise_list",
            description="List installed tools and their versions",
            inputSchema={
                "type": "object",
                "properties": {
                    "all": {
                        "type": "boolean",
                        "description": "Show all available versions (default: false)",
                        "default": False,
                    },
                    "current": {
                        "type": "boolean",
                        "description": "Show only current/active versions (default: false)",
                        "default": False,
                    },
                },
            },
        ),
        Tool(
            name="mise_outdated",
            description="Show outdated tool versions",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="mise_upgrade",
            description="Upgrade tools to their latest versions",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool": {
                        "type": "string",
                        "description": "Specific tool to upgrade (optional, upgrades all if not specified)",
                    },
                },
            },
        ),
        Tool(
            name="mise_current",
            description="Show current tool versions in use",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="mise_exec",
            description="Execute a command with mise-managed tools in PATH",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to execute",
                    },
                    "tool": {
                        "type": "string",
                        "description": "Specific tool version to use (optional)",
                    },
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="mise_which",
            description="Show path to a binary managed by mise",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command/binary name to locate",
                    },
                },
                "required": ["command"],
            },
        ),
        Tool(
            name="mise_env",
            description="Show or export environment variables for mise tools",
            inputSchema={
                "type": "object",
                "properties": {
                    "shell": {
                        "type": "string",
                        "description": "Shell format (bash, zsh, fish, etc.)",
                        "default": "bash",
                    },
                },
            },
        ),
        Tool(
            name="mise_run",
            description="Run a command with mise environment variables loaded",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to execute with mise environment",
                    },
                },
                "required": ["command"],
            },
        ),
    ]


def get_all_tools() -> list[Tool]:
    """Get all available tools."""
    return get_mise_tools()
