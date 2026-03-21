# Google Workspace MCP Advanced

High-performance MCP server for Google Workspace integration. 50+ async tools for Gmail, Drive, Calendar, Docs, Sheets, Chat, Forms, Slides, Tasks, and Search.

## Identity
- **Status:** production
- **Tech:** Python, FastMCP, Google APIs, Pydantic

## Hard Constraints
1. **NO SPEC = NO CODE:** Demand `SPEC.md` or a clear plan before implementation.
2. **ZERO TOLERANCE:** No lint errors (`ruff`). No type errors. No failing tests (`pytest`).
3. **DRY RUN DEFAULT:** All tools modifying Google Workspace MUST default to `dry_run=True`.
4. **ASYNC ONLY:** All MCP tools must be `async`. Wrap blocking SDK calls in `asyncio.to_thread()`.
5. **SAFETY:** Use `@require_google_service` and `@handle_http_errors` decorators on all tools.
6. **ATOMICITY:** One tool or feature per implementation. No scope creep.

## Architecture (3-Layer)
1. **Presentation (Tool Layer):** `*/tools.py`. FastMCP decorators, input validation, output formatting.
2. **Service (Logic Layer):** `core/managers.py` or domain logic. Business rules, sync algorithms.
3. **Data (SDK Layer):** `auth/service_decorator.py` and raw Google API calls.

Use Pydantic models for all complex data structures (DTOs).

## Verification Protocol (Definition of Done)
1. `uv run ruff check .` — must return no errors
2. `uv run ruff format .` — must not modify files
3. `uv run pytest` — must pass all tests

## Quick Reference

| Task | Command |
|------|---------|
| Install | `uv pip install -e ".[dev]"` |
| Run server | `python main.py` |
| Lint + format | `uv run ruff check . && uv run ruff format .` |

## Environment & Security
- `USER_GOOGLE_EMAIL`: Target Google account email (Required).
- `WORKSPACE_MCP_CONFIG_DIR`: Credentials directory (default: `~/.config/google-workspace-mcp-advanced`).
- Never hardcode secrets. Never log OAuth tokens. Never log PII.

Read `agent-docs/` for architecture patterns and Python conventions.
Read `MIGRATION_NOTES.md` for pending npm publishing TODO.
