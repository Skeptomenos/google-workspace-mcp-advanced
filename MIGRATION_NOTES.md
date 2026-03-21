# Migration Notes: GWS MCP Advanced

**Old path:** `~/repos/ai-tooling/mcp-servers/gws-mcp-advanced`
**New path:** `~/repos/ai-dev/_infra/gws-mcp-advanced/gws-mcp-advanced/` (public nested clone)
**GitHub:** `Skeptomenos/gws-mcp-advanced` (ACTIVE — public repo)
**Type:** Public nested repo (wrapper + clone)

## Issues

### 1. Virtual environment needs recreating

The old venv at the old path is gone. The MCP server config in `opencode.json` references it. Recreate:

```bash
cd ~/repos/ai-dev/_infra/gws-mcp-advanced/gws-mcp-advanced
uv sync  # or: python3 -m venv .venv && pip install -r requirements.txt
```

### 2. OpenCode MCP config broken

`~/.config/opencode/opencode.json` references old path for both the Python command and PYTHONPATH. See `ai-dev/MIGRATION_NOTES.md` Section 1 for the fix.

### 3. Stash patch pending

`~/repos/tmp/_stash_recovery/gws-mcp-advanced-stash-d926500.patch` contains unique type signature improvements (accepting `list` in addition to `str` for calendar reminders, attendees, sheet values). Apply when ready:

```bash
cd ~/repos/ai-dev/_infra/gws-mcp-advanced/gws-mcp-advanced
git apply ~/repos/tmp/_stash_recovery/gws-mcp-advanced-stash-d926500.patch
```

**Review before applying** — the patch is from an older commit and may conflict with current HEAD.

## Push Workflow

This is a public nested repo:
```bash
cd ~/repos/ai-dev/_infra/gws-mcp-advanced/gws-mcp-advanced
git add . && git commit -m "..." && git push
# Pushes to Skeptomenos/gws-mcp-advanced (public)
```
