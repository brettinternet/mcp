"""Tool call handlers for the mise MCP server."""

from typing import Sequence

from mcp.types import TextContent

from .commands import run_mise_command, run_command_with_mise_env


async def handle_mise_install(arguments: dict) -> Sequence[TextContent]:
    """Handle mise install tool call."""
    tool = arguments["tool"]
    global_flag = arguments.get("global", False)
    args = ["install"]
    if global_flag:
        args.append("-g")
    args.append(tool)
    result = await run_mise_command(args)
    return _format_result(result)


async def handle_mise_uninstall(arguments: dict) -> Sequence[TextContent]:
    """Handle mise uninstall tool call."""
    tool = arguments["tool"]
    args = ["uninstall", tool]
    result = await run_mise_command(args)
    return _format_result(result)


async def handle_mise_use(arguments: dict) -> Sequence[TextContent]:
    """Handle mise use tool call."""
    tool = arguments["tool"]
    global_flag = arguments.get("global", False)
    args = ["use"]
    if global_flag:
        args.append("-g")
    args.append(tool)
    result = await run_mise_command(args)
    return _format_result(result)


async def handle_mise_list(arguments: dict) -> Sequence[TextContent]:
    """Handle mise list tool call."""
    args = ["list"]
    if arguments.get("all", False):
        args.append("-a")
    if arguments.get("current", False):
        args.append("-c")
    result = await run_mise_command(args)
    return _format_result(result)


async def handle_mise_outdated(arguments: dict) -> Sequence[TextContent]:
    """Handle mise outdated tool call."""
    args = ["outdated"]
    result = await run_mise_command(args)
    return _format_result(result)


async def handle_mise_upgrade(arguments: dict) -> Sequence[TextContent]:
    """Handle mise upgrade tool call."""
    args = ["upgrade"]
    if "tool" in arguments:
        args.append(arguments["tool"])
    result = await run_mise_command(args)
    return _format_result(result)


async def handle_mise_current(arguments: dict) -> Sequence[TextContent]:
    """Handle mise current tool call."""
    args = ["current"]
    result = await run_mise_command(args)
    return _format_result(result)


async def handle_mise_exec(arguments: dict) -> Sequence[TextContent]:
    """Handle mise exec tool call."""
    command = arguments["command"]
    args = ["exec"]
    if "tool" in arguments:
        args.extend(["--", arguments["tool"]])
    args.extend(["--", "sh", "-c", command])
    result = await run_mise_command(args)
    return _format_result(result)


async def handle_mise_which(arguments: dict) -> Sequence[TextContent]:
    """Handle mise which tool call."""
    command = arguments["command"]
    args = ["which", command]
    result = await run_mise_command(args)
    return _format_result(result)


async def handle_mise_env(arguments: dict) -> Sequence[TextContent]:
    """Handle mise env tool call."""
    shell = arguments.get("shell", "bash")
    args = ["env", "-s", shell]
    result = await run_mise_command(args)
    return _format_result(result)


async def handle_mise_run(arguments: dict) -> Sequence[TextContent]:
    """Handle mise run tool call."""
    command = arguments["command"]
    result = await run_command_with_mise_env(command)
    return _format_result(result)


def _format_result(result: dict) -> Sequence[TextContent]:
    """Format command result into TextContent."""
    if result["success"]:
        output = result["stdout"].strip()
        if result["stderr"].strip():
            output += f"\n\nWarnings/Info:\n{result['stderr'].strip()}"
        return [TextContent(type="text", text=output or "Command completed successfully")]
    else:
        error_msg = result["stderr"].strip() or "Command failed"
        return [TextContent(type="text", text=f"Error: {error_msg}")]


# Handler mapping
TOOL_HANDLERS = {
    "mise_install": handle_mise_install,
    "mise_uninstall": handle_mise_uninstall,
    "mise_use": handle_mise_use,
    "mise_list": handle_mise_list,
    "mise_outdated": handle_mise_outdated,
    "mise_upgrade": handle_mise_upgrade,
    "mise_current": handle_mise_current,
    "mise_exec": handle_mise_exec,
    "mise_which": handle_mise_which,
    "mise_env": handle_mise_env,
    "mise_run": handle_mise_run,
}
