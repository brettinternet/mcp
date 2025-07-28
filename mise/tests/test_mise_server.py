"""Tests for the mise MCP server."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from mcp_server_mise.server import app, list_tools, call_tool
from mcp_server_mise.commands import run_mise_command


@pytest.fixture
def mock_subprocess():
    """Mock subprocess for testing."""
    with patch("mcp_server_mise.commands.subprocess.run") as mock_run:
        yield mock_run


@pytest.mark.asyncio
async def test_run_mise_command_success(mock_subprocess):
    """Test successful mise command execution."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "Success output"
    mock_result.stderr = ""
    mock_subprocess.return_value = mock_result

    result = await run_mise_command(["list"])

    assert result["success"] is True
    assert result["stdout"] == "Success output"
    assert result["stderr"] == ""
    assert result["returncode"] == 0
    mock_subprocess.assert_called_once_with(
        ["mise", "list"],
        capture_output=True,
        text=True,
        cwd=None,
        timeout=30,
    )


@pytest.mark.asyncio
async def test_run_mise_command_failure(mock_subprocess):
    """Test failed mise command execution."""
    mock_result = Mock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "Error message"
    mock_subprocess.return_value = mock_result

    result = await run_mise_command(["invalid-command"])

    assert result["success"] is False
    assert result["stdout"] == ""
    assert result["stderr"] == "Error message"
    assert result["returncode"] == 1


@pytest.mark.asyncio
async def test_run_mise_command_not_found(mock_subprocess):
    """Test mise command not found."""
    mock_subprocess.side_effect = FileNotFoundError()

    result = await run_mise_command(["list"])

    assert result["success"] is False
    assert "mise command not found" in result["stderr"]
    assert result["returncode"] == -1


@pytest.mark.asyncio
async def test_run_mise_command_timeout(mock_subprocess):
    """Test mise command timeout."""
    from subprocess import TimeoutExpired

    mock_subprocess.side_effect = TimeoutExpired(["mise", "list"], 30)

    result = await run_mise_command(["list"])

    assert result["success"] is False
    assert "timed out" in result["stderr"]
    assert result["returncode"] == -1


@pytest.mark.asyncio
async def test_list_tools():
    """Test listing available tools."""
    tools = await list_tools()

    tool_names = [tool.name for tool in tools]
    expected_tools = [
        "mise_install",
        "mise_uninstall",
        "mise_use",
        "mise_list",
        "mise_outdated",
        "mise_upgrade",
        "mise_current",
        "mise_exec",
        "mise_which",
        "mise_env",
    ]

    for expected_tool in expected_tools:
        assert expected_tool in tool_names


@pytest.mark.asyncio
async def test_call_tool_mise_install():
    """Test mise install tool call."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "Installing python@3.11...",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_install", {"tool": "python@3.11"})

        assert len(result) == 1
        assert "Installing python@3.11..." in result[0].text
        mock_run.assert_called_once_with(["install", "python@3.11"])


@pytest.mark.asyncio
async def test_call_tool_mise_install_global():
    """Test mise install tool call with global flag."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "Installing python@3.11 globally...",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_install", {"tool": "python@3.11", "global": True})

        assert len(result) == 1
        assert "Installing python@3.11 globally..." in result[0].text
        mock_run.assert_called_once_with(["install", "-g", "python@3.11"])


@pytest.mark.asyncio
async def test_call_tool_mise_uninstall():
    """Test mise uninstall tool call."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "Uninstalled python@3.10",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_uninstall", {"tool": "python@3.10"})

        assert len(result) == 1
        assert "Uninstalled python@3.10" in result[0].text
        mock_run.assert_called_once_with(["uninstall", "python@3.10"])


@pytest.mark.asyncio
async def test_call_tool_mise_use():
    """Test mise use tool call."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "Using python@3.11",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_use", {"tool": "python@3.11"})

        assert len(result) == 1
        assert "Using python@3.11" in result[0].text
        mock_run.assert_called_once_with(["use", "python@3.11"])


@pytest.mark.asyncio
async def test_call_tool_mise_use_global():
    """Test mise use tool call with global flag."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "Using python@3.11 globally",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_use", {"tool": "python@3.11", "global": True})

        assert len(result) == 1
        assert "Using python@3.11 globally" in result[0].text
        mock_run.assert_called_once_with(["use", "-g", "python@3.11"])


@pytest.mark.asyncio
async def test_call_tool_mise_list():
    """Test mise list tool call."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "python 3.11.0\nnode 20.0.0",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_list", {})

        assert len(result) == 1
        assert "python 3.11.0" in result[0].text
        assert "node 20.0.0" in result[0].text
        mock_run.assert_called_once_with(["list"])


@pytest.mark.asyncio
async def test_call_tool_mise_list_all():
    """Test mise list tool call with all flag."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "All available versions...",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_list", {"all": True})

        assert len(result) == 1
        assert "All available versions..." in result[0].text
        mock_run.assert_called_once_with(["list", "-a"])


@pytest.mark.asyncio
async def test_call_tool_mise_outdated():
    """Test mise outdated tool call."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "python 3.10.0 -> 3.11.0",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_outdated", {})

        assert len(result) == 1
        assert "python 3.10.0 -> 3.11.0" in result[0].text
        mock_run.assert_called_once_with(["outdated"])


@pytest.mark.asyncio
async def test_call_tool_mise_upgrade():
    """Test mise upgrade tool call."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "Upgraded python to 3.11.0",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_upgrade", {})

        assert len(result) == 1
        assert "Upgraded python to 3.11.0" in result[0].text
        mock_run.assert_called_once_with(["upgrade"])


@pytest.mark.asyncio
async def test_call_tool_mise_upgrade_specific():
    """Test mise upgrade tool call for specific tool."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "Upgraded python to 3.11.0",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_upgrade", {"tool": "python"})

        assert len(result) == 1
        assert "Upgraded python to 3.11.0" in result[0].text
        mock_run.assert_called_once_with(["upgrade", "python"])


@pytest.mark.asyncio
async def test_call_tool_mise_current():
    """Test mise current tool call."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "python 3.11.0\nnode 20.0.0",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_current", {})

        assert len(result) == 1
        assert "python 3.11.0" in result[0].text
        assert "node 20.0.0" in result[0].text
        mock_run.assert_called_once_with(["current"])


@pytest.mark.asyncio
async def test_call_tool_mise_exec():
    """Test mise exec tool call."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "Hello from python!",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_exec", {"command": "python --version"})

        assert len(result) == 1
        assert "Hello from python!" in result[0].text
        mock_run.assert_called_once_with(["exec", "--", "sh", "-c", "python --version"])


@pytest.mark.asyncio
async def test_call_tool_mise_which():
    """Test mise which tool call."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "/path/to/python",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_which", {"command": "python"})

        assert len(result) == 1
        assert "/path/to/python" in result[0].text
        mock_run.assert_called_once_with(["which", "python"])


@pytest.mark.asyncio
async def test_call_tool_mise_env():
    """Test mise env tool call."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": True,
            "stdout": "export PATH=/path/to/tools:$PATH",
            "stderr": "",
            "returncode": 0,
        }

        result = await call_tool("mise_env", {"shell": "bash"})

        assert len(result) == 1
        assert "export PATH" in result[0].text
        mock_run.assert_called_once_with(["env", "-s", "bash"])


@pytest.mark.asyncio
async def test_call_tool_unknown():
    """Test calling unknown tool."""
    result = await call_tool("unknown_tool", {})

    assert len(result) == 1
    assert "Unknown tool: unknown_tool" in result[0].text


@pytest.mark.asyncio
async def test_call_tool_error_handling():
    """Test error handling in tool calls."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.return_value = {
            "success": False,
            "stdout": "",
            "stderr": "Command failed with error",
            "returncode": 1,
        }

        result = await call_tool("mise_list", {})

        assert len(result) == 1
        assert "Error: Command failed with error" in result[0].text


@pytest.mark.asyncio
async def test_call_tool_exception_handling():
    """Test exception handling in tool calls."""
    with patch("mcp_server_mise.handlers.run_mise_command") as mock_run:
        mock_run.side_effect = Exception("Unexpected error")

        result = await call_tool("mise_list", {})

        assert len(result) == 1
        assert "Error executing mise_list: Unexpected error" in result[0].text
