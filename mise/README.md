# Mise MCP Server

A server for AI agents to enable tooling to manage dependencies and development dependencies using [mise](https://github.com/jdx/mise).

> [!CAUTION]
> This server allows agents to install additional dependencies and may represent a security risk. Exercise caution when using this MCP server to ensure this does not install and use executables inappropriately.

## Usage

### Available Tools

#### Mise Commands

- `mise_install` - Install a tool/runtime
- `mise_uninstall` - Uninstall a tool/runtime  
- `mise_use` - Set tool version for current directory or globally
- `mise_list` - List installed tools and versions
- `mise_outdated` - Show outdated tool versions
- `mise_upgrade` - Upgrade tools to latest versions
- `mise_current` - Show current tool versions in use
- `mise_exec` - Execute command with mise-managed tools
- `mise_which` - Show path to mise-managed binary
- `mise_env` - Show/export environment variables

### Configure for your agent

Add to your MCP settings:

<details>
<summary>Using uvx from published</summary>

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-mise"]
    }
  }
}
```
</details>

<details>
<summary>Using uvx from git</summary>

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["--from git+https://github.com/brettinternet/mcp.git#subdirectory=mise mcp-server-mise"]
    }
  }
}
```
</details>

<details>
<summary>Using docker</summary>

```json
{
  "mcpServers": {
    "fetch": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "ghcr.io/brettinternet/mcp-mise"]
    }
  }
}
```
</details>

<details>
<summary>Using pip installation</summary>

```json
{
  "mcpServers": {
    "fetch": {
      "command": "python",
      "args": ["-m", "mcp_server_mise"]
    }
  }
}
```
</details>
