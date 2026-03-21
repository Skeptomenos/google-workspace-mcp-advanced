# Distribution Publishing Playbook

Use this when asked to commit, tag, push, or publish a release.

## Goal

Ship one clean PyPI/uvx release without re-discovering the workflow.

## Preflight

1. Finish code/docs/test work first.
2. Check repo state:
   - `git status --short`
   - `git log -5 --oneline`
3. Check version/tag availability before bumping:
   - local tags: `git tag --list | sort -V`
   - remote tag: `git ls-remote --tags origin "vX.Y.Z"`
4. If the remote tag already exists, do not reuse it. Bump to a new version.

## Commit Split

Use two commits when doing a release:

1. `fix(...)` or `docs(...)`
   - code changes
   - behavior docs
   - tests
   - specs/checkpoints
2. `release: vX.Y.Z <short label>`
    - version bumps
    - pinned install examples
    - release notes entry mentioning the release version

## Distribution Scope

- Canonical distribution is PyPI via `uvx`.
- Do not treat npm as an active release target.
- There is no npm release workflow in the active path.

## Release Files

Always update:

- `pyproject.toml`
- `uv.lock`
- `docs/RELEASE_NOTES.md`

Usually update pinned install docs too:

- `README.md`
- `docs/DISTRIBUTION_RELEASE.md`
- `docs/setup/CLAUDE_CODE_MCP_SETUP.md`
- `docs/setup/CURSOR_MCP_SETUP.md`
- `docs/setup/GEMINI_CLI_MCP_SETUP.md`
- `docs/setup/OPENCODE_MCP_SETUP.md`
- `docs/setup/MIGRATING_FROM_GWS_MCP_ADVANCED.md`

## Required Checks

Run these before pushing/tagging:

1. `uv run ruff check .`
2. `uv run ruff format --check .`
3. `uv run pyright --project pyrightconfig.json`
4. `uv run pytest`
5. `uv run python scripts/check_distribution_scope.py`
6. `uv run pytest -q tests/unit/core/test_distribution_checks.py`
7. `uv build`

## Push and Publish Order

1. Push branch.
2. Create/push tag `vX.Y.Z`.
3. PyPI publishes from tag push via `.github/workflows/release-pypi.yml`.
4. Wait for PyPI success.
5. Watch workflow state with `gh run list` / `gh run watch`.

## Workflow Facts

- PyPI workflow requires tag version to match `pyproject.toml`.

## Non-Negotiables

- Never retag or republish an existing remote version unless the user explicitly asks for destructive recovery.
- Publish PyPI only.
- Do not include unrelated worktree changes in release commits.
- Keep historical plan/investigation docs out of the release unless intentionally shipping them.
