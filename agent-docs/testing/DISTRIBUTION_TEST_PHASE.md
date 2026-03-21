# Distribution Test Phase Guide (Living)

Use this file to execute and track the next distribution validation phase.

## Document Controls
- Status: `COMPLETE_UVX_ONLY`
- Last Updated (UTC): `2026-03-02T13:53:12Z`
- Tester: Codex
- Branch: `main`
- Commit: `e714355` (PyPI publish run head SHA)
- Related Plan: `/Users/david.helmus/repos/ai-dev/_infra/gws-mcp-advanced/gws-mcp-advanced/agent-docs/roadmap/PLAN.md`
- Related Release Guide: `/Users/david.helmus/repos/ai-dev/_infra/gws-mcp-advanced/gws-mcp-advanced/docs/DISTRIBUTION_RELEASE.md`

## Preconditions
1. Trusted publisher is configured in PyPI for `google-workspace-mcp-advanced` (GitHub OIDC).
2. Release workflow is present:
   - `.github/workflows/release-pypi.yml`
3. Guard scripts pass:
   - `uv run python scripts/check_distribution_scope.py`

## Test Matrix

| ID | Area | Action | Expected Result | Status | Evidence | Notes |
|---|---|---|---|---|---|---|
| DT-01 | Release (PyPI) | Trigger `Release PyPI` workflow for current version | Workflow passes, artifact published to PyPI | PASS | Run `22577853068` (`verify/build/publish` all green) | Baseline release lane is operational. |
| DT-02 | Channel Stable (Primary) | `uvx google-workspace-mcp-advanced --transport stdio` | Server starts and exposes tools normally | PASS | `uvx google-workspace-mcp-advanced==1.0.0 --help` succeeded | uvx lane validated from published package. |
| DT-03 | Channel Pinned (Primary) | `uvx google-workspace-mcp-advanced==1.0.0 --transport stdio` | Deterministic pinned version starts successfully | PASS | `uvx ...==1.0.0 --help` output shows CLI options | Primary deterministic channel validated. |

## Execution Notes
1. Record exact workflow run IDs and package version numbers in Evidence.
2. If any test fails, add a defect row in `PLAN.md` / `TASKS.md` and keep this file append-only.
3. Keep `Status` values to: `PASS`, `FAIL`, `BLOCKED`, `NOT RUN`.

## Session Summary (Codex - 2026-03-02)
- **Tester:** Codex
- **Branch/Target:** `main`
- **Timestamp:** `2026-03-02T13:23:10Z`
- **Result Snapshot:**
  - PASS: 3 (`DT-01`..`DT-03`)
- **Decision Update:** Distribution baseline is uvx-first and PyPI-only for active release work.
- **Scope Update:** npm/npx references were removed from active distribution guidance.

## Next Actions
1. Keep uvx lane as canonical in user docs and setup guides.
2. Re-run `DT-01`..`DT-03` when the release pipeline changes.
