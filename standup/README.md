# MCP Standup Server

A Model Context Protocol (MCP) server for generating standup reports from GitHub activity. It uses the GitHub CLI so we don't have to use a PAT for the API.

## Features

- **GitHub Integration**: Fetch and analyze GitHub activity (commits, PRs, reviews, comments)
- **Smart Date Parsing**: Support for natural language dates ("yesterday", "last friday", etc.)
- **Standup-Friendly Formatting**: Generate concise, linkable summaries perfect for team standups
- **Commit Deduplication**: Handles force pushes and duplicate commits intelligently
- **Multiple Output Formats**: Markdown, plain text, or JSON output

## Usage

Ensure you have the [GitHub CLI](https://cli.github.com/) installed and authenticated:

```bash
# Authenticate with GitHub
gh auth login
```

Set the following environment variables:

```bash
# Required for GitHub integration
export GITHUB_ORG="your_organization"
# OR
export GITHUB_REPOS="org/repo1,org/repo2"
# OR set them in your MCP configuration
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

### Configure

Add to your MCP settings:

<details>
<summary>Using uvx from published</summary>

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-standup"],
      "env": {
        "GITHUB_REPOS": "brettinternet/mcp"
      }
    }
  }
}
```
</details>

<details>
<summary>Using uvx from local</summary>

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["--from . mcp-server-standup"],
      "env": {
        "GITHUB_REPOS": "brettinternet/mcp"
      }
    }
  }
}
```
</details>

<details>
<summary>Using uvx from GitHub</summary>

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["--from git+https://github.com/brettinternet/mcp.git#subdirectory=standup mcp-server-standup"],
      "env": {
        "GITHUB_REPOS": "brettinternet/mcp"
      }
    }
  }
}
```
</details>

<!-- <details>
<summary>Using docker</summary>

```json
{
  "mcpServers": {
    "fetch": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "ghcr.io/brettinternet/mcp-standup"],
      "env": {
        "GITHUB_REPOS": "brettinternet/mcp"
      }
    }
  }
}
```
</details> -->

<details>
<summary>Using pip installation</summary>

```json
{
  "mcpServers": {
    "fetch": {
      "command": "python",
      "args": ["-m", "mcp_server_standup"],
      "env": {
        "GITHUB_REPOS": "brettinternet/mcp"
      }
    }
  }
}
```
</details>

### Examples

#### 1. Get Standup Summary (Most Common)

```bash
# Get yesterday's activity summary
get_standup_summary(date="yesterday")

# Get Friday's activity for a specific user
get_standup_summary(date="friday", username="john-doe")

# Get activity for specific repositories
get_standup_summary(date="2024-07-23", repos="myorg/repo1,myorg/repo2")
```

**Expected Output:**
```markdown
# Standup Summary - July 23, 2024

- Made **3 commits** to [myorg/repo1](https://github.com/myorg/repo1)
  - Add user authentication ([abc123d](https://github.com/myorg/repo1/commit/abc123def456))
  - Fix login validation ([def456g](https://github.com/myorg/repo1/commit/def456ghi789))
  - Update tests ([ghi789j](https://github.com/myorg/repo1/commit/ghi789jkl012))
- Opened **[PR #142](https://github.com/myorg/repo2/pull/142)**: Implement password reset
- Reviewed **[PR #138](https://github.com/myorg/repo1/pull/138)** (approved)

## GitHub Activity Details

**3 events** across **2 repositories**

- [myorg/repo1](https://github.com/myorg/repo1)
- [myorg/repo2](https://github.com/myorg/repo2)
```

#### 2. Get Detailed GitHub Activity

```bash
# Get detailed activity report
get_github_activity(date="yesterday", username="john-doe")

# Get activity for specific date
get_github_activity(date="2024-07-23", repos="myorg/repo1")
```

#### 3. Parse Date Expressions

```bash
# Test date parsing
get_workday_date(date_expression="last friday")
get_workday_date(date_expression="yesterday")
get_workday_date(date_expression="2024-07-23")
```

**Expected Output:**
```
Parsed date: 2024-07-19T00:00:00
```

#### 4. Format Custom Reports

```bash
# Format activity data in different formats
format_standup_report(
  github_activity=activity_data,
  format="json"
)

format_standup_report(
  github_activity=activity_data,
  format="text"
)
```

### Integration with Existing Workflow

#### Automated Standup Generation

Create a daily standup note:

```bash
# This would typically be called from Claude
standup_summary = get_standup_summary(date="yesterday")
# Save to file or share with team
```

### Advanced Usage

#### Filtering by User

```bash
# Get activity for specific team member
get_standup_summary(date="yesterday", username="team-lead")

# Compare activity across multiple users (call multiple times)
get_standup_summary(date="yesterday", username="developer1")
get_standup_summary(date="yesterday", username="developer2")
```

#### Date Range Flexibility

```bash
# Various date formats supported
get_standup_summary(date="monday")
get_standup_summary(date="last tuesday")
get_standup_summary(date="2024-07-15")
get_standup_summary(date="July 15, 2024")
```

#### Repository Filtering

```bash
# All org repositories (default)
get_standup_summary(date="yesterday")

# Specific repositories only
get_standup_summary(date="yesterday", repos="org/frontend,org/backend,org/api")

# Single repository
get_standup_summary(date="yesterday", repos="org/critical-service")
```

#### Output Formats

- Markdown (Default): Rich formatting with links, perfect for copying to team channels, includes repository links and commit references
- Plain Text: Clean, no-formatting output, good for plain text environments, links converted to readable text
- JSON: Structured data format, perfect for programmatic processing, includes full event details and metadata
