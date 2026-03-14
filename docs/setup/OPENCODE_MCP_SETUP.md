# OpenCode MCP Setup

This guide configures `google-workspace-mcp-advanced` for OpenCode.

## Config File Location

Use one of these OpenCode config files:

- Project config: `opencode.json` or `opencode.jsonc`
- Global config: `~/.config/opencode/opencode.json`

## Stable (Published) Configuration

```json
{
  "mcp": {
    "google-workspace": {
      "type": "local",
      "enabled": true,
      "command": [
        "uvx",
        "google-workspace-mcp-advanced==1.0.9",
        "--transport",
        "stdio"
      ],
      "timeout": 60000,
      "environment": {
        "USER_GOOGLE_EMAIL": "your.email@company.com",
        "WORKSPACE_MCP_CONFIG_DIR": "/Users/<you>/.config/google-workspace-mcp-advanced"
      }
    }
  }
}
```

## Dev (Local Repository) Configuration

Use this while developing unreleased code.

```json
{
  "mcp": {
    "google-workspace": {
      "type": "local",
      "enabled": true,
      "command": [
        "uv",
        "run",
        "--project",
        "/absolute/path/to/google-workspace-mcp-advanced",
        "python",
        "/absolute/path/to/google-workspace-mcp-advanced/main.py"
      ],
      "timeout": 60000,
      "environment": {
        "USER_GOOGLE_EMAIL": "your.email@company.com",
        "WORKSPACE_MCP_CONFIG_DIR": "/Users/<you>/.config/google-workspace-mcp-advanced"
      }
    }
  }
}
```

## Verify

1. Restart OpenCode after config changes.
2. Ask OpenCode to list tools from `google-workspace`.
3. Execute one read-only tool call.

## Troubleshooting

- If server is missing, confirm config file path and JSON validity.
- If OpenCode shows `Invalid input mcp.google-workspace`, remove unsupported fields such as `cwd`, `args`, or legacy `mcpServers` entries.
- If process launch fails, test the command directly in terminal:

```bash
uvx google-workspace-mcp-advanced==1.0.9 --transport stdio
```

For local dev mode:

```bash
uv run --project /absolute/path/to/google-workspace-mcp-advanced \
  python /absolute/path/to/google-workspace-mcp-advanced/main.py --transport stdio
```

## Official References

- [OpenCode MCP servers](https://opencode.ai/docs/mcp-servers)
- [OpenCode configuration](https://opencode.ai/docs/config)
