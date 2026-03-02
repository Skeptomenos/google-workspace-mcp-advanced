# MCP Client Setup Guide

Audience: users and team operators.

This guide shows the recommended client setup for `google-workspace-mcp-advanced`.

## 1. Prerequisite: Install `uv`

`uvx` is the recommended runtime path.

```bash
# macOS (Homebrew)
brew install uv

# Linux/macOS (official installer)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify
uv --version
```

## 2. Stable Team Setup (Recommended)

Use a pinned version for reproducible team behavior.

```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "uvx",
      "args": ["google-workspace-mcp-advanced==1.0.0", "--transport", "stdio"],
      "env": {
        "USER_GOOGLE_EMAIL": "your.email@company.com"
      }
    }
  }
}
```

## 3. Local Development Setup

Use this when testing local repository changes.

```json
{
  "mcpServers": {
    "google-workspace-dev": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/path/to/google-workspace-mcp-advanced",
        "google-workspace-mcp-advanced",
        "--transport",
        "stdio"
      ],
      "env": {
        "USER_GOOGLE_EMAIL": "your.email@company.com"
      }
    }
  }
}
```

## 4. First-Run Authentication

1. Start the MCP server from your client.
2. Open the OAuth URL shown in the client/server output.
3. Sign in and grant scopes.
4. Confirm tools are available (for example, ask the client to list tools from `google-workspace`).

## Client Notes

### OpenCode

1. Add one of the server entries above.
2. Restart OpenCode after config or code changes.
3. Run a quick smoke prompt: "List available tools from google-workspace."

### Gemini CLI

Use the same `mcpServers` block in your Gemini CLI MCP configuration.

### Claude Code and Other TUIs

Use the same `mcpServers` JSON shape in the client-specific config file.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `USER_GOOGLE_EMAIL` | Yes | Google account used by this server instance |
| `GOOGLE_OAUTH_CLIENT_ID` | Yes | OAuth client ID |
| `GOOGLE_OAUTH_CLIENT_SECRET` | Yes | OAuth client secret |
| `WORKSPACE_MCP_CONFIG_DIR` | No | Override credential/config directory |

## Best Practices

- Pin stable team configs (`==x.y.z`), not floating latest.
- Keep separate entries for stable and local-dev servers.
- Restart your MCP client after changing MCP config.
