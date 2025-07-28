"""Tests for server module."""

import pytest
from datetime import datetime
from unittest.mock import patch, AsyncMock

from mcp.types import TextContent

from mcp_server_standup.server import (
    handle_list_tools,
    handle_call_tool,
    _get_standup_summary,
    _get_github_activity,
    _get_workday_date,
    _format_standup_report,
    github_service,
    date_parser,
    formatter,
)
from mcp_server_standup.github import GitHubActivity


class TestMCPServer:
    """Test the MCP server functionality."""

    @pytest.mark.asyncio
    async def test_handle_list_tools(self):
        """Test that list_tools returns expected tools."""
        tools = await handle_list_tools()

        assert len(tools) == 4
        tool_names = [tool.name for tool in tools]

        assert "get_standup_summary" in tool_names
        assert "get_github_activity" in tool_names
        assert "get_workday_date" in tool_names
        assert "format_standup_report" in tool_names

    @pytest.mark.asyncio
    async def test_handle_list_tools_schemas(self):
        """Test that tools have proper schemas."""
        tools = await handle_list_tools()

        standup_tool = next(
            tool for tool in tools if tool.name == "get_standup_summary"
        )

        # Check required properties exist
        props = standup_tool.inputSchema["properties"]
        assert "date" in props
        assert "username" in props
        assert "repos" in props

        # Check that include_linear was removed
        assert "include_linear" not in props

    @pytest.mark.asyncio
    async def test_handle_call_tool_unknown_tool(self):
        """Test calling unknown tool returns error."""
        result = await handle_call_tool("unknown_tool", {})

        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Unknown tool" in result[0].text

    @pytest.mark.asyncio
    async def test_handle_call_tool_none_arguments(self):
        """Test calling tool with None arguments."""
        with patch(
            "standup_server.server._get_workday_date", new_callable=AsyncMock
        ) as mock_func:
            mock_func.return_value = [TextContent(type="text", text="test")]

            await handle_call_tool("get_workday_date", None)

            mock_func.assert_called_once_with({})

    @pytest.mark.asyncio
    async def test_handle_call_tool_exception_handling(self):
        """Test that exceptions in tools are handled gracefully."""
        with patch(
            "standup_server.server._get_workday_date",
            side_effect=Exception("Test error"),
        ):
            result = await handle_call_tool(
                "get_workday_date", {"date_expression": "test"}
            )

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Error: Test error" in result[0].text


class TestStandupSummaryTool:
    """Test the get_standup_summary tool."""

    @pytest.mark.asyncio
    async def test_get_standup_summary_basic(self):
        """Test basic standup summary generation."""
        # Mock the services
        mock_activity = GitHubActivity(
            target_date=datetime(2024, 7, 23, 0, 0, 0, 0),
            username="testuser",
            repos=None,
            events=[],
            summary={"total_events": 0, "repositories": []},
        )

        with patch.object(date_parser, "parse_date") as mock_parse:
            with patch.object(
                github_service, "get_activity", new_callable=AsyncMock
            ) as mock_get_activity:
                with patch.object(formatter, "format_standup_report") as mock_format:
                    mock_parse.return_value = datetime(2024, 7, 23, 0, 0, 0, 0)
                    mock_get_activity.return_value = mock_activity
                    mock_format.return_value = "# Standup Summary\n\nNo activity"

                    result = await _get_standup_summary(
                        {
                            "date": "yesterday",
                            "username": "testuser",
                            "repos": "org/repo1,org/repo2",
                        }
                    )

                    assert len(result) == 1
                    assert isinstance(result[0], TextContent)
                    assert "Standup Summary" in result[0].text

                    # Verify service calls
                    mock_parse.assert_called_once_with("yesterday")
                    mock_get_activity.assert_called_once_with(
                        target_date=datetime(2024, 7, 23, 0, 0, 0, 0),
                        username="testuser",
                        repos=["org/repo1", "org/repo2"],
                    )
                    mock_format.assert_called_once_with(
                        github_activity=mock_activity, format_type="markdown"
                    )

    @pytest.mark.asyncio
    async def test_get_standup_summary_empty_arguments(self):
        """Test standup summary with empty arguments."""
        mock_activity = GitHubActivity(
            target_date=datetime(2024, 7, 22, 0, 0, 0, 0),
            username=None,
            repos=None,
            events=[],
            summary={"total_events": 0, "repositories": []},
        )

        with patch.object(date_parser, "parse_date") as mock_parse:
            with patch.object(
                github_service, "get_activity", new_callable=AsyncMock
            ) as mock_get_activity:
                with patch.object(formatter, "format_standup_report") as mock_format:
                    mock_parse.return_value = datetime(2024, 7, 22, 0, 0, 0, 0)
                    mock_get_activity.return_value = mock_activity
                    mock_format.return_value = "No activity"

                    await _get_standup_summary({})

                    # Should use defaults
                    mock_get_activity.assert_called_once_with(
                        target_date=datetime(2024, 7, 22, 0, 0, 0, 0),
                        username="",
                        repos=None,
                    )

    @pytest.mark.asyncio
    async def test_get_standup_summary_repos_parsing(self):
        """Test that repos string is properly parsed."""
        mock_activity = GitHubActivity(
            target_date=datetime(2024, 7, 23, 0, 0, 0, 0),
            username="testuser",
            repos=["org/repo1", "org/repo2", "org/repo3"],
            events=[],
            summary={"total_events": 0, "repositories": []},
        )

        with patch.object(date_parser, "parse_date") as mock_parse:
            with patch.object(
                github_service, "get_activity", new_callable=AsyncMock
            ) as mock_get_activity:
                with patch.object(formatter, "format_standup_report") as mock_format:
                    mock_parse.return_value = datetime(2024, 7, 23, 0, 0, 0, 0)
                    mock_get_activity.return_value = mock_activity
                    mock_format.return_value = "Summary"

                    await _get_standup_summary(
                        {"repos": "  org/repo1  , org/repo2 ,org/repo3  "}
                    )

                    # Should parse and clean repos
                    mock_get_activity.assert_called_once_with(
                        target_date=datetime(2024, 7, 23, 0, 0, 0, 0),
                        username="",
                        repos=["  org/repo1  ", " org/repo2 ", "org/repo3  "],
                    )


class TestGitHubActivityTool:
    """Test the get_github_activity tool."""

    @pytest.mark.asyncio
    async def test_get_github_activity_basic(self):
        """Test basic GitHub activity fetching."""
        mock_activity = GitHubActivity(
            target_date=datetime(2024, 7, 23, 0, 0, 0, 0),
            username="testuser",
            repos=["org/repo1"],
            events=[],
            summary={"total_events": 0, "repositories": []},
        )

        with patch.object(date_parser, "parse_date") as mock_parse:
            with patch.object(
                github_service, "get_activity", new_callable=AsyncMock
            ) as mock_get_activity:
                with patch.object(formatter, "format_github_activity") as mock_format:
                    mock_parse.return_value = datetime(2024, 7, 23, 0, 0, 0, 0)
                    mock_get_activity.return_value = mock_activity
                    mock_format.return_value = "# GitHub Activity\n\nNo events"

                    result = await _get_github_activity(
                        {
                            "date": "2024-07-23",
                            "username": "testuser",
                            "repos": "org/repo1",
                        }
                    )

                    assert len(result) == 1
                    assert isinstance(result[0], TextContent)
                    assert "GitHub Activity" in result[0].text

                    mock_format.assert_called_once_with(mock_activity)

    @pytest.mark.asyncio
    async def test_get_github_activity_missing_date(self):
        """Test GitHub activity with missing required date."""
        # This should raise a KeyError which gets caught by handle_call_tool
        with pytest.raises(KeyError):
            await _get_github_activity({})

    @pytest.mark.asyncio
    async def test_get_github_activity_optional_params(self):
        """Test GitHub activity with optional parameters."""
        mock_activity = GitHubActivity(
            target_date=datetime(2024, 7, 23, 0, 0, 0, 0),
            username="",
            repos=None,
            events=[],
            summary={"total_events": 0, "repositories": []},
        )

        with patch.object(date_parser, "parse_date") as mock_parse:
            with patch.object(
                github_service, "get_activity", new_callable=AsyncMock
            ) as mock_get_activity:
                with patch.object(formatter, "format_github_activity") as mock_format:
                    mock_parse.return_value = datetime(2024, 7, 23, 0, 0, 0, 0)
                    mock_get_activity.return_value = mock_activity
                    mock_format.return_value = "Activity"

                    await _get_github_activity({"date": "yesterday"})

                    # Should handle missing optional params
                    mock_get_activity.assert_called_once_with(
                        target_date=datetime(2024, 7, 23, 0, 0, 0, 0),
                        username="",
                        repos=None,
                    )


class TestWorkdayDateTool:
    """Test the get_workday_date tool."""

    @pytest.mark.asyncio
    async def test_get_workday_date_basic(self):
        """Test basic date parsing."""
        with patch.object(date_parser, "parse_date") as mock_parse:
            mock_parse.return_value = datetime(2024, 7, 22, 0, 0, 0, 0)

            result = await _get_workday_date({"date_expression": "yesterday"})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Parsed date: 2024-07-22T00:00:00" in result[0].text

            mock_parse.assert_called_once_with("yesterday")

    @pytest.mark.asyncio
    async def test_get_workday_date_various_expressions(self):
        """Test various date expressions."""
        test_cases = [
            ("yesterday", datetime(2024, 7, 22, 0, 0, 0, 0)),
            ("last friday", datetime(2024, 7, 19, 0, 0, 0, 0)),
            ("2024-07-15", datetime(2024, 7, 15, 0, 0, 0, 0)),
        ]

        for expression, expected_date in test_cases:
            with patch.object(date_parser, "parse_date") as mock_parse:
                mock_parse.return_value = expected_date

                result = await _get_workday_date({"date_expression": expression})

                expected_iso = expected_date.isoformat()
                assert expected_iso in result[0].text

    @pytest.mark.asyncio
    async def test_get_workday_date_missing_expression(self):
        """Test workday date with missing expression."""
        with pytest.raises(KeyError):
            await _get_workday_date({})


class TestFormatStandupReportTool:
    """Test the format_standup_report tool."""

    @pytest.mark.asyncio
    async def test_format_standup_report_basic(self):
        """Test basic report formatting."""
        github_activity_data = {
            "target_date": "2024-07-23T00:00:00",
            "events": [],
            "summary": {"total_events": 0},
        }

        with patch.object(formatter, "format_standup_report") as mock_format:
            mock_format.return_value = "# Formatted Report\n\nContent"

            result = await _format_standup_report(
                {"github_activity": github_activity_data, "format": "markdown"}
            )

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Formatted Report" in result[0].text

            mock_format.assert_called_once_with(
                github_activity=github_activity_data, format_type="markdown"
            )

    @pytest.mark.asyncio
    async def test_format_standup_report_default_format(self):
        """Test report formatting with default format."""
        github_activity_data = {"events": [], "summary": {}}

        with patch.object(formatter, "format_standup_report") as mock_format:
            mock_format.return_value = "Report"

            await _format_standup_report({"github_activity": github_activity_data})

            # Should use default markdown format
            mock_format.assert_called_once_with(
                github_activity=github_activity_data, format_type="markdown"
            )

    @pytest.mark.asyncio
    async def test_format_standup_report_all_formats(self):
        """Test report formatting with different formats."""
        github_activity_data = {"events": [], "summary": {}}
        formats = ["markdown", "text", "json"]

        for format_type in formats:
            with patch.object(formatter, "format_standup_report") as mock_format:
                mock_format.return_value = f"Report in {format_type}"

                result = await _format_standup_report(
                    {"github_activity": github_activity_data, "format": format_type}
                )

                assert format_type in result[0].text
                mock_format.assert_called_once_with(
                    github_activity=github_activity_data, format_type=format_type
                )

    @pytest.mark.asyncio
    async def test_format_standup_report_missing_github_activity(self):
        """Test report formatting with missing required data."""
        with pytest.raises(KeyError):
            await _format_standup_report({})


class TestIntegration:
    """Integration tests for the MCP server."""

    @pytest.mark.asyncio
    async def test_full_workflow_via_handle_call_tool(self):
        """Test full workflow through handle_call_tool."""
        mock_activity = GitHubActivity(
            target_date=datetime(2024, 7, 23, 0, 0, 0, 0),
            username="testuser",
            repos=None,
            events=[],
            summary={"total_events": 0, "repositories": []},
        )

        with patch.object(date_parser, "parse_date") as mock_parse:
            with patch.object(
                github_service, "get_activity", new_callable=AsyncMock
            ) as mock_get_activity:
                with patch.object(formatter, "format_standup_report") as mock_format:
                    mock_parse.return_value = datetime(2024, 7, 23, 0, 0, 0, 0)
                    mock_get_activity.return_value = mock_activity
                    mock_format.return_value = "# Integration Test\n\nSuccess"

                    result = await handle_call_tool(
                        "get_standup_summary",
                        {"date": "yesterday", "username": "testuser"},
                    )

                    assert len(result) == 1
                    assert isinstance(result[0], TextContent)
                    assert "Integration Test" in result[0].text

    @pytest.mark.asyncio
    async def test_error_handling_in_integration(self):
        """Test error handling in full integration."""
        with patch.object(
            github_service, "get_activity", side_effect=Exception("API Error")
        ):
            result = await handle_call_tool(
                "get_standup_summary", {"date": "yesterday"}
            )

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Error: API Error" in result[0].text
