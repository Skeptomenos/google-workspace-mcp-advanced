# Migration Guide: `gws-mcp-advanced` -> `google-workspace-mcp-advanced`

Audience: existing users migrating from the legacy naming/path.

## What Changed

1. Python package / `uvx` command:
   - old: `gws-mcp-advanced`
   - new: `google-workspace-mcp-advanced`
2. Default config directory:
   - old: `~/.config/gws-mcp-advanced`
   - new: `~/.config/google-workspace-mcp-advanced`
3. Recommended MCP server key in client config:
   - `google-workspace`

## Backward Compatibility

Current releases include compatibility behavior:

1. If `WORKSPACE_MCP_CONFIG_DIR` is not set, startup will try to migrate/copy data from:
   - `~/.config/gws-mcp-advanced` -> `~/.config/google-workspace-mcp-advanced`
2. Credential loading supports legacy fallback if files still exist in the old directory.

This allows staged migration without immediate manual file moves.

## Migration Steps

1. Update MCP command in client config:
    - old: `uvx gws-mcp-advanced --transport stdio`
    - new: `uvx google-workspace-mcp-advanced==1.0.10 --transport stdio`
2. Keep your MCP server key as `google-workspace` (recommended).
3. Restart your MCP client so it spawns a new subprocess with updated config.
4. Run a read-only tool (`list_calendars`, `list_drive_items`) to confirm auth loads.
5. Optional cleanup after validation:
   - archive or remove `~/.config/gws-mcp-advanced` when you no longer need rollback.

## If You Use a Custom Config Directory

If you already set `WORKSPACE_MCP_CONFIG_DIR`, no automatic migration is performed.
Your explicit path remains authoritative.

## Troubleshooting

1. Auth prompts unexpectedly:
   - verify `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` are set in the MCP environment.
   - verify the client was restarted after config changes.
2. Wrong credential directory:
   - run with explicit `WORKSPACE_MCP_CONFIG_DIR` to remove ambiguity.

## Related Docs

- [Authentication Model](AUTHENTICATION_MODEL.md)
- [MCP Client Setup Guide](MCP_CLIENT_SETUP_GUIDE.md)
