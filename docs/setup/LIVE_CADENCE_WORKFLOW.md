# Cadence Workflow User Guide

This guide explains how the live cadence workflow runs, what each lane does, and how to operate it safely as an end user/operator.

Workflow file:
`.github/workflows/live-mcp-cadence.yml`

## Purpose

The cadence workflow gives you scheduled confidence that this MCP is still healthy in real Google Workspace environments, not just in unit tests.

It is designed to:

1. run read-only validation on a schedule,
2. optionally run write-lane probes when explicitly enabled,
3. keep test artifacts bounded via prefix + retention cleanup controls.

## How It Works

Each run executes in this order:

1. Preflight gate
   1. verifies required secrets exist,
   2. exits cleanly if the environment is not configured.
2. Credential bootstrap
   1. writes credentials into a temporary `WORKSPACE_MCP_CONFIG_DIR` for CI.
3. Validation lanes
   1. `mcp_protocol` lane for protocol contract checks,
   2. `live_mcp` lane for read-focused live API checks,
   3. optional `live_write` lane for mutation probes.
4. Cleanup phase
   1. always runs cleanup preview,
   2. runs destructive cleanup only when explicitly enabled.

## Trigger Modes

1. Scheduled run: nightly at `03:15 UTC`.
2. Manual run: `workflow_dispatch` with inputs:
   1. `run_write_lane`,
   2. `execute_cleanup`,
   3. `cleanup_older_than_hours`.

## Required Secrets

1. `MCP_TEST_USER_EMAIL`
   1. Google account used by live lanes.
2. `MCP_CREDENTIALS_JSON`
   1. OAuth credential JSON for that account.

Optional:

1. `MCP_AUTH_CLIENTS_JSON`
   1. only needed when testing multi-client auth routing.

## Optional Variables

1. `MCP_TEST_PREFIX`
   1. artifact prefix guard (fallback: `codex-it-`).
2. `MCP_LIVE_WRITE_CADENCE`
   1. set `1` to make write lane default-on for cadence runs.
3. `MCP_LIVE_CLEANUP_EXECUTE`
   1. set `1` to make cleanup execute mode default-on.

## Cleanup Behavior

Cleanup is handled by:
`scripts/mcp_live_cleanup.py`

Rules:

1. dry-run by default,
2. deletion only when `--execute` is set,
3. item must match both:
   1. name/title starts with test prefix,
   2. age exceeds `older_than_hours`,
4. supported services:
   1. Drive files,
   2. Calendar events,
   3. Tasks task lists.

## Manual Cleanup Commands

Preview only:

```bash
uv run python scripts/mcp_live_cleanup.py \
  --user-email "$MCP_TEST_USER_EMAIL" \
  --artifact-prefix "${MCP_TEST_PREFIX:-codex-it-}" \
  --older-than-hours 24 \
  --services all
```

Execute deletion:

```bash
uv run python scripts/mcp_live_cleanup.py \
  --user-email "$MCP_TEST_USER_EMAIL" \
  --artifact-prefix "${MCP_TEST_PREFIX:-codex-it-}" \
  --older-than-hours 24 \
  --services all \
  --execute
```

## Operating Policy

1. Keep write lane disabled unless you are actively validating mutators.
2. Keep destructive cleanup disabled by default.
3. Scope all test artifacts with a dedicated prefix.
4. Use manual dispatch for high-risk runs.
