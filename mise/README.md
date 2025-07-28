# Mise MCP Server

A server for AI agents to enable tooling to manage dependencies and development dependencies using [mise](https://github.com/jdx/mise).

> [!CAUTION]
> This server allows agents to install additional dependencies and may represent a security risk. Exercise caution when using this MCP server to ensure this does not install and use executables inappropriately.

## Usage

To use this tool, it's important to understand how mise modifies the shell. Programs managed by mise are available to a project by activating [PATH](https://mise.jdx.dev/dev-tools/shims.html#path-activation) or with [shims](https://mise.jdx.dev/dev-tools/shims.html) (see mise's [shims vs PATH](https://mise.jdx.dev/dev-tools/shims.html#shims-vs-path)). The agent's shell operates differently depending on the way you activate mise. Below are examples of Claude Code with each method.

<details>
<summary>PATH activation</summary>

```
$ eval "$(mise activate zsh)"

$ elixir -v
zsh: command not found: elixir

$ claude

! elixir -v
  ⎿  zsh: command not found: elixir

> install erlang and elixir, then get the version

⏺ I'll install Erlang and Elixir using mise, then get the version.

⏺ mise - mise_install (MCP)(tool: "erlang@latest")
  ⎿

     Warnings/Info:
     … +5 lines (ctrl+r to expand)

⏺ mise - mise_install (MCP)(tool: "elixir@latest")
  ⎿  Error: mise elixir@1.18.4-otp-28                install
     mise elixir@1.18.4-otp-28                download v1.18.4-otp-28.zip
     mise elixir@1.18.4-otp-28                extract v1.18.4-otp-28.zip
     … +22 lines (ctrl+r to expand)

⏺ The Elixir installation failed because it can't find the erl command. Let me use the Erlang installation and
  then get the Elixir version:

⏺ mise - mise_use (MCP)(tool: "erlang@28.0.2")
  ⎿  mise ~/dev/me/mcp/mise.toml tools: erlang@28.0.2

⏺ mise - mise_install (MCP)(tool: "elixir@latest")
  ⎿

     Warnings/Info:
     … +8 lines (ctrl+r to expand)

⏺ mise - mise_use (MCP)(tool: "elixir@1.18.4-otp-28")
  ⎿  mise ~/dev/me/mcp/mise.toml tools: elixir@1.18.4-otp-28

⏺ Bash(elixir -v)
  ⎿  Error: zsh: command not found: elixir

⏺ mise - mise_exec (MCP)(command: "elixir -v")
  ⎿  Erlang/OTP 28 [erts-16.0.2] [source] [64-bit] [smp:10:10] [ds:10:10:10] [async-threads:1] [jit]

     Elixir 1.18.4 (compiled with Erlang/OTP 28)

⏺ Elixir 1.18.4 (compiled with Erlang/OTP 28)
```
</details>

<details>
<summary>Shims</summary>

```
$ eval "$(mise activate --shims)"

$ elixir -v
mise ERROR No version is set for shim: elixir
Set a global default version with one of the following:
mise use -g elixir@1.16.2-otp-26
mise use -g elixir@1.18.3-otp-27
mise ERROR Run with --verbose or MISE_VERBOSE=1 for more information

$ claude

! elixir -v
  ⎿  mise ERROR No version is set for shim: elixir
     Set a global default version with one of the following:
     mise use -g elixir@1.16.2-otp-26
     … +2 lines (ctrl+r to expand)

! elixir -v
  ⎿  zsh: command not found: elixir

> install erlang and elixir, then get the version

⏺ I'll install Erlang and Elixir using mise, then get the version.

⏺ mise - mise_install (MCP)(tool: "erlang@latest")
  ⎿

     Warnings/Info:
     … +5 lines (ctrl+r to expand)

⏺ mise - mise_install (MCP)(tool: "elixir@latest")
  ⎿  Error: mise elixir@1.18.4-otp-28                install
     mise elixir@1.18.4-otp-28                download v1.18.4-otp-28.zip
     mise elixir@1.18.4-otp-28                extract v1.18.4-otp-28.zip
     … +22 lines (ctrl+r to expand)

⏺ mise - mise_use (MCP)(tool: "erlang@28.0.2")
  ⎿  mise ~/dev/me/mcp/mise.toml tools: erlang@28.0.2

⏺ mise - mise_install (MCP)(tool: "elixir@latest")
  ⎿

     Warnings/Info:
     … +8 lines (ctrl+r to expand)

⏺ Bash(elixir -v)
  ⎿  Error: zsh: command not found: elixir

⏺ mise - mise_use (MCP)(tool: "elixir@1.18.4-otp-28")
  ⎿  mise ~/dev/me/mcp/mise.toml tools: elixir@1.18.4-otp-28

⏺ mise - mise_exec (MCP)(command: "elixir -v")
  ⎿  Erlang/OTP 28 [erts-16.0.2] [source] [64-bit] [smp:10:10] [ds:10:10:10] [async-threads:1] [jit]

     Elixir 1.18.4 (compiled with Erlang/OTP 28)

⏺ Installed Erlang 28.0.2 and Elixir 1.18.4. The version is:

  Erlang/OTP 28 [erts-16.0.2] [source] [64-bit] [smp:10:10] [ds:10:10:10] [async-threads:1] [jit]

  Elixir 1.18.4 (compiled with Erlang/OTP 28)
```
</details>

> [!NOTE]
> In both examples, Claude was asked to install erlang and elixir (erlang is a dependency for elixir). Lines with `$` demonstrate standard shell commands. Lines prefixed with `!` represent Claude Code's "Bash mode" which essentially runs the command in Claude's subshell. Lines with `>` are prompts.

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
<summary>Using uvx from local</summary>

```json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["--from . mcp-server-mise"]
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

### Examples

<details>
<summary>Is there an elixir upgrade available?</summary>

```json
> Is there an elixir upgrade available?
  ⎿  node                           lts     22.17.0  22.17.1 ~/dev/me/mcp/mise.toml
     npm:@anthropic-ai/claude-code  latest  1.0.43   1.0.61  ~/dev/me/mcp/mise.toml
PreToolUse:mcp__mise__mise_outdated

⏺ No, Elixir 1.18.4 is the latest version available through mise.
```
</details>
