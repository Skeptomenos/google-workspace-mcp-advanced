# Distribution and Release Guide

## Metadata

- Last Updated (UTC): 2026-03-17T00:00:00Z
- Primary Runtime: `uvx`
- Python Package: `google-workspace-mcp-advanced`

## Release Validation Path

- Workflow: `.github/workflows/release-pypi.yml`
- Trigger: pushed tag `vX.Y.Z`
- Required jobs: `verify`, `build`, `publish`

## Distribution Model

This project ships through PyPI and runs through `uvx`.

```bash
# Stable (latest published)
uvx google-workspace-mcp-advanced --transport stdio

# Pinned (recommended for teams)
uvx google-workspace-mcp-advanced==1.0.10 --transport stdio
```

## Prerequisite

Install `uv` before using `uvx`.

```bash
# macOS (Homebrew)
brew install uv

# Windows (winget)
winget install --id=astral-sh.uv -e

# Windows (PowerShell installer)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Linux/macOS (official installer)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify
uv --version
```

## Release Sequence

1. Publish package to PyPI.
2. Validate both channels:
   1. stable (`uvx google-workspace-mcp-advanced ...`)
   2. pinned (`uvx google-workspace-mcp-advanced==x.y.z ...`)

## Workflow

- Release workflow: `.github/workflows/release-pypi.yml`
- Trusted publishing target: PyPI (OIDC)
- npm wrapper publishing is not part of the active release path.

## Rollback

If a release is bad, pin clients to a known-good version:

```bash
uvx google-workspace-mcp-advanced==<good_version> --transport stdio
```

## Pre-Release Checks

1. `uv run python scripts/check_distribution_scope.py`
2. `uv run pytest -q tests/unit/core/test_distribution_checks.py`
3. `uvx google-workspace-mcp-advanced==1.0.10 --help`

## Team Rollout Guidance

- Use pinned versions in production-facing MCP configs.
- Roll forward by updating the pinned version.
- Roll back by reverting to the prior known-good pinned version.
