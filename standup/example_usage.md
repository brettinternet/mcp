# MCP Standup Server - Usage Examples

This document shows how to use the MCP Standup Server tools once it's configured in Claude.

## Configuration

First, make sure your `.mcp.json` includes the standup server:

```json
{
  "mcpServers": {
    "standup-server": {
      "command": "python",
      "args": ["-m", "standup_server.server"],
      "cwd": "./mcp-standup-server",
      "env": {
        "GITHUB_TOKEN": "your_github_token",
        "GITHUB_ORG": "your_organization"
      }
    }
  }
}
```

## Tool Examples

### 1. Get Standup Summary (Most Common)

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

---

## GitHub Activity Details

**3 events** across **2 repositories**

- [myorg/repo1](https://github.com/myorg/repo1)
- [myorg/repo2](https://github.com/myorg/repo2)
```

### 2. Get Detailed GitHub Activity

```bash
# Get detailed activity report
get_github_activity(date="yesterday", username="john-doe")

# Get activity for specific date
get_github_activity(date="2024-07-23", repos="myorg/repo1")
```

### 3. Parse Date Expressions

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

### 4. Format Custom Reports

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

## Integration with Existing Workflow

### Replace Shell Script Usage

Instead of running:
```bash
task github:myactivity DAY=thu REPOS=org/repo1,org/repo2
```

Now use:
```bash
get_standup_summary(date="thursday", repos="org/repo1,org/repo2")
```

### Automated Standup Generation

Create a daily standup note:
```bash
# This would typically be called from Claude
standup_summary = get_standup_summary(date="yesterday")
# Save to file or share with team
```

## Advanced Usage

### Filtering by User

```bash
# Get activity for specific team member
get_standup_summary(date="yesterday", username="team-lead")

# Compare activity across multiple users (call multiple times)
get_standup_summary(date="yesterday", username="developer1")
get_standup_summary(date="yesterday", username="developer2")
```

### Date Range Flexibility

```bash
# Various date formats supported
get_standup_summary(date="monday")
get_standup_summary(date="last tuesday")
get_standup_summary(date="2024-07-15")
get_standup_summary(date="July 15, 2024")
```

### Repository Filtering

```bash
# All org repositories (default)
get_standup_summary(date="yesterday")

# Specific repositories only
get_standup_summary(date="yesterday", repos="org/frontend,org/backend,org/api")

# Single repository
get_standup_summary(date="yesterday", repos="org/critical-service")
```

## Output Formats

### Markdown (Default)
- Rich formatting with links
- Perfect for copying to team channels
- Includes repository links and commit references

### Plain Text
- Clean, no-formatting output
- Good for plain text environments
- Links converted to readable text

### JSON
- Structured data format
- Perfect for programmatic processing
- Includes full event details and metadata

## Tips for Best Results

1. **Set Environment Variables**: Ensure `GITHUB_TOKEN` and `GITHUB_ORG` are properly configured
2. **Use Recent Dates**: GitHub API returns limited history, so stick to recent dates
3. **Filter by User**: Use `username` parameter to focus on specific team members
4. **Repository Filtering**: Use `repos` parameter to focus on relevant projects
5. **Save Output**: Copy the markdown output directly to your standup notes

## Troubleshooting

- **No activity found**: Check date format and ensure activity exists for that day
- **API errors**: Verify GitHub token has appropriate permissions
- **Empty results**: Ensure username matches GitHub login exactly (case-sensitive)
- **Timeout issues**: Try filtering to specific repositories to reduce API calls