# MCP Standup Server

A Model Context Protocol (MCP) server for generating standup reports from GitHub activity.

## Features

- **GitHub Integration**: Fetch and analyze GitHub activity (commits, PRs, reviews, comments)
- **Smart Date Parsing**: Support for natural language dates ("yesterday", "last friday", etc.)
- **Standup-Friendly Formatting**: Generate concise, linkable summaries perfect for team standups
- **Commit Deduplication**: Handles force pushes and duplicate commits intelligently
- **Multiple Output Formats**: Markdown, plain text, or JSON output

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   cd mcp-standup-server
   pip install -e .
   ```

## Configuration

Set the following environment variables:

```bash
# Required for GitHub integration
export GITHUB_TOKEN="your_github_token"
export GITHUB_ORG="your_organization"

```

## Usage

Add this server to your MCP configuration (`.mcp.json`):

```json
{
  "mcpServers": {
    "standup-server": {
      "command": "python",
      "args": ["-m", "standup_server.server"],
      "env": {
        "GITHUB_TOKEN": "your_token",
        "GITHUB_ORG": "your_org"
      }
    }
  }
}
```

## Available Tools

### `get_standup_summary`

Generate a comprehensive standup summary from GitHub activity.

**Parameters:**
- `date` (optional): Target date ("yesterday", "friday", "2024-07-22", etc.)
- `username` (optional): GitHub username to filter by
- `repos` (optional): Comma-separated list of repositories

### `get_github_activity`

Get detailed GitHub activity for a specific date and user.

**Parameters:**
- `date` (required): Target date
- `username` (optional): GitHub username to filter by
- `repos` (optional): Comma-separated list of repositories

### `get_workday_date`

Parse human-readable date expressions into ISO dates.

**Parameters:**
- `date_expression` (required): Date like "yesterday", "last friday", etc.

### `format_standup_report`

Format activity data into standup-friendly reports.

**Parameters:**
- `github_activity` (required): GitHub activity data
- `format` (optional): Output format ("markdown", "text", "json")

## Migration from Shell Script

This MCP server replaces the functionality of `scripts/github-activity.sh` with several improvements:

- **Better Error Handling**: Robust HTTP error handling and retry logic
- **Async Performance**: Concurrent API calls for faster data fetching
- **Structured Data**: Clean data models and processing pipeline
- **Extensibility**: Easy to add new data sources via additional MCP servers
- **Testing**: Unit testable components
- **Rich Formatting**: Multiple output formats with proper markdown links

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Format code:

```bash
ruff format src tests
ruff check src tests
```

## Architecture

- **`server.py`**: Main MCP server with tool definitions
- **`github.py`**: GitHub API integration and event processing
- **`formatting.py`**: Report formatting and standup generation
- **`utils.py`**: Date parsing and utility functions

## Future Enhancements

- [ ] Add Jira integration
- [ ] Support for custom report templates
- [ ] Caching for improved performance
- [ ] Webhook support for real-time updates
- [ ] Export to various formats (PDF, CSV, etc.)

## License

MIT License - see LICENSE file for details.
